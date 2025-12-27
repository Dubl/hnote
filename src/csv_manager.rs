use std::fs::File;
use std::io::Write;
use std::io::BufReader;
use std::error::Error;
use csv::{ReaderBuilder, Writer};
use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use serde_json::from_reader;
use crate::types::*;
use unicode_width::UnicodeWidthStr;



pub fn load_hnotelist_from_file(path: &str) -> Result<Vec<HNote>, Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    // Suppose the file is an array of measures: [ { "long_ratio": 2.0, ...}, ... ]
    let measurelist: Vec<HNote> = from_reader(reader)?;
    Ok(measurelist)
}



pub fn load_calllist_from_file(path: &str) -> Result<Vec<Call>, Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    // Suppose the file is an array of measures: [ { "long_ratio": 2.0, ...}, ... ]
    let calllist: Vec<Call> = from_reader(reader)?;
    Ok(calllist)
}



pub fn write_to_json(resultHNote: &HNote) -> std::io::Result<()> {


    // Serialize struct to JSON string
    let json_string = serde_json::to_string_pretty(&resultHNote).expect("Failed to serialize");

    // Write JSON to a file
    let mut file = File::create("HNote.json")?;
    file.write_all(json_string.as_bytes())?;

    println!("JSON written to HNote.json");
    
    Ok(())
}


pub fn write_to_file(tree_output: &String) -> std::io::Result<()> {


    // Serialize struct to JSON string
    let mut file = File::create("tree_output.txt")?;
    file.write_all(tree_output.as_bytes())?;
    
    Ok(())
}



