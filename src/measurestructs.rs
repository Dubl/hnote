use crate::types::*;
use crate::song_generator::*;




pub fn top_measure4()->SlMeasure { SlMeasure {
        long_ratio: 1.0,
        short_ratio: 2.0,
        orientation: 0, // forward
        master: 0,
        notes: vec![
            SlNote {midi_number: 60,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 62,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 64,velocity: 80,timing: "l".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 65,velocity: 90,timing: "m".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 66,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 67,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 68,velocity: 80,timing: "l".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 67,velocity: 90,timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 65,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 64,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},                    
            SlNote {midi_number: 62,velocity: 80,timing: "l".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 60,velocity: 90, timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 58,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 60,velocity: 100,timing: "s".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 62,velocity: 80,timing: "l".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 64,velocity: 90,timing: "m".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 66,velocity: 100,timing: "m".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 68,velocity: 80,timing: "m".to_string(),channel: 1,child_measure: None},//  Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 70,velocity: 100,timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 68,velocity: 80,timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 66,velocity: 80,timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            SlNote {midi_number: 64,velocity: 80,timing: "m".to_string(),channel: 1,child_measure: None},// Some(Box::new(child_measure.clone()))},
            ],
}}

// fn holding()->f64{


//     let c_major_scale = [60, 62, 64, 65, 67, 69, 71, 72]; // C major scale

//     //let song=generate_swing_beat_with_layers("Swing Trio", &c_major_scale, 8, 120 as f64); // 8 measures at 120 BPM
//     //let song=generate_swing_drum_beat3("Swing Drums w random durations", 8, 120.0, 1.0);
//     // let song=generate_pattern_song(
//     //     "Pattern-Based Song",
//     //     &[1, 2, 3, 1, 2, 3, 1, 2], // Pattern
//     //     140.0,                     // Tempo: 120 BPM
//     //     36,                        // MIDI number: C4
//     //     80,                        // Base velocity
//     //     4,                         // Number of measures
//     // );

//     let songx=generate_kick_hat_pattern(
//         "Kick and Hi-Hat Pattern",
//         &[
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)
            
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 0), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)


//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)
            
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 0), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)


//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)
            
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 0), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)


//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)
            
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 0), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)

//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('l', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 38), // Long timing for Kick Drum (MIDI 35)
//             ('l', 36), // Short timing for Hi-Hat (MIDI 42)
//             ('s', 38), // Long timing for Snare Drum (MIDI 38)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('s', 36), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 38), // Short timing for Open Hi-Hat (MIDI 46)
//             ('l', 0), // Short timing for Open Hi-Hat (MIDI 46)



//         ],
//         120.0,      // Tempo: 120 BPM
//         2.0,        // Long time relative value
//         1.0,        // Short time relative value
//         24,          // Number of measures
//     );





//     let top_measureold = SlMeasure {
//         long_ratio: 2.0,
//         short_ratio: 1.0,
//         orientation: 0, // forward
//         notes: vec![
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},

//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 38,velocity: 100,timing: 's',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 36,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},
//             SlNote {midi_number: 0,velocity: 100,timing: 'l',channel: 9,child_measure: Some(Box::new(child_measure.clone()))},


            





//         ],
//     };

// }