mod song_generator;
mod csv_manager;
mod types;


use std::env;
use std::cmp::Ordering;
use midir::{MidiOutput, MidiOutputConnection};
use windows::Win32::System::Performance::{
    QueryPerformanceCounter, QueryPerformanceFrequency,
};
use windows::Win32::System::Threading::{
    GetCurrentProcess, SetPriorityClass, REALTIME_PRIORITY_CLASS,
};
use std::time::Duration;

use serde::Deserialize;

use types::*;
use types::calculate_duration_from_locked;
use song_generator::*;

//{generate_songs, generate_pattern_song, save_generated_songs, generate_chord_progression, generate_swing_beat_with_layers, generate_swing_drum_beat, generate_swing_drum_beat2, generate_swing_drum_beat3};
use csv_manager::*;
use std::sync::{Arc, Mutex, mpsc};

use std::thread;

use std::collections::HashMap;
use std::fs::File;
use std::io::BufReader;
use csv::ReaderBuilder;
use std::error::Error;



#[derive(Debug, Deserialize)]
struct CsvRow {
    song_name: String,
    midi_number: u8,
    channel: u8,
    velocity: u8,
    start_time: f64,
    duration: f64,
}




struct HighResTimer {
    frequency: f64,
}

impl HighResTimer {
    fn new() -> Self {
        let mut frequency = 0;
        unsafe {
            QueryPerformanceFrequency(&mut frequency);
        }
        HighResTimer {
            frequency: frequency as f64,
        }
    }

    fn now(&self) -> f64 {
        let mut counter = 0;
        unsafe {
            QueryPerformanceCounter(&mut counter);
        }
        counter as f64 / self.frequency
    }
}

fn set_realtime_priority() {
    unsafe {
        let process = GetCurrentProcess();
        let g = match SetPriorityClass(process, REALTIME_PRIORITY_CLASS) {
            Ok(rtrn)=> rtrn,
            Err(error)=> panic!("problem"),
        };
        
    }
}



fn send_note_on(
    connection: &mut MidiOutputConnection,
    midi_number: u8,
    channel: u8,
    velocity: u8,
) -> f64 {
    let status_byte = 0x90 | (channel & 0x0F); // Note On for specified channel
    connection
        .send(&[status_byte, midi_number, velocity])
        .expect("Failed to send Note On message");
    HighResTimer::new().now()
}

fn send_note_off(connection: &mut MidiOutputConnection, midi_number: u8, channel: u8) -> f64 {
    let status_byte = 0x80 | (channel & 0x0F); // Note Off for specified channel
    connection
        .send(&[status_byte, midi_number, 0])
        .expect("Failed to send Note Off message");
    HighResTimer::new().now()
}


fn flatten_hnotes(note: &HNote) -> Vec<HNote> {
    let mut notes=vec![];

    // if note.midi_number!=0 {
        notes.extend(vec![note.clone()]);
    // }

    if let Some(children) = &note.children {
        for child in children.iter() {
            notes.extend(flatten_hnotes(child));
        }
    }
    if let Some(prechildren) = &note.prechildren {
        for prechild in prechildren.iter() {
            notes.extend(flatten_hnotes(prechild));
        }
    }
    notes
}

/// Plays a song by taking a single HNote representing the entire song.
/// This function flattens the hierarchical HNote structure into a flat list
/// of notes (sorted by start_time) and then processes them in a loop.
/// It sends note-on messages when the note’s start_time is reached and
/// sends note-off messages after the note’s duration has elapsed.
fn play_song(connection: &mut MidiOutputConnection, timer: &HighResTimer, song: &HNote) {
    // 1. Flatten the hierarchical HNote structure into a flat list.
    let mut flat_notes = flatten_hnotes(song);

    // 2. Sort the notes by their start_time.
    flat_notes.sort_by(|a, b| {
        a.start_time
            .partial_cmp(&b.start_time)
            .unwrap_or(Ordering::Equal)
    });

    // println!("{:?}", flat_notes);   
    // 3. Initialize the state:
    //    - inactive_notes: notes that haven't been triggered yet.
    //    - active_notes: notes that have been triggered and are waiting to be turned off.
    let mut inactive_notes: Vec<HNote> = flat_notes;
    let mut active_notes: Vec<(HNote, f64)> = Vec::new();

    // Small buffer before playback to ensure MIDI device is ready
    std::thread::sleep(Duration::from_millis(100));

    let start_time = timer.now();
    
    loop {
        let elapsed = timer.now() - start_time;
        let mut all_done = true;
        
        // Process inactive notes.
        // If a note's start_time has passed, trigger it (send note_on)
        // and move it to active_notes.
        inactive_notes.retain(|note| {
            if note.start_time <= elapsed {
                let actual_start = send_note_on(
                    connection,
                    note.midi_number,
                    note.channel,
                    note.velocity,
                );
                active_notes.push((note.clone(), actual_start));
                false // Remove from inactive_notes.
            } else {
                true // Keep in inactive_notes.
            }
        });
        
        // Process active notes.
        // If the note's elapsed time has reached its end_time (with a small tolerance),
        // send note_off and remove it from active_notes.
        active_notes.retain(|(note, _start)| {
            // Calculate the note's duration from its start_time and end_time.
            let duration = note.end_time - note.start_time;
            if elapsed >= note.start_time + duration - 0.01 {
                let _actual_stop = send_note_off(connection, note.midi_number, note.channel);
                false // Remove from active_notes.
            } else {
                true // Keep in active_notes.
            }
        });
        
        // If there are still notes to process, keep running.
        if !inactive_notes.is_empty() || !active_notes.is_empty() {
            all_done = false;
        }
        
        // Exit the loop if all notes have been processed.
        if all_done {
            break;
        }
        
        // Small sleep to reduce CPU usage.
        std::thread::sleep(Duration::from_micros(500));
    }
}