// // Render a node into a rectangular block represented as Vec<String>.
// // Each line in the block has equal length.
pub fn render_node_rect(node: &HNote) -> Vec<String> {
    // The first line is the node's label.
    let label = format!("[{:.2} - {:.2} {}]", node.start_time, node.end_time, node.midi_number);
    let mut block = vec![label.clone()];

    // Get the children block if any.
    // Get both children and prechildren as Option<&Vec<HNote>>
    let children_opt = node.children.as_ref().map(|b| b.as_ref());
    let prechildren_opt = node.prechildren.as_ref().map(|b| b.as_ref());

    // Treat missing lists as empty.
    let children_empty = children_opt.map_or(true, |c| c.is_empty());
    let prechildren_empty = prechildren_opt.map_or(true, |p| p.is_empty());

    // Only return early if both are empty.
    if children_empty && prechildren_empty {
        let width = label.len();
        return vec![format!("{:width$}", label, width = width)];
    }

    // Combine prechildren and children into one vector.
    // Each tuple holds (is_prechild, &HNote)
    let mut combined: Vec<(bool, &HNote)> = Vec::new();
    if let Some(pre) = prechildren_opt {
        for child in pre {
            combined.push((true, child));
        }
    }
    if let Some(ch) = children_opt {
        for child in ch {
            combined.push((false, child));
        }
    }
    match node.child_direction {
        // Direction::Sequential => {
        //     // For sequential children, render each child's rectangular block,
        //     // and stack them vertically with connectors.
        //     let mut child_blocks = Vec::new();
        //     for (i, child) in children.iter().enumerate() {
        //         let child_rect = render_node_rect(child);
        //         // Add connectors to the first line.
        //         let connector = if i == children.len() - 1 { "└── " } else { "├── " };
        //         let mut new_block = Vec::new();
        //         if let Some(first) = child_rect.get(0) {
        //             new_block.push(format!("{}{}", connector, first));
        //         }
        //         // For subsequent lines, prepend with spaces (same length as connector).
        //         // for line in child_rect.iter().skip(1) {
        //         //     new_block.push(format!("{:width$}{}", "", line, width = connector.len()));
        //         // }


        //         let cont_prefix = if i == children.len() - 1 { "    " } else { "│   " };
        //         for line in child_rect.iter().skip(1) {
        //             new_block.push(format!("{}{}", cont_prefix, line));
        //         }




        //         child_blocks.push(new_block);
        //     }
        //     // Stack the child blocks vertically.
        //     block.extend(child_blocks.into_iter().flatten());
        // }


        Direction::Sequential => {
            // For sequential children, render each child's rectangular block,
            // and stack them vertically with connectors.
            // Combine prechildren and children into one vector.
            // Each entry is a tuple: (is_prechild, &HNote)

            let mut child_blocks = Vec::new();
            for (i, (is_pre, child)) in combined.iter().enumerate() {
                // Render the child block.
                let mut child_rect = render_node_rect(child);
                // If this child is from prechildren, modify its label.
                if *is_pre {
                    if let Some(first_line) = child_rect.get_mut(0) {
                        *first_line = format!("p{}", first_line);
                    }
                }
                // Use connectors as before.
                let connector = if i == combined.len() - 1 { "└── " } else { "├── " };
                let mut new_block = Vec::new();
                if let Some(first) = child_rect.get(0) {
                    new_block.push(format!("{}{}", connector, first));
                }
                let cont_prefix = if i == combined.len() - 1 { "    " } else { "│   " };
                for line in child_rect.iter().skip(1) {
                    new_block.push(format!("{}{}", cont_prefix, line));
                }
                child_blocks.push(new_block);
            }
            block.extend(child_blocks.into_iter().flatten());

        }






        Direction::Sidebyside => {
            let children = children_opt.unwrap();
            // For parallel children, render each child's block.
            let child_blocks: Vec<Vec<String>> = children.iter().map(|child| render_node_rect(child)).collect();
            // Determine the max height for these blocks.
            let max_height = child_blocks.iter().map(|b| b.len()).max().unwrap_or(0);
            // Normalize each block: pad with empty lines if necessary,
            // and pad each line to have equal width per block.
            let normalized: Vec<Vec<String>> = child_blocks
                .iter()
                .map(|block| {
                    let width = block.iter().map(|line| line.len()).max().unwrap_or(0);
                    let mut new_block: Vec<String> = block
                        .iter()
                        .map(|line| format!("{:width$}", line, width = width))
                        .collect();
                    while new_block.len() < max_height {
                        new_block.push(" ".repeat(width));
                    }
                    new_block
                })
                .collect();
            // Merge the blocks horizontally row by row.
            let mut merged = Vec::new();
            for i in 0..max_height {
                let row: Vec<String> = normalized.iter().map(|b| b[i].clone()).collect();
                // Use a separator of 4 spaces between columns.
                merged.push(row.join("    "));
            }
            // Create a header line made of dashes with same column widths.
            // let header_parts: Vec<String> = normalized
            //     .iter()
            //     .map(|b| {
            //         let w = b.iter().map(|s| s.width()).max().unwrap_or(0);
            //         //"-".repeat(w)
            //          "-".repeat(w)
            //     })
            //     .collect();

            let header_parts: Vec<String> = normalized
            .iter()
            .enumerate()
            .map(|(i, b)| {
                let w = b.iter().map(|s| s.width()).max().unwrap_or(0);
                if i == normalized.len() - 1 {
                    "".to_string()
                } else {
                    "-".repeat(w)
                }
            })
            .collect();
        



            let header = format!("|{}", header_parts.join("---┐"));
            // Add an indent so that the children block is shifted right to align with parent's connector.
            let indent = "    ";
            let merged_with_indent: Vec<String> = merged.into_iter().map(|s| format!("{}{}", indent, s)).collect();
            // Append header and merged rows.
            block.push(format!("{}{}", indent, header));
            block.extend(merged_with_indent);
        }
    }

    // Finally, ensure every line in the block has equal width.
    let max_width = block.iter().map(|line| line.len()).max().unwrap_or(0);
    block = block.into_iter().map(|line| format!("{:width$}", line, width = max_width)).collect();
    block
}


