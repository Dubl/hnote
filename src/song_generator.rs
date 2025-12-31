use crate::types::*;
use crate::csv_manager::*;
use rand::Rng;
use rand::prelude::SliceRandom;



pub fn apply_hnote_call(
    sourcehnotes: &[HNote],
    prechild_library: &[HNote],
    call: &Call,
    resulthnote: &mut HNote,
    passedstruct: Option<&mut HNote>
) {
    match call {
        Call::Roll { target, amount, then, status } => {
            // Handle inactive status - skip entirely
            if *status == CallStatus::Inactive {
                return;
            }
            println!("in roll");
            let mut from_hnote = sourcehnotes[1].clone();
            // println!("from_hnote:{:?}",from_hnote);
            let mut rollee =passedstruct.unwrap().clone();
            println!("from_hnote:{:?}",from_hnote);
            println!("rollee:{:?}",rollee);            
            // 1) Take hnote1.prechildren, or default to an empty Vec if None
            let mut from_hnote1 = from_hnote
                .prechildren
                .take()                       // take the Option<Box<Vec<HNote>>>, leaving None
                .map(|boxed_vec| *boxed_vec)  // unbox into Vec<HNote>
                .unwrap_or_default();         // if None, produce an empty Vec
            // println!("from_hnote1{:?}",from_hnote1);
            // 2) Find the descendant in hnote2 with rolled == Some(true)
            println!("rollee find rolled {:?}",rollee.find_rolled_mut());
            if let Some(descendant) = rollee.find_rolled_mut() {
                // 3) Ensure descendant.prechildren is Some(Box<Vec<HNote>>>) 
                //    and append from_hnote1
                println!("found a descendant");
                let target_prechildren = descendant
                    .prechildren
                    .get_or_insert_with(|| Box::new(Vec::new()));
                println!("target_prechilren: {:?}",target_prechildren);
                target_prechildren.append(&mut from_hnote1);

                descendant.timing_based_on_children=Some(false);
                descendant.anchor_prechild=Some(6);
                descendant.anchor_end=Some(true);
                descendant.overwrite_children=Some(true);
                descendant.ancestor_overwrite_level=Some(1);
            }

      

            if let Some(next_call) = then {
                return apply_hnote_call(sourcehnotes, prechild_library, next_call, resulthnote, Some(&mut rollee));
            }
            else {
            // Handle silent status - set all midi notes to 0
            if *status == CallStatus::Silent {
                rollee.silence();
            }
            // 4) Return hnote2
            resulthnote.children
            .get_or_insert_with(|| Box::new(Vec::new()))
            // Now we have &mut Box<Vec<CustomType>>, so we can push
            .extend(vec![rollee]);

            }

        }
        Call::Twice { target, then, status } => {
            // Handle inactive status - skip entirely
            if *status == CallStatus::Inactive {
                return;
            }
            // 1. Call maketwocopies on the chosen struct
            // println!("Calling maketwocopies on object #{}", target);
            let mut copies = sourcehnotes[*target].twice();

            // 2. We store them in `results` (or do something else with them)
            // println!("Created {} copies from object #{}", copies.len(), target);


            // 3. Apply any chained calls in `then` to each copy
            if let Some(next_call) = then {
                for copy in &mut copies {
                    apply_hnote_call(sourcehnotes, prechild_library, next_call, resulthnote, Some(copy));
                }
            }
            else {
                // Handle silent status - set all midi notes to 0
                if *status == CallStatus::Silent {
                    for copy in &mut copies {
                        copy.silence();
                    }
                }
                resulthnote.children
                .get_or_insert_with(|| Box::new(Vec::new()))
                // Now we have &mut Box<Vec<CustomType>>, so we can push
                .extend(copies);

            }

        }
        Call::Once { target, then, status } => {
            // Handle inactive status - skip entirely
            if *status == CallStatus::Inactive {
                return;
            }
            // 1. Call maketwocopies on the chosen struct
            // println!("Calling maketwocopies on object #{}", target);
            // let copy = sourcehnotes[*target].once();
            let mut copy= sourcehnotes[*target].clone();
            // 2. We store them in `results` (or do something else with them)
            // println!("Created {} copies from object #{}", copies.len(), target);

            // 3. Apply any chained calls in `then`
            if let Some(next_call) = then {
                println!("then found:{:?}", next_call);
                apply_hnote_call(sourcehnotes, prechild_library, next_call, resulthnote, Some(&mut copy));
            }
            else {
                println!("no then found");
                // Handle silent status - set all midi notes to 0
                if *status == CallStatus::Silent {
                    copy.silence();
                }
                resulthnote.children
                .get_or_insert_with(|| Box::new(Vec::new()))
                // Now we have &mut Box<Vec<CustomType>>, so we can push
                .extend(vec![copy]);

            }

        }
        Call::Combine { calls, direction, then, status } => {
            // Handle inactive status - skip entirely
            if *status == CallStatus::Inactive {
                return;
            }
            // Create a wrapper HNote with the specified direction
            let mut wrapper = HNote {
                midi_number: 0,
                velocity: 100,
                timing: 1.0,
                channel: 9,
                child_direction: direction.clone(),
                children: Some(Box::new(Vec::new())),
                start_time: 0.0,
                end_time: 0.0,
                prechildren: None,
                anchor_prechild: None,
                anchor_end: None,
                timing_based_on_children: None,
                overwrite_children: None,
                ancestor_overwrite_level: None,
                parent: None,
                rolled: None,
                print_length: None,
                name: None,
            };

            // Process each nested call and add results as children of the wrapper
            for nested_call in calls {
                apply_hnote_call(sourcehnotes, prechild_library, nested_call, &mut wrapper, None);
            }

            // Apply any chained calls in `then`
            if let Some(next_call) = then {
                apply_hnote_call(sourcehnotes, prechild_library, next_call, resulthnote, Some(&mut wrapper));
            } else {
                // Handle silent status - set all midi notes to 0
                if *status == CallStatus::Silent {
                    wrapper.silence();
                }
                resulthnote.children
                    .get_or_insert_with(|| Box::new(Vec::new()))
                    .extend(vec![wrapper]);
            }
        }
        Call::InjectPrechildren { target, path, prechild_library_target, then, status } => {
            // Handle inactive status - skip entirely
            if *status == CallStatus::Inactive {
                return;
            }
            // 1. Clone measure from sourcehnotes[target]
            let mut copy = sourcehnotes[*target].clone();

            // 2. Navigate to target node using path
            if let Some(target_node) = copy.navigate_path_mut(path) {
                // 3. Get template from prechild library
                let template = &prechild_library[*prechild_library_target];

                // 4. Extract and copy fields from template
                target_node.prechildren = template.prechildren.clone();
                target_node.timing_based_on_children = template.timing_based_on_children;
                target_node.anchor_prechild = template.anchor_prechild;
                target_node.anchor_end = template.anchor_end;
                target_node.overwrite_children = template.overwrite_children;
                target_node.ancestor_overwrite_level = template.ancestor_overwrite_level;
            }

            // 5. Handle 'then' chaining
            if let Some(next_call) = then {
                apply_hnote_call(sourcehnotes, prechild_library, next_call, resulthnote, Some(&mut copy));
            } else {
                // Handle silent status - set all midi notes to 0
                if *status == CallStatus::Silent {
                    copy.silence();
                }
                // 6. Add to resulthnote
                resulthnote.children
                    .get_or_insert_with(|| Box::new(Vec::new()))
                    .extend(vec![copy]);
            }
        }

    }
}

/// Apply a *list* of calls in sequence.
pub fn apply_hnote_calls(
    sourcehnotes: &[HNote],
    prechild_library: &[HNote],
    calls: &[Call],
    resulthnote: &mut HNote,
) {
    println!("hi");
    for call in calls {
        apply_hnote_call(sourcehnotes, prechild_library, call, resulthnote, None);
    }
}