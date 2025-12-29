use serde::{Deserialize, Serialize};
use std::error::Error;


#[derive(Debug, Deserialize)]
#[serde(tag = "function")]
#[serde(rename_all = "lowercase")]
pub enum Call {
    Twice {
        target: usize,        
        #[serde(default)]
        then: Option<Box<Call>>,
    },
    Once {
        target: usize,        
        #[serde(default)]
        then: Option<Box<Call>>,
    },    
    Roll {
        target: usize,
        amount: usize,
        #[serde(default)]
        then: Option<Box<Call>>,
    },
    Combine {
        calls: Vec<Call>,
        direction: Direction,
        #[serde(default)]
        then: Option<Box<Call>>,
    }

}

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum Direction {
    Sequential,
    Sidebyside,
}

impl Default for Direction {
    fn default() -> Self {
        // Choose whichever variant you want to be the default
        Direction::Sequential
    }
}


#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HNote {
    pub midi_number: u8,
    pub velocity: u8,
    pub timing: f64,         // 'l' or 's'
    pub channel: u8,
    #[serde(default)]  
    pub child_direction: Direction,
    #[serde(default)]
    pub children: Option<Box<Vec<HNote>>>, 
    #[serde(default)]
    pub start_time: f64,
    #[serde(default)]    
    pub end_time: f64,
    pub prechildren: Option<Box<Vec<HNote>>>,
    pub anchor_prechild: Option<usize>, //1 index
    pub anchor_end: Option<bool>,
    pub timing_based_on_children: Option<bool>,
    pub overwrite_children: Option<bool>,
    pub ancestor_overwrite_level: Option<usize>,
    #[serde(skip)]
    pub parent: Option<*mut HNote>,
    pub rolled: Option<bool>
    //             ^^^^^^^
    // Boxed child measure to allow recursion
}

fn layout_children_sequentially_in_range(children: &mut [HNote], start: f64, end: f64) {
    let length = end - start;
    let total_shares: f64 = children.iter().map(|c| c.timing).sum();

    if total_shares == 0.0 {
        // All children collapse to zero length
        for child in children {
            child.start_time = start;
            child.end_time   = start;
            child.recalc_times();
        }
        return;
    }

    let num_children = children.len();
    let mut current_start = start;

    for (i, child) in children.iter_mut().enumerate() {
        child.start_time = current_start;
        if i < num_children - 1 {
            let share_ratio = child.timing / total_shares;
            let seg_length  = length * share_ratio;
            child.end_time  = current_start + seg_length;
            current_start  += seg_length;
        } else {
            // Last child soaks up remainder
            child.end_time = end;
        }
        child.recalc_times();
    }
}

fn compute_sum_of_children_shares(note: &HNote) -> f64 {
    if let Some(boxed) = &note.children {
        boxed.iter().map(|c| c.timing).sum()
    } else {
        0.0
    }
}

fn overwrite_midi_recursive(note: &mut HNote, clearingtime: f64) {
    println!("Checking {} at {} vs clearingtime of {}", note.midi_number,note.start_time, clearingtime);
    if note.start_time > clearingtime {
        println!("changing {} at {} to 0", note.midi_number, note.start_time);       
        note.midi_number = 0;
    }
    if let Some(ref mut children) = note.children {
        for child in children.iter_mut() {
            overwrite_midi_recursive(child, clearingtime);
        }
    }
    // if let Some(ref mut prechildren) = note.prechildren {
    //     for prechild in prechildren.iter_mut() {
    //         overwrite_midi_recursive(prechild);
    //     }
    // }
}

impl HNote {

    /// Recursively find the *first* node whose `rolled` is `Some(true)`.
    pub fn find_rolled_mut(&mut self) -> Option<&mut HNote> {
        if self.rolled == Some(true) {
            // This node is "rolled"
            return Some(self);
        }
        // Otherwise, if we have children, search them
        if let Some(children_box) = self.children.as_mut() {
            for child in children_box.iter_mut() {
                if let Some(found) = child.find_rolled_mut() {
                    return Some(found);
                }
            }
        }
        None
    }

    pub fn twice(&self) -> Vec<HNote> {
        vec![self.clone(),self.clone()]
    }

    pub fn once(&self) -> Vec<HNote> {
        vec![self.clone()]
    }


