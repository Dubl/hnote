# MIDI Music Generation System - User Guide

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Concepts](#core-concepts)
4. [File Structure](#file-structure)
5. [Data Structures and Attributes](#data-structures-and-attributes)
6. [Call Functions Reference](#call-functions-reference)
7. [Creating Music](#creating-music)
8. [Running the Program](#running-the-program)
9. [Examples](#examples)
10. [Tips and Best Practices](#tips-and-best-practices)

---

## Overview

This system allows you to compose drum patterns (or any MIDI music) using a hierarchical, rule-based approach. Instead of manually placing every note, you define:

1. **Base patterns** (measures) - reusable building blocks
2. **Embellishments** (prechild library) - fills, rolls, and variations
3. **Composition rules** (call lists) - how to combine and modify patterns

The system then generates the complete MIDI note tree with precise timing.

---

## System Architecture

### Three Layers of Abstraction

```
Layer 1: Base Measures (measures.json)
         ↓
Layer 2: Prechild Library (prechildren_library.json)
         ↓
Layer 3: Call Lists (calllist.jsonc)
         ↓
      Final Song
```

**Why this matters:**
- **Reusability**: Define a hi-hat pattern once, use it everywhere
- **Modularity**: Swap out fills without touching base patterns
- **Expressiveness**: Compose at a high level ("combine hi-hats with this kick pattern, add a fill at the end")

---

## Core Concepts

### HNote (Hierarchical Note)

An `HNote` is a musical event that can contain other events. Think of it like a tree:

```
Measure (4 beats)
├── Beat 1
│   ├── Note: Kick drum
│   └── Prechild: Ghost note (before the kick)
├── Beat 2
│   └── Note: Snare
├── Beat 3
│   └── Note: Kick drum
└── Beat 4
    └── Note: Snare with roll (prechildren)
```

**Key insight**: Every level can have timing, velocity, and its own sub-events.

### Children vs Prechildren

- **Children**: Normal sub-events that happen within the parent's time window
- **Prechildren**: Events that can happen BEFORE, DURING, or AFTER the parent's time
  - Used for fills, rolls, grace notes, and embellishments
  - Positioned using anchors (see below)

### Timing System

The system uses **proportional timing**:

```json
"timing": 2.0
```

This is NOT duration in seconds—it's a **share** of the available time.

**Example:**
```
Parent duration: 4.0 seconds
Child A timing: 1.0
Child B timing: 3.0
Total shares: 4.0

Child A gets: (1.0 / 4.0) × 4.0 = 1.0 second
Child B gets: (3.0 / 4.0) × 4.0 = 3.0 seconds
```

---

## File Structure

### Project Files

```
hello-rust/
├── src/
│   ├── main.rs                    # Entry point
│   ├── types.rs                   # HNote and Call definitions
│   ├── song_generator.rs          # Call processing logic
│   └── csv_manager.rs             # File loading/saving
├── measures.json          # Base patterns library
├── prechildren_library.json    # Embellishments library
├── calllist.jsonc  # Composition instructions
├── calllist.jsonc # Alternative composition
└── tree_output.txt                # Visual tree output (generated)
```

---

## Data Structures and Attributes

### HNote Structure

```json
{
  "midi_number": 36,           // MIDI note (36 = kick, 38 = snare, 42/43 = hi-hat)
  "velocity": 100,             // Volume (0-127)
  "timing": 2.0,               // Proportional time share
  "channel": 9,                // MIDI channel (9 = drums)
  "child_direction": "sequential",  // How children are arranged
  "children": [...],           // Array of child HNotes
  "prechildren": [...],        // Array of embellishment HNotes

  // Prechild timing controls (optional)
  "anchor_prechild": 2,        // Which prechild is the anchor (1-indexed)
  "anchor_end": true,          // Anchor to parent's end (true) or start (false)
  "timing_based_on_children": true,  // Scale prechildren based on children's timing

  // Overwrite controls (optional)
  "overwrite_children": false, // Should prechildren silence conflicting children?
  "ancestor_overwrite_level": 2  // How many levels up to apply overwrite
}
```

### Common MIDI Drum Numbers

```
36 = Bass Drum (Kick)
38 = Acoustic Snare
42 = Closed Hi-Hat
43 = High Floor Tom
46 = Open Hi-Hat
51 = Ride Cymbal
55 = Splash Cymbal
58 = Vibraslap
59 = Ride Cymbal 2
```

### Child Direction

```json
"child_direction": "sequential"  // Children play one after another
"child_direction": "sidebyside"  // Children play simultaneously
```

**Visual:**
```
Sequential:        Sidebyside:
[Note A]           [Note A]
[Note B]           [Note B]  (at same time)
[Note C]           [Note C]
```

### Anchor System (for Prechildren)

Controls WHERE prechildren are positioned relative to the parent note.

#### anchor_prechild (1-indexed)

Which prechild is the "anchor" that aligns with the parent.

**Example:**
```json
"anchor_prechild": 2,
"prechildren": [
  {"midi_number": 43, "timing": 0.26},  // This one comes BEFORE
  {"midi_number": 36, "timing": 0.26},  // THIS IS THE ANCHOR
  {"midi_number": 38, "timing": 0.26}   // This one comes AFTER
]
```

#### anchor_end

- `true`: Anchor aligns with parent's END time
- `false`: Anchor aligns with parent's START time

**Example (anchor_end: false):**
```
Parent:     [==================]
                ↑
Anchor here (start)
Prechildren: [pre1][ANCHOR][pre3]
```

**Example (anchor_end: true):**
```
Parent:     [==================]
                              ↑
                    Anchor here (end)
Prechildren:          [pre1][ANCHOR][pre3]
```

#### timing_based_on_children

- `true`: Scale prechild timing based on children's timing shares
- `false`: Scale prechild timing based on parent's duration

**When to use:**
- `true`: When you want the embellishment to "fit" within the children's rhythm
- `false`: When you want the embellishment to be independent of children

---

## Call Functions Reference

Call functions are instructions for building your song from base patterns.

### 1. Once

Clone a single measure.

```json
{
  "target": 0,
  "function": "once"
}
```

**Parameters:**
- `target`: Index in `measures.json` (0-based)

**Result:** Copy of that measure added to the song.

---

### 2. Twice

Clone a measure twice.

```json
{
  "target": 1,
  "function": "twice"
}
```

**Result:** Two copies of the measure, played sequentially.

---

### 3. Combine

Combine multiple calls with a specific layout direction.

```json
{
  "function": "combine",
  "direction": "sidebyside",
  "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]
}
```

**Parameters:**
- `direction`: "sequential" or "sidebyside"
- `calls`: Array of nested call objects

**Use cases:**
- `sidebyside`: Layer hi-hats with kick/snare
- `sequential`: Chain different sections

**Example (sidebyside):**
```
Result: Hi-hats playing simultaneously with kick/snare pattern
Timeline: 0--------------------4.0
         [Hi-hat pattern      ]
         [Kick/snare pattern  ]
```

---

### 4. InjectPrechildren

Surgically inject embellishments into specific notes using path-based targeting.

```json
{
  "target": 2,
  "function": "injectprechildren",
  "path": [0],
  "prechild_library_target": 1
}
```

**Parameters:**
- `target`: Base measure index
- `path`: Navigation path (array of child indices)
- `prechild_library_target`: Template index in prechild library

**Path Examples:**
- `[]` = Target the root of the measure
- `[0]` = Target the first child
- `[3, 1]` = Target the second child of the fourth child

**What gets injected:**
- `prechildren` array
- `anchor_prechild`
- `anchor_end`
- `timing_based_on_children`
- `overwrite_children`
- `ancestor_overwrite_level`

**Use cases:**
- Adding a snare roll before a particular hit
- Adding a crash cymbal at a specific moment
- Creating variations without duplicating entire measures

---

### 5. Roll (Advanced)

Dynamically inject prechildren with special "rolled" targeting.

```json
{
  "target": 1,
  "amount": 4,
  "function": "roll"
}
```

**Note:** This is more advanced and requires measures with `"rolled": true` markers.

---

### Call Chaining with "then"

All call functions support chaining:

```json
{
  "target": 0,
  "function": "once",
  "then": {
    "target": 1,
    "function": "injectprechildren",
    "path": [0],
    "prechild_library_target": 2
  }
}
```

**Result:** First copies measure 0, THEN injects prechildren into it before adding to the song.

---

## Creating Music

### Step 1: Create Base Measures

**File:** `measures.json`

Define your fundamental patterns:

```json
[
  {
    "midi_number": 0,
    "velocity": 100,
    "timing": 2,
    "channel": 9,
    "child_direction": "sequential",
    "children": [
      {"midi_number": 43, "velocity": 60, "timing": 2.0, "channel": 9, "children": null},
      {"midi_number": 42, "velocity": 50, "timing": 2.0, "channel": 9, "children": null}
    ]
  }
]
```

**Tips:**
- Index 0 is often a hi-hat pattern
- Index 1 is often a kick/snare pattern
- Keep them simple and reusable

---

### Step 2: Create Embellishment Templates

**File:** `prechildren_library.json`

Define reusable fills and embellishments:

```json
[
  {
    "midi_number": 38,
    "velocity": 80,
    "timing": 1.95,
    "channel": 9,
    "children": null,
    "timing_based_on_children": false,
    "anchor_prechild": 2,
    "anchor_end": true,
    "overwrite_children": false,
    "ancestor_overwrite_level": 2,
    "prechildren": [
      {"midi_number": 58, "velocity": 80, "timing": 2.0, "channel": 9, "children": null},
      {"midi_number": 0, "velocity": 80, "timing": 0.20, "channel": 9, "children": null}
    ]
  }
]
```

**Note:** Only the prechild-related fields will be used when injecting.

---

### Step 3: Compose with Call Lists

**File:** `calllist.jsonc`

Combine patterns into a full song:

```json
[
  {
    "function": "combine",
    "direction": "sidebyside",
    "calls": [
      {"target": 0, "function": "once"},
      {"target": 1, "function": "once"}
    ]
  },
  {
    "function": "combine",
    "direction": "sidebyside",
    "calls": [
      {"target": 0, "function": "once"},
      {
        "target": 1,
        "function": "injectprechildren",
        "path": [0],
        "prechild_library_target": 2
      }
    ]
  }
]
```

**This creates:**
1. First measure: Hi-hats layered with basic kick/snare
2. Second measure: Hi-hats layered with kick/snare that has a fill on the first beat

---

## Running the Program

### From VS Code

#### Option 1: Using the Run Button

1. Open `src/main.rs`
2. Click the "Run" button at the top right (▷)
3. Or press `Ctrl+F5` (Windows/Linux) or `Cmd+F5` (Mac)

#### Option 2: Using the Terminal

1. Open the integrated terminal in VS Code (`Ctrl+` ` or View → Terminal)
2. Run:
   ```bash
   cargo run
   ```

#### Option 3: With Arguments

To specify which call list to use:

1. Open `.vscode/launch.json` (create if it doesn't exist):
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "type": "lldb",
         "request": "launch",
         "name": "Debug",
         "cargo": {
           "args": ["build", "--bin=hello-rust", "--package=hello-rust"]
         },
         "args": ["generate_hnote_from_rules"],
         "cwd": "${workspaceFolder}"
       }
     ]
   }
   ```

2. Or modify `src/main.rs` line 238 to change the call list:
   ```rust
   let calllistpath = "calllist.jsonc".to_string();
   ```

### Changing the Call List

Edit `src/main.rs` around line 237:

```rust
//let calllistpath = "calllist.jsonc".to_string();
let calllistpath = "calllist.jsonc".to_string();
//let calllistpath = "my_calllist2.jsonc".to_string();
//let calllistpath = "calllist.jsonc".to_string();
```

Uncomment the one you want to use.

### Changing the Song Duration

Edit `src/main.rs` around line 254:

```rust
let mut resulthnote = HNote {
    start_time: 0.0,
    end_time: 30.0,  // Change this (in seconds)
    timing: 1.0,
    // ...
};
```

### Viewing the Output

After running, check `tree_output.txt` to see the complete hierarchical structure with timing:

```
[0.00 - 30.00 0]
├── [0.00 - 7.50 0]
│   ├── [0.00 - 0.47 43]
│   ├── [0.47 - 0.91 43]
│   └── ...
```

- Numbers in brackets: `[start_time - end_time midi_number]`
- `p` prefix = prechild (e.g., `p[1.35 - 1.83 36]`)

---

## Examples

### Example 1: Simple Layering

**Goal:** Hi-hats with kick/snare for 4 measures

```json
[
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]}
]
```

### Example 2: Adding a Fill

**Goal:** 3 normal measures + 1 with a fill

```json
[
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {
      "target": 1,
      "function": "injectprechildren",
      "path": [3],
      "prechild_library_target": 0
    }
  ]}
]
```

### Example 3: Surgical Injection at Root

**Goal:** Add prechildren to an entire measure (not just one note)

```json
{
  "target": 1,
  "function": "injectprechildren",
  "path": [],
  "prechild_library_target": 0
}
```

---

## Tips and Best Practices

### Organizing Your Measures

1. **Index 0**: Hi-hat or other continuous pattern
2. **Index 1**: Basic kick/snare groove
3. **Index 2+**: Variations and alternatives

### Creating Prechildren Templates

1. **Keep them focused**: One template = one type of embellishment
2. **Use descriptive MIDI numbers**: Make it clear what sound you're adding
3. **Test anchor settings**: Try both `anchor_end: true` and `false` to see which sounds better

### Debugging

1. **Check `tree_output.txt`**: See exact timing of every note
2. **Look for `p` markers**: Verify prechildren are where you expect
3. **Simplify**: If something sounds wrong, try a simpler call list first

### Performance Tips

1. **Reuse measures**: Don't create 10 copies of the same hi-hat pattern
2. **Use Combine wisely**: Sidebyside for layering, sequential for sections
3. **InjectPrechildren over duplication**: Inject fills instead of creating measure variants

### Common Patterns

**Intro → Verse → Chorus → Outro:**
```json
[
  // Intro: Just hi-hats
  {"target": 0, "function": "twice"},

  // Verse: Hi-hats + kick/snare
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "once"}
  ]},

  // Chorus: Add a fill
  {"function": "combine", "direction": "sidebyside", "calls": [
    {"target": 0, "function": "once"},
    {"target": 1, "function": "injectprechildren", "path": [0], "prechild_library_target": 2}
  ]}
]
```

---

## Troubleshooting

### "Failed to load initial calls"

**Problem:** JSON syntax error in call list

**Solution:** Check for:
- Missing commas
- Unclosed brackets
- Function names must be lowercase: `"injectprechildren"` not `"inject_prechildren"`

### "Index out of bounds"

**Problem:** Referenced a measure or library entry that doesn't exist

**Solution:**
- Check `target` values are valid (0-based indexing)
- Check `prechild_library_target` is valid
- Count your array entries in the JSON files

### Prechildren not appearing

**Problem:** Path navigation failed or anchor settings incorrect

**Solution:**
- Verify `path` is correct (use `tree_output.txt` to see structure)
- Check that `anchor_prechild` is 1-indexed and within bounds
- Ensure library entry has `prechildren` array

### Timing sounds wrong

**Problem:** `timing_based_on_children` or anchor settings incorrect

**Solution:**
- Try toggling `timing_based_on_children`
- Try both `anchor_end: true` and `false`
- Check that timing shares add up logically

---

## Quick Reference Card

```
FILES:
  measures.json          → Base patterns
  prechildren_library.json    → Embellishments
  calllist.jsonc            → Song composition
  tree_output.txt                → Generated timing visualization

FUNCTIONS:
  once          → Copy measure once
  twice         → Copy measure twice
  combine       → Layer or sequence multiple calls
  injectprechildren → Add embellishments at specific locations

DIRECTIONS:
  sequential    → One after another
  sidebyside    → Simultaneous

PATHS:
  []            → Root of measure
  [0]           → First child
  [2, 1]        → Second child of third child

ANCHORS:
  anchor_prechild: 2      → Second prechild is anchor (1-indexed)
  anchor_end: true        → Anchor to parent's end
  anchor_end: false       → Anchor to parent's start
  timing_based_on_children: true   → Scale with children
  timing_based_on_children: false  → Scale with parent

RUNNING:
  cargo run                    → Build and run
  Edit main.rs line 237        → Change call list
  Edit main.rs line 257        → Change duration
  Check tree_output.txt        → View results
```

---

## Next Steps

1. **Experiment**: Try modifying the existing call lists
2. **Create new patterns**: Add your own measures to `measures.json`
3. **Build a library**: Create a collection of fills in `prechildren_library.json`
4. **Compose**: Use InjectPrechildren to create dynamic, varied drum patterns

Happy composing! 🥁
