# Shared machinery for the note-level timing editor.
#
# Replicates the engine's layout math (types.rs) in Python for one bar:
#   - sequential children: normalized shares (layout_children_sequentially_in_range)
#   - sidebyside children: each spans the parent
#   - roll prechildren: anchor_end layout (anchor slot STARTS at bar end)
#   - erasure window: [pc[0].start, pc[eos-1].start), whitelist passes through
#
# The editing primitive: onset k of a sequential container is the boundary
# between siblings k-1 and k. `share[k-1] += d; share[k] -= d` moves only that
# boundary (total is unchanged). Delaying a first child inserts a leading rest
# with share d instead. Moving a first child earlier is pinned in v1.

import json

BAR = 4.0

def is_sounding(n):
    if n.get("midi_number"): return True
    return any(is_sounding(c) for c in (n.get("children") or []))

def _walk(node, start, end, path, out):
    """Collect sounding leaves with onsets and container context."""
    if node.get("midi_number"):
        out.append({"path": path, "onset": start, "end": end,
                    "midi": node["midi_number"], "vel": node.get("velocity", 0)})
    kids = node.get("children") or []
    if not kids:
        return
    if node.get("child_direction") == "sidebyside":
        for i, c in enumerate(kids):
            _walk(c, start, end, path + [("c", i)], out)
    else:  # sequential (default)
        total = sum(c.get("timing", 0.0) for c in kids)
        if total <= 0:
            return
        cur = start
        for i, c in enumerate(kids):
            if i < len(kids) - 1:
                seg = (end - start) * c.get("timing", 0.0) / total
                cend = cur + seg
            else:
                cend = end  # last child soaks the remainder
            _walk(c, cur, cend, path + [("c", i)], out)
            cur = cend

def beat_hits(measure, bar_start=0.0):
    out = []
    _walk(measure, bar_start, bar_start + BAR, [], out)
    return out

def roll_layout(roll, bar_start=0.0):
    """Lay out a roll measure's prechildren as applied to a bar (anchor_end).
    Returns (hits, slot_starts, window) where window = [silence_start, silence_end)."""
    pcs = roll.get("prechildren") or []
    anchor_idx = 6 - 1                                  # Call::Roll hardcodes 6
    bar_end = bar_start + BAR
    durations = [pc.get("timing", 0.0) * BAR for pc in pcs]
    starts = [0.0] * len(pcs)
    total_before = sum(durations[:anchor_idx])
    off = bar_end - total_before
    for i in range(anchor_idx):
        starts[i] = off; off += durations[i]
    starts[anchor_idx] = bar_end
    off = bar_end + durations[anchor_idx]
    for i in range(anchor_idx + 1, len(pcs)):
        starts[i] = off; off += durations[i]
    hits = []
    for i, pc in enumerate(pcs):
        sub = []
        _walk(pc, starts[i], starts[i] + durations[i], [("p", i)], sub)
        hits.extend(sub)
    eos = roll.get("end_of_silence_prechild") or 6
    idx = min(eos - 1, len(pcs) - 1)
    window = (starts[0], starts[idx])
    return hits, starts, window

def container_at(measure, path):
    """Return (container_node, key, index) for the leaf at path: the leaf is
    container[key][index] where key is 'children' or 'prechildren'."""
    node = measure
    for arm, i in path[:-1]:
        node = (node["prechildren"] if arm == "p" else node["children"])[i]
    arm, i = path[-1]
    key = "prechildren" if arm == "p" else "children"
    return node, key, i