    pub fn format_time(&self) -> String {
        match (self.start_time, self.end_time) {
            (start, end) => format!("[{:.2} - {:.2}]", start, end),
            _ => String::from("[Unknown]"),
        }
    }


    pub fn build_treeold(&self, prefix: &str, is_last: bool) -> String {
        let mut tree = String::new();
        let connector = if is_last { "└── " } else { "├── " };
        tree.push_str(&format!("{}{}{}\n", prefix, connector, self.format_time()));

        let new_prefix = format!("{}{}", prefix, if is_last { "    " } else { "│   " });

        // Process pre_children first with a unique connector ├────
        if let Some(pre_children) = &self.prechildren {
            for (i, child) in pre_children.iter().enumerate() {
                let is_last_prechild = i == pre_children.len() - 1;
                let prechild_connector = if is_last_prechild { "└────pre " } else { "├────pre " };
                tree.push_str(&format!("{}{}{}\n", new_prefix, prechild_connector, child.format_time()));
                let pre_child_prefix = format!("{}│   ", new_prefix);
                tree.push_str(&child.build_treeold(&pre_child_prefix, is_last_prechild));
            }
        }

        // Process normal children next
        if let Some(children) = &self.children {
            for (i, child) in children.iter().enumerate() {
                let is_last_child = i == children.len() - 1;

                let child_prefix = new_prefix.clone();
                tree.push_str(&child.build_treeold(&child_prefix, is_last_child));
            }
        }
        tree
    }
    /// Recursively assign parent pointers to all children and prechildren.
    pub fn assign_parents(&mut self) {
        let self_ptr = self as *mut _; // store a pointer to self
        if let Some(ref mut children) = self.children {
            for child in children.iter_mut() {
                child.parent = Some(self_ptr);
                child.assign_parents();
            }
        }
        if let Some(ref mut prechildren) = self.prechildren {
            for prechild in prechildren.iter_mut() {
                prechild.parent = Some(self_ptr);
                prechild.assign_parents();
            }
        }
    }

    unsafe fn get_ancestor(&mut self, level: usize) -> Option<*mut HNote> {
        let mut current: *mut HNote = self;
        for _ in 0..level {
            if let Some(parent_ptr) = (*current).parent {
                current = parent_ptr;
            } else {
                return None;
            }
        }
        Some(current)
    }

