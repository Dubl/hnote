// Dependency-free Standard MIDI File (SMF) writer.
//
// Takes the same flat, resolved note list that `play_song` streams to a live
// MIDI port and writes it to a `.mid` file instead. This is the "front-end
// validation" path: render the HNote tree to a file, commit it, listen on phone.
//
// Format 0 (single track, multi-channel). Absolute note times are in seconds;
// we convert to ticks under a fixed tempo. The stated BPM is arbitrary because
// the conversion is consistent — wall-clock timing is preserved regardless.

use crate::types::HNote;

const PPQ: u16 = 480; // ticks per quarter note (SMF division)
const TEMPO_US_PER_QUARTER: u32 = 500_000; // 120 BPM; arbitrary, timing stays correct
// ticks per second = PPQ * 1_000_000 / tempo
const TICKS_PER_SECOND: f64 = PPQ as f64 * 1_000_000.0 / TEMPO_US_PER_QUARTER as f64;

/// One MIDI channel-voice event, tagged with its absolute tick and a sort order
/// so note-offs win the tie against note-ons at the same tick.
struct Event {
    tick: u64,
    order: u8, // 0 = note-off (sorts first), 1 = note-on
    bytes: [u8; 3],
}

/// Encode a value as a MIDI variable-length quantity (big-endian, 7 bits/byte).
fn write_vlq(buf: &mut Vec<u8>, mut value: u32) {
    let mut stack = vec![(value & 0x7f) as u8];
    value >>= 7;
    while value > 0 {
        stack.push(((value & 0x7f) as u8) | 0x80);
        value >>= 7;
    }
    for b in stack.iter().rev() {
        buf.push(*b);
    }
}

/// Write a flat list of resolved notes to `path` as a `.mid` file.
///
/// Notes with `midi_number == 0` are treated as structural/container nodes and
/// skipped (matching the sounding-note convention used elsewhere).
pub fn write_midi_file(notes: &[HNote], path: &str) -> std::io::Result<()> {
    let mut events: Vec<Event> = Vec::new();

    for n in notes {
        if n.midi_number == 0 {
            continue;
        }
        let on_tick = (n.start_time * TICKS_PER_SECOND).round().max(0.0) as u64;
        let mut off_tick = (n.end_time * TICKS_PER_SECOND).round().max(0.0) as u64;
        if off_tick <= on_tick {
            off_tick = on_tick + 1; // guarantee a positive-length note
        }
        let ch = n.channel & 0x0f;
        events.push(Event {
            tick: on_tick,
            order: 1,
            bytes: [0x90 | ch, n.midi_number, n.velocity],
        });
        events.push(Event {
            tick: off_tick,
            order: 0,
            bytes: [0x80 | ch, n.midi_number, 0],
        });
    }

    // Absolute order: by tick, then note-offs before note-ons at the same tick.
    events.sort_by(|a, b| a.tick.cmp(&b.tick).then(a.order.cmp(&b.order)));

    // --- Build the track chunk body ---
    let mut track: Vec<u8> = Vec::new();

    // Tempo meta event at tick 0: FF 51 03 tt tt tt
    write_vlq(&mut track, 0);
    track.extend_from_slice(&[
        0xFF,
        0x51,
        0x03,
        (TEMPO_US_PER_QUARTER >> 16) as u8,
        (TEMPO_US_PER_QUARTER >> 8) as u8,
        TEMPO_US_PER_QUARTER as u8,
    ]);

    let mut last_tick: u64 = 0;
    for ev in &events {
        let delta = (ev.tick - last_tick) as u32;
        write_vlq(&mut track, delta);
        track.extend_from_slice(&ev.bytes);
        last_tick = ev.tick;
    }

    // End of track: FF 2F 00
    write_vlq(&mut track, 0);
    track.extend_from_slice(&[0xFF, 0x2F, 0x00]);

    // --- Assemble the file ---
    let mut out: Vec<u8> = Vec::new();
    out.extend_from_slice(b"MThd");
    out.extend_from_slice(&[0, 0, 0, 6]); // header length
    out.extend_from_slice(&[0, 0]); // format 0
    out.extend_from_slice(&[0, 1]); // one track
    out.extend_from_slice(&PPQ.to_be_bytes()); // division

    out.extend_from_slice(b"MTrk");
    out.extend_from_slice(&(track.len() as u32).to_be_bytes());
    out.extend_from_slice(&track);

    std::fs::write(path, out)?;
    Ok(())
}
