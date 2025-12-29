# Nested Calls Guide

## Overview

The `Combine` call variant allows you to nest and group calls with directional control (sequential or sidebyside), creating an abstraction layer between primitive measures and your final composition.

## Basic Usage

### Simple Sequential Combination

```json
[
  {
    "function": "combine",
    "direction": "sequential",
    "calls": [
      {"target": 0, "function": "once"},
      {"target": 1, "function": "once"},
      {"target": 2, "function": "once"}
    ]
  }
]
```

This creates a wrapper HNote with `child_direction: "sequential"` containing measures 0, 1, and 2 in sequence.

### Side-by-Side Combination

```json
[
  {
    "function": "combine",
    "direction": "sidebyside",
    "calls": [
      {"target": 0, "function": "once"},
      {"target": 1, "function": "once"}
    ]
  }
]
```

This plays measures 0 and 1 simultaneously (like kick drum + hi-hat layers).

## Advanced Usage

### Nested Combinations

You can nest `combine` calls recursively:

```json
[
  {
    "function": "combine",
    "direction": "sequential",
    "calls": [
      {
        "function": "combine",
        "direction": "sidebyside",
        "calls": [
          {"target": 0, "function": "once"},
          {"target": 1, "function": "once"}
        ]
      },
      {"target": 2, "function": "once"}
    ]
  }
]
```

This creates a structure where:
1. Measures 0 and 1 play side-by-side
2. Then measure 2 plays after them

### Chaining with `then`

Like other calls, `combine` supports the `then` parameter:

```json
[
  {
    "function": "combine",
    "direction": "sequential",
    "calls": [
      {"target": 0, "function": "once"},
      {"target": 1, "function": "once"}
    ],
    "then": {
      "target": 1,
      "function": "roll",
      "amount": 2
    }
  }
]
```

### Mixing with Existing Calls

You can mix `combine` with existing `once`, `twice`, and `roll` calls:

```json
[
  {"target": 0, "function": "once"},
  {
    "function": "combine",
    "direction": "sequential",
    "calls": [
      {"target": 1, "function": "once"},
      {"target": 2, "function": "once"}
    ]
  },
  {"target": 3, "function": "once"}
]
```

## How It Works

The `Combine` variant creates a wrapper HNote with:
- `midi_number`: 0 (silent)
- `child_direction`: as specified (sequential or sidebyside)
- `children`: populated from the nested calls
- `timing`: 1.0 (can be adjusted based on children)

Each nested call is processed independently and added as a child of the wrapper.

## Future Enhancements

This foundation enables future features like:
- Named patterns (e.g., `"pattern": "verse"`)
- Parameterized patterns (e.g., pattern templates with variables)
- Pattern libraries loaded from external files

## Example Test File

See `my_calllist_nested_test.jsonc` for a working example.