    /// Recursively recalculates the start_time and end_time of all children
    /// so that they are laid out sequentially from `self.start_time` to `self.end_time`.
    pub fn recalc_times(&mut self) {
        let parent_length = self.end_time - self.start_time;

        // --- 1. Lay out the normal children using the existing logic. ---
        if let Some(children_box) = &mut self.children {
            match self.child_direction {
                Direction::Sequential => {
                    layout_children_sequentially_in_range(children_box, self.start_time, self.end_time);
                }
                Direction::Sidebyside => {
                    for child in children_box.iter_mut() {
                        child.start_time = self.start_time;
                        child.end_time = self.end_time;
                        child.recalc_times();
                    }
                }
                _ => {
                    // (Other directions could be handled here.)
                }
            }
        }
        // The mutable borrow of self.children ends here.

        // --- 2. Lay out the prechildren, if provided and if anchor_prechild is valid.
        if let (Some(prechildren_box), Some(anchor_pre)) = (&mut self.prechildren, self.anchor_prechild) {
            // Convert the 1-indexed anchor_prechild to a 0-indexed value.
            let anchor_idx = anchor_pre.saturating_sub(1);
            if anchor_idx < prechildren_box.len() {
                // Determine the base scale for prechildren.
                // If timing_based_on_children is true, use the scale of the children.
                let base = if self.timing_based_on_children.unwrap_or(false) {
                    if let Some(children_box) = &self.children {
                        let total_children_shares: f64 = children_box.iter().map(|child| child.timing).sum();
                        if total_children_shares.abs() < 1e-12 {
                            parent_length
                        } else {
                            parent_length / total_children_shares
                        }
                    } else {
                        parent_length
                    }
                } else {
                    parent_length
                };

                // Compute each prechild's absolute duration as: base * (prechild.timing / divider).
                // (Here we assume each prechild has a field `timing` that determines its written share.)
                let durations: Vec<f64> = prechildren_box
                    .iter()
                    .map(|prechild| base * (prechild.timing))
                    .collect();

                // Decide the anchor point based on anchor_end.
                // If anchor_end is Some(true), anchor at parent's end_time; otherwise, anchor at parent's start_time.
                let anchor_point = if self.anchor_end.unwrap_or(false) {
                    self.end_time
                } else {
                    self.start_time
                };

                if self.anchor_end.unwrap_or(false) {
                    // --- Anchor the prechild to parent's end_time ---
                    // Lay out prechildren BEFORE the anchor so that the one immediately preceding
                    // the anchor ends exactly at parent's end_time.
                    let total_before: f64 = durations.iter().take(anchor_idx).sum();
                    let mut offset = self.end_time - total_before;
                    for i in 0..anchor_idx {
                        let d = durations[i];
                        prechildren_box[i].start_time = offset;
                        prechildren_box[i].end_time = offset + d;
                        prechildren_box[i].recalc_times();
                        offset += d;
                    }
                    // Layout the anchor prechild.
                    {
                        let d = durations[anchor_idx];
                        prechildren_box[anchor_idx].start_time = self.end_time;
                        prechildren_box[anchor_idx].end_time = self.end_time + d;
                        prechildren_box[anchor_idx].recalc_times();
                    }
                    // Lay out prechildren AFTER the anchor.
                    let mut offset = self.end_time + durations[anchor_idx];
                    for i in (anchor_idx + 1)..prechildren_box.len() {
                        let d = durations[i];
                        prechildren_box[i].start_time = offset;
                        prechildren_box[i].end_time = offset + d;
                        prechildren_box[i].recalc_times();
                        offset += d;
                    }
                } else {
                    // --- Anchor the prechild to parent's start_time ---
                    // Lay out prechildren BEFORE the anchor so that the one immediately preceding
                    // the anchor ends exactly at parent's start_time.
                    let total_before: f64 = durations.iter().take(anchor_idx).sum();
                    let mut offset = self.start_time - total_before;
                    for i in 0..anchor_idx {
                        let d = durations[i];
                        prechildren_box[i].start_time = offset;
                        prechildren_box[i].end_time = offset + d;
                        prechildren_box[i].recalc_times();
                        offset += d;
                    }
                    // Layout the anchor prechild.
                    {
                        let d = durations[anchor_idx];
                        prechildren_box[anchor_idx].start_time = self.start_time;
                        prechildren_box[anchor_idx].end_time = self.start_time + d;
                        prechildren_box[anchor_idx].recalc_times();
                    }
                    // Lay out prechildren AFTER the anchor.
                    let mut offset = self.start_time + durations[anchor_idx];
                    for i in (anchor_idx + 1)..prechildren_box.len() {
                        let d = durations[i];
                        prechildren_box[i].start_time = offset;
                        prechildren_box[i].end_time = offset + d;
                        prechildren_box[i].recalc_times();
                        offset += d;
                    }
                }
            }
            // If anchor_prechild is out of bounds, we simply ignore prechildren.
        }

        // --- Overwrite children based on ancestor_overwrite_level ---




    }

    pub fn overwrite_times(&mut self) {

        if self.overwrite_children.unwrap_or(false) {
            println!("set to true");
            let level = self.ancestor_overwrite_level.unwrap_or(0);
            println!("level: {}", level);
            // If level == 0, target is self; otherwise, get the ancestor.
            let target_node_ptr = if level == 0 {
                self as *mut _
            } else {
                unsafe { self.get_ancestor(level) }.unwrap_or(self as *mut _)
            };
            unsafe {println!("target_node_ptr is {},{}", (*target_node_ptr).start_time,(*target_node_ptr).end_time);}
            unsafe {
                if let Some(ref mut target_children) = (*target_node_ptr).children {
                    // For each child in the target node, if its start_time is after the first prechild's start_time, overwrite.
                    if let Some(ref prechildren_box) = self.prechildren {
                        if !prechildren_box.is_empty() {
                            let first_prechild_start = prechildren_box[0].start_time;
                            for child in target_children.iter_mut() { //need to keep recursing regardless of start time
                                // if child.start_time > first_prechild_start {
                                    overwrite_midi_recursive(child, first_prechild_start);
                                // }
                            }
                            
                        }
                    }
                }
            }
        }
        if let Some(ref mut children) = self.children {
            for child in children.iter_mut() {
                child.overwrite_times();
            }
        }

    }


}