fn initialize_midi() -> MidiOutputConnection {
    let midi_out = MidiOutput::new("Rust MIDI Output").expect("Failed to create MIDI output");
    let out_ports = midi_out.ports();

    if out_ports.is_empty() {
        panic!("No available MIDI output ports");
    }
    for port in &out_ports {
        println!("port name: {}", midi_out.port_name(&port).unwrap());
    }

    let port = &out_ports[0]; // Select the first available port
    midi_out.connect(port, "Rust MIDI").expect("Failed to connect to MIDI output")
}


fn main() {

    let args: Vec<String> = env::args().collect();

    let function = args.get(1)
        .map(|s| s.as_str())
        .unwrap_or("generate_hnote_from_rules");


    println!("running {function}");

    if function=="generate_hnote_from_rules" {

        let mut connection = initialize_midi();
        let timer = HighResTimer::new();

        let calllistpath = "calllist.jsonc".to_string();

        let calls = load_calllist_from_file(&calllistpath)
        .expect("Failed to load initial calls");

        let measurelistpath = "measures.json".to_string();
        let sourcehnotes = load_hnotelist_from_file(&measurelistpath) //vec of hnote
        .expect("Failed to load initial measures");

        let prechild_library_path = "prechildren_library.json".to_string();
        let prechild_library = load_prechild_library_from_file(&prechild_library_path)
            .unwrap_or_else(|_| {
                println!("Warning: Could not load prechild library from {}, using empty library", prechild_library_path);
                Vec::new()
            });

        let mut resulthnote = HNote {
            start_time: 0.0,
            end_time: 30.0,
            timing: 1.0,
            child_direction: Direction::Sequential,
            children: None,
            prechildren: None,
            anchor_prechild: None,
            end_of_silence_prechild: None,
            anchor_end: None,
            timing_based_on_children: None,
            overwrite_children: None,
            ancestor_overwrite_level: None,
            parent: None,
            midi_number: 0,
            velocity: 0,
            channel: 0,
            rolled:None,
            print_length: None,
            name: None
        };


        apply_hnote_calls(&sourcehnotes, &prechild_library, &calls, &mut resulthnote);

        resulthnote.assign_parents();

        // Calculate duration from locked note if one exists
        if let Some(duration) = calculate_duration_from_locked(&resulthnote) {
            println!("Found locked note, calculated song duration: {:.2} seconds", duration);
            resulthnote.end_time = duration;
        } else {
            println!("No locked note found, using default end_time: {:.2} seconds", resulthnote.end_time);
        }

        resulthnote.recalc_times();
        resulthnote.overwrite_times();
        resulthnote.print_lengths();
        //let mut ancestors: Vec<*mut HNote> = Vec::new();
        //resulthnote.recalc_times_with_ancestors(&mut ancestors);

        // println!("\n=== All newly-created copies ===");
        // let pretty_json = serde_json::to_string_pretty(&resulthnote).unwrap();
        // println!("{}", pretty_json);

        let tree_lines = render_node_rect(&resulthnote);

        let tree_output = tree_lines.join("\n");
    
        write_to_file(&tree_output);
    

        play_song(&mut connection, &timer, &resulthnote);

        // Buffer time to let the last note finish playing
        std::thread::sleep(Duration::from_millis(1500));

    }



    
    else {
            println!("what's this?");
    }
}