def container_children_spans(measure, cpath, bar_span=BAR, bar_start=0.0):
    """Absolute (start,end) of every child of the sequential container at cpath."""
    node = measure
    start, end = bar_start, bar_start + bar_span
    for arm, i in cpath:
        if arm == "p":
            pcs = node["prechildren"]
            durations = [pc.get("timing", 0.0) * bar_span for pc in pcs]
            anchor_idx = 6 - 1
            starts = [0.0] * len(pcs)
            total_before = sum(durations[:anchor_idx])
            off = (bar_start + bar_span) - total_before
            for j in range(anchor_idx):
                starts[j] = off; off += durations[j]
            starts[anchor_idx] = bar_start + bar_span
            off = starts[anchor_idx] + durations[anchor_idx]
            for j in range(anchor_idx + 1, len(pcs)):
                starts[j] = off; off += durations[j]
            start, end = starts[i], starts[i] + durations[i]
            node = pcs[i]
        else:
            kids = node["children"]
            if node.get("child_direction") == "sidebyside":
                node = kids[i]
            else:
                total = sum(c.get("timing", 0.0) for c in kids)
                cur = start
                for j, c in enumerate(kids):
                    seg = (end - start) * c.get("timing", 0.0) / total
                    cend = end if j == len(kids) - 1 else cur + seg
                    if j == i:
                        start, end = cur, cend
                        break
                    cur = cend
                node = kids[i]
    kids = node["children"]
    total = sum(c.get("timing", 0.0) for c in kids)
    spans = []
    cur = start
    for j, c in enumerate(kids):
        seg = (end - start) * c.get("timing", 0.0) / (total if total > 0 else 1)
        cend = end if j == len(kids) - 1 else cur + seg
        spans.append((cur, cend))
        cur = cend
    return spans

def shift_onset(measure, path, dt, bar_span=BAR):
    """Apply a compensating share transfer so the leaf at `path` moves by dt
    seconds (positive = later). Container span in seconds must be supplied via
    the recomputed layout; here we recompute from the measure itself."""
    node, key, k = container_at(measure, path)
    kids = node[key]
    if key == "prechildren":
        raise ValueError("direct prechild-slot shifts are out of scope (window edges)")
    total = sum(c.get("timing", 0.0) for c in kids)
    span = _container_span(measure, path[:-1], bar_span)
    if span <= 0 or total <= 0:
        raise ValueError("degenerate container")
    d = dt / span * total
    if k == 0:
        if d < 0:
            raise ValueError("first-child onset cannot move earlier (pinned)")
        rest = {"midi_number": 0, "velocity": 0, "timing": d, "channel": 9, "children": None}
        if kids[0].get("timing", 0.0) - d <= 1e-9:
            raise ValueError("delay exceeds first child's span")
        kids[0]["timing"] = kids[0].get("timing", 0.0) - d
        kids.insert(0, rest)
    else:
        if d > 0 and kids[k].get("timing", 0.0) - d <= 1e-9:
            raise ValueError("delay exceeds hit's own span")
        if d < 0 and kids[k-1].get("timing", 0.0) + d <= 1e-9:
            raise ValueError("advance exceeds previous sibling's span")
        kids[k-1]["timing"] = kids[k-1].get("timing", 0.0) + d
        kids[k]["timing"] = kids[k].get("timing", 0.0) - d

def _container_span(measure, cpath, bar_span):
    """Absolute span in seconds of the container at cpath, for a bar of bar_span."""
    # walk down replicating layout spans
    node = measure; start, end = 0.0, bar_span
    for arm, i in cpath:
        if arm == "p":
            pcs = node["prechildren"]
            durations = [pc.get("timing", 0.0) * bar_span for pc in pcs]
            anchor_idx = 6 - 1
            starts = [0.0] * len(pcs)
            total_before = sum(durations[:anchor_idx])
            off = bar_span - total_before
            for j in range(anchor_idx):
                starts[j] = off; off += durations[j]
            starts[anchor_idx] = bar_span
            off = bar_span + durations[anchor_idx]
            for j in range(anchor_idx + 1, len(pcs)):
                starts[j] = off; off += durations[j]
            start, end = starts[i], starts[i] + durations[i]
            node = pcs[i]
        else:
            kids = node["children"]
            if node.get("child_direction") == "sidebyside":
                node = kids[i]  # spans parent unchanged
            else:
                total = sum(c.get("timing", 0.0) for c in kids)
                cur = start
                for j, c in enumerate(kids):
                    seg = (end - start) * c.get("timing", 0.0) / total
                    cend = end if j == len(kids) - 1 else cur + seg
                    if j == i:
                        start, end = cur, cend
                        break
                    cur = cend
                node = kids[i]
    return end - start

def path_str(path):
    return "/".join(f"{a}{i}" for a, i in path)

def parse_path(s):
    return [(seg[0], int(seg[1:])) for seg in s.split("/")]

