use crate::types::*;
use crate::csv_manager::*;
use rand::Rng;
use rand::prelude::SliceRandom;



pub fn apply_hnote_call(
    sourcehnotes: &[HNote],
    call: &Call,
    resulthnote: &mut HNote,
    passedstruct: Option<&mut HNote>
) {
    match call {
        Call::Roll { target, amount, then } => {
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
                return apply_hnote_call(sourcehnotes, next_call, resulthnote, Some(&mut rollee));
            } 
            else {
            // 4) Return hnote2
            resulthnote.children
            .get_or_insert_with(|| Box::new(Vec::new()))
            // Now we have &mut Box<Vec<CustomType>>, so we can push
            .extend(vec![rollee]);     

            }

        }
        Call::Twice { target, then } => {
            // 1. Call maketwocopies on the chosen struct
            // println!("Calling maketwocopies on object #{}", target);
            let copies = sourcehnotes[*target].twice();

            // 2. We store them in `results` (or do something else with them)
            // println!("Created {} copies from object #{}", copies.len(), target);


            // 3. Apply any chained calls in `then`
            if let Some(next_call) = then {
                return apply_hnote_call(sourcehnotes, next_call, resulthnote, Some(&mut copies));
            } 

            else {
                resulthnote.children
                .get_or_insert_with(|| Box::new(Vec::new()))
                // Now we have &mut Box<Vec<CustomType>>, so we can push
                .extend(copies);

            }
            
        }
        Call::Once { target, then } => {
            // 1. Call maketwocopies on the chosen struct
            // println!("Calling maketwocopies on object #{}", target);
            // let copy = sourcehnotes[*target].once();
            let mut copy= sourcehnotes[*target].clone();
            // 2. We store them in `results` (or do something else with them)
            // println!("Created {} copies from object #{}", copies.len(), target);

            // 3. Apply any chained calls in `then`
            if let Some(next_call) = then {
                println!("then found:{:?}", next_call);
                apply_hnote_call(sourcehnotes, next_call, resulthnote, Some(&mut copy));
            } 
            else {
                println!("no then found");
                resulthnote.children
                .get_or_insert_with(|| Box::new(Vec::new()))
                // Now we have &mut Box<Vec<CustomType>>, so we can push
                .extend(vec![copy]);
                
            }
            
        }

    }
}

/// Apply a *list* of calls in sequence.
pub fn apply_hnote_calls(
    sourcehnotes: &[HNote],
    calls: &[Call],
    resulthnote: &mut HNote,
) {
    println!("hi");
    for call in calls {
        apply_hnote_call(sourcehnotes, call, resulthnote, None);
    }
}