# --- loop crop/extend --------------------------------------------------------
# The loop length c is share mass: content occupying [0, c) of a virtual loop
# is renormalized over the bar, so every onset scales by bar/c. c < bar crops
# (stretch, hits later); c > bar pads a trailing rest (compress, hits earlier).
# Crop is ABSOLUTE, not cumulative: the sidecar (crops.json) stashes each
# beat's pristine lanes on first crop and every crop restarts from them.

import copy

CROPS_SIDECAR = "crops.json"

def load_sidecar(path=CROPS_SIDECAR):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}

def save_sidecar(sc, path=CROPS_SIDECAR):
    json.dump(sc, open(path, "w", encoding="utf-8"), indent=1)

def crop_loop(measure, c, sidecar, bar_span=BAR):
    """Set the beat's loop length to c seconds (absolute). Restores pristine
    lanes from the sidecar first, so repeated crops don't compound."""
    name = measure["name"]
    if name not in sidecar:
        sidecar[name] = {"orig_children": copy.deepcopy(measure["children"]), "c": bar_span}
    measure["children"] = copy.deepcopy(sidecar[name]["orig_children"])
    sidecar[name]["c"] = c
    if abs(c - bar_span) < 1e-9:
        return
    if not (0.5 * bar_span <= c <= 1.5 * bar_span):
        raise ValueError(f"crop {c} out of sane range")
    for lane in measure["children"]:
        kids = lane.get("children") or []
        if not kids:
            continue
        total = sum(k.get("timing", 0.0) for k in kids)
        target = total * c / bar_span
        if c > bar_span:
            kids.append({"midi_number": 0, "velocity": 0,
                         "timing": total * (c - bar_span) / bar_span,
                         "channel": 9, "children": None, "name": "loopcrop"})
            continue
        acc = 0.0
        cut = None
        for i, k in enumerate(kids):
            t = k.get("timing", 0.0)
            if acc + t > target + 1e-12:
                keep = target - acc
                if keep > 1e-9:
                    k["timing"] = keep       # straddling cell: trim its tail
                    cut = i + 1
                else:
                    cut = i
                break
            acc += t
        if cut is not None:
            del kids[cut:]

def mute_roll(roll, sidecar):
    """Silence a roll entirely: no notes, no erasure. Reversible via sidecar."""
    name = roll["name"]
    if name not in sidecar:
        sidecar[name] = {"orig_prechildren": copy.deepcopy(roll.get("prechildren")),
                         "orig_whitelist": copy.deepcopy(roll.get("overwrite_whitelist"))}
    sidecar[name]["muted"] = True
    def zero(n):
        n["midi_number"] = 0
        n["velocity"] = 0
        for c in (n.get("children") or []): zero(c)
    for pc in (roll.get("prechildren") or []): zero(pc)
    roll["overwrite_whitelist"] = list(range(35, 82))   # erasure becomes a no-op

def unmute_roll(roll, sidecar):
    name = roll["name"]
    if name not in sidecar or "orig_prechildren" not in sidecar[name]:
        return                                           # never muted
    roll["prechildren"] = copy.deepcopy(sidecar[name]["orig_prechildren"])
    roll["overwrite_whitelist"] = copy.deepcopy(sidecar[name]["orig_whitelist"])
    sidecar[name]["muted"] = False

def roll_muted(sidecar, roll_name):
    return bool(sidecar.get(roll_name, {}).get("muted"))

def bar_windows(byname, beat_name, bar):
    """Erasure windows applying to base hits of this bar, as
    [(lo, hi, whitelist_set)] in bar-local seconds. Own roll's window, plus
    the previous bar's roll-2 forward reach when bar == 3."""
    roll = byname[f"rroll{beat_name[5:]}_{bar}"]
    _, _, (lo, hi) = roll_layout(roll)
    wins = [(lo, hi, set(roll.get("overwrite_whitelist") or []))]
    if bar == 3:
        r2 = byname[f"rroll{beat_name[5:]}_2"]
        _, _, (l2, h2) = roll_layout(r2)
        if h2 > BAR:                       # spills forward into this bar
            wins.append((0.0, h2 - BAR, set(r2.get("overwrite_whitelist") or [])))
    return wins
