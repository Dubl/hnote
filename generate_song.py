# Fresh song generator: N beats + the short-roll arc, with everything learned
# from song 1 baked in — per-beat seeded kits, multi-instrument walkers with
# no-three-in-a-row, uneven timing shares, short rolls (~2 sixteenths at the
# bar end), roll 2 spilling past the bar line, roll 3 playing over the base.
#
# Usage: python generate_song.py <song> [nbeats] [seed] [barsecs] [bars_per_beat]
# Writes measures.<song>.json and calllist.<song>.browse.jsonc.
# barsecs: loop length in seconds (4 or 8; same 0.125s cell grid either way -
# 8s doubles the cell count, and roll bar-fractions halve so rolls keep the
# same absolute size). bars_per_beat: 4 = full roll arc (buzz/spiller/over/
# build), 2 = plain bar + spiller bar (compact browse).

import json, random, sys

BAR_SHARES_A = 32      # kick/snare lane: 32nd-grid cells
BAR_SHARES_H = 32      # hat lane
BAR_SHARES_X = 16      # aux lanes: 16th cells
COLORS = [51, 53, 54, 56, 60, 61, 62, 63, 64, 70, 75, 76, 77, 37, 39]
TOMS = [41, 43, 45]

def leaf(m, v, t=1.0):
    return {"midi_number": m, "velocity": v, "timing": t, "channel": 9, "children": None}
def cont(children, t=1.0, direction="sequential"):
    return {"midi_number": 0, "velocity": 0, "timing": t, "channel": 9,
            "child_direction": direction, "children": children}
def rest(t=1.0):
    return leaf(0, 0, t)

KICK_TEMPLATES = {
    "steady":  lambda n: [i for i in range(n) if i % 8 == 0],
    "broken":  lambda n: [i for i in range(n) if i % 32 in (0, 12, 24)],
    "push":    lambda n: [i for i in range(n) if i % 16 in (0, 6)],
    "half":    lambda n: [i for i in range(n) if i % 32 == 0],
}
SNARE_TEMPLATES = {
    "classic":   lambda n: [(i, 38) for i in range(n) if i % 16 == 8],
    "half":      lambda n: [(i, 38) for i in range(n) if i % 32 == 16],
    "displaced": lambda n: [(i, 38) for i in range(n) if i % 32 in (8, 26)],
    "clap":      lambda n: [(i, 38) for i in range(n) if i % 32 == 8]
                         + [(i, 39) for i in range(n) if i % 32 == 24],
}

WILD_FEATURES = ["poly", "oddaccent", "burst", "drunk", "dropout", "invert", "chaoskick"]

def make_beat(name, rng, barsecs=4, style="base"):
    scale = barsecs / 4
    drive = style == "drive"
    vary = style in ("vary", "wild")
    wild = style == "wild"
    feats = set(rng.sample(WILD_FEATURES, rng.randint(2, 4))) if wild else set()
    aux = rng.sample(COLORS, rng.choice([2, 2, 3]))
    ghost_p = 0.30 if drive else 0.16
    # lane A: kick/snare (rolled)
    cells = []
    n_a = int(BAR_SHARES_A * scale)
    if vary:                                # per-beat structural identity
        pool = list(KICK_TEMPLATES) + (["chaos"] if "chaoskick" in feats else [])
        kt = rng.choice(pool)
        st = rng.choice(list(SNARE_TEMPLATES))
        kicks = (set(rng.sample(range(n_a), rng.randint(5, 9))) if kt == "chaos"
                 else set(KICK_TEMPLATES[kt](n_a)))
        if kicks and rng.random() < 0.5:    # jitter: drop or add one
            if rng.random() < 0.5 and len(kicks) > 2:
                kicks.discard(rng.choice(sorted(kicks)[1:]))
            else:
                kicks.add(rng.choice([i for i in range(n_a) if i % 4 == 2]))
        snares = dict(SNARE_TEMPLATES[st](n_a))
    else:
        kicks = set(i for i in range(n_a) if i % 8 == 0)
        snares = {i: 38 for i in range(n_a) if (i // 2) % 8 == 4 and i % 2 == 0}
    syncs = set(rng.sample([i for i in range(n_a) if i % 8 in (3, 6)],
                           rng.randint(2, 4) if drive else 0))
    # dynamic inversion: one half of the loop turns inside-out
    inv_lo, inv_hi = (n_a // 2, n_a) if ("invert" in feats and rng.random() < 0.5) else (0, n_a // 2)
    invert = "invert" in feats
    def vel(base_lo, base_hi, i, ghost=False):
        v = rng.randint(base_lo, base_hi)
        if invert and inv_lo <= i < inv_hi:
            v = rng.randint(85, 100) if ghost else rng.randint(45, 60)
        return v
    # dropouts: holes where kick/snare AND ride vanish together
    drop = set()
    if "dropout" in feats:
        for _ in range(rng.randint(1, 2)):
            start = rng.randrange(4, n_a - 8)
            drop.update(range(start, start + rng.randint(4, 8)))
    burst_p = rng.uniform(0.04, 0.08) if "burst" in feats else 0.0
    def maybe_burst(cell_leaf):
        if rng.random() < burst_p and cell_leaf.get("midi_number"):
            p, v = cell_leaf["midi_number"], cell_leaf["velocity"]
            k = rng.choice([2, 3])
            sh = [float(rng.choice([1, 1, 2])) for _ in range(k)]
            return cont([leaf(p, max(30, v - 12 * (k - 1 - h)), sh[h]) for h in range(k)], 0.5)
        return cell_leaf
    for i in range(n_a):
        if i in drop:
            cells.append(rest(0.5))
        elif i in kicks:
            cells.append(maybe_burst(leaf(36, vel(102, 115, i) if drive else vel(95, 110, i), 0.5)))
        elif i in snares:
            cells.append(maybe_burst(leaf(snares[i], vel(105, 118, i) if drive else vel(98, 112, i), 0.5)))
        elif i in syncs:                                 # hard syncopated accents
            p = 36 if rng.random() < 0.6 else 38
            cells.append(leaf(p, vel(96, 112, i), 0.5))
        elif rng.random() < ghost_p:
            p = 36 if rng.random() < 0.55 else 38
            v = vel(40, 70, i, ghost=True) if p == 38 else vel(70, 95, i, ghost=True)
            if rng.random() < 0.12:                      # uneven drag pair
                sh = rng.choice([[1, 2], [1, 3], [2, 1]])
                cells.append(cont([leaf(p, v - 18, float(sh[0])),
                                   leaf(p, v, float(sh[1]))], 0.5))
            else:
                cells.append(leaf(p, v, 0.5))
        else:
            cells.append(rest(0.5))
    laneA = cont(cells)
    laneA["rolled"] = True
    # lane B: the ride layer - per-beat vehicle, density, accent period
    if vary:
        vehicle = rng.choices([42, 51, 70], weights=[5, 3, 2])[0]
        dens = rng.uniform(0.62, 0.88)
        accent = rng.choice([3, 4, 5, 6, 7] if "oddaccent" in feats else [3, 4, 6])
    else:
        vehicle, dens, accent = 42, (0.86 if drive else 0.52), 4
    cells = []
    for i in range(int(BAR_SHARES_H * scale)):
        r = rng.random()
        if i in drop:
            cells.append(rest(0.5))
        elif r < dens:
            p = 46 if (vehicle == 42 and rng.random() < 0.05) else vehicle
            if drive or vary:
                v = rng.randint(68, 84) if i % accent == 0 else rng.randint(46, 62)
            else:
                v = rng.randint(44, 72)
            cells.append(maybe_burst(leaf(p, v, 0.5)) if wild else leaf(p, v, 0.5))
        else:
            cells.append(rest(0.5))
    laneB = cont(cells)
    if vary and rng.random() < 0.30:        # swing: uneven 32nd pairs, 16th grid intact
        sw = rng.uniform(1.10, 1.25)
        for lane_cells in (cells,):
            for k in range(0, len(lane_cells) - 1, 2):
                lane_cells[k]["timing"] = 0.5 * sw
                lane_cells[k+1]["timing"] = 0.5 * (2 - sw)
    if "drunk" in feats:                    # smear the ride layer's grid
        j = rng.uniform(0.10, 0.22)
        for c in cells:
            c["timing"] = c.get("timing", 0.5) * rng.uniform(1 - j, 1 + j)
    # aux lanes
    def aux_lane(inst, dens):
        cells = []
        for i in range(int(BAR_SHARES_X * scale)):
            if rng.random() < dens:
                cells.append(leaf(inst, rng.randint(55, 85), 0.0625))
            else:
                cells.append(rest(0.0625))
        return cont(cells)
    lanes = [laneA, laneB, aux_lane(aux[0], 0.22)]
    if len(aux) > 2 or rng.random() < 0.5:
        lanes.append(aux_lane(aux[1], 0.13))
    if "drunk" in feats:                    # smear aux lanes too
        for lane in lanes[2:]:
            j = rng.uniform(0.10, 0.22)
            for c in lane["children"]:
                c["timing"] = c.get("timing", 0.0625) * rng.uniform(1 - j, 1 + j)
    if "poly" in feats:
        # a voice hitting every P cells, P coprime-ish to the loop: phases
        # across the 8s and only re-syncs at the loop point
        P = rng.choice([5, 6, 7, 10])
        n_p = int(BAR_SHARES_A * scale)
        voice = rng.choice([x for x in COLORS if x not in aux])
        cells = []
        for i in range(n_p):
            if i % P == 0:
                cells.append(leaf(voice, rng.randint(58, 86), 0.5))
            else:
                cells.append(rest(0.5))
        lanes.append(cont(cells))
    if vary:
        # signature figure: a short motif on a distinctive voice, repeated in
        # both halves of the loop at the same position - per-beat identity
        n_f = int(BAR_SHARES_A * scale)
        cells = [rest(0.5) for _ in range(n_f)]
        voice = rng.choice(aux)
        pos0 = rng.choice([10, 14, 20, 26])
        motif = [(k * rng.choice([1, 2]), rng.randint(62, 88)) for k in range(rng.randint(2, 3))]
        for half in (0, n_f // 2):
            for off, v in motif:
                idx = half + pos0 + off
                if idx < n_f: cells[idx] = leaf(voice, v, 0.5)
        lanes.append(cont(cells))
    if drive or vary:
        # quiet fills: 1-2 soft tom runs tucked into pockets of the loop
        n_f = int(BAR_SHARES_A * scale)
        cells = [rest(0.5) for _ in range(n_f)]
        for _ in range(rng.randint(1, 2)):
            start = rng.choice([x for x in range(6, n_f - 8) if x % 8 in (5, 6, 7)])
            pos = rng.choice([2, 1])
            for k in range(rng.randint(3, 6)):
                pos = max(0, min(2, pos + rng.choice([-1, -1, 0, 1])))
                cells[start + k] = leaf(TOMS[pos], rng.randint(34, 55), 0.5)
        lanes.append(cont(cells))
    return {"midi_number": 0, "velocity": 0, "timing": 1.0, "channel": 9,
            "child_direction": "sidebyside", "children": lanes,
            "start_time": 0.0, "end_time": 0.0, "name": name}, aux

# --- tree style: the hierarchy IS the rhythm ---------------------------------
# Each beat is a nested ratio tree (no grid): the loop divides by a funky
# share vocabulary, segments divide again, 3-4 levels deep. Voices speak
# depths: kick=1, snare=2 (preferring onsets off the kicks), ride=3,
# ghosts=4. Swing = a lean applied at any interior node, at that node's scale.
TOP_RATIOS = [[3, 3, 2], [3, 3, 2], [2, 2], [3, 1], [2, 1, 1], [1, 2, 1], [2, 3]]
MID_RATIOS = [[1, 1], [2, 1], [1, 2], [1, 1, 1], [1, 1, 1], [2, 1, 1], [1, 1, 2], [3, 1]]

def build_ratio_tree(rng, depth_left, lean_p):
    if depth_left == 0:
        return None
    shares = [float(x) for x in rng.choice(MID_RATIOS if depth_left < 3 else TOP_RATIOS)]
    if rng.random() < lean_p:                       # swing at THIS node's scale
        shares[0] *= rng.uniform(1.08, 1.30)
    kids = [build_ratio_tree(rng, depth_left - 1, lean_p) for _ in shares]
    return {"shares": shares, "kids": kids}

def emit_lane(tree, target_depth, sound_fn, depth=1):
    """Realize the ratio tree as an HNote lane where only depth==target nodes
    sound. sound_fn(depth_index, is_downbeat_child) -> leaf or rest."""
    out = []
    for ci, (sh, kid) in enumerate(zip(tree["shares"], tree["kids"])):
        if depth == target_depth or kid is None:
            out.append({**sound_fn(ci == 0), "timing": sh})
        else:
            inner = emit_lane(kid, target_depth, sound_fn, depth + 1)
            out.append(cont(inner, sh))
    return out

def make_tree_beat(name, rng, barsecs=8):
    aux = rng.sample(COLORS, rng.choice([2, 3]))
    depth = rng.choice([4, 4, 5])
    tree = build_ratio_tree(rng, depth, lean_p=0.25)
    vehicle = rng.choices([42, 51, 70], weights=[5, 3, 2])[0]

    def kick_fn(first):
        if first or rng.random() < 0.55:
            return leaf(36, rng.randint(96, 112))
        return rest()
    def snare_fn(first):
        # prefer NOT landing with the kicks: sound mostly on non-first children
        if (not first and rng.random() < 0.55) or (first and rng.random() < 0.10):
            return leaf(38 if rng.random() < 0.8 else 37, rng.randint(70, 108))
        return rest()
    def ride_fn(first):
        if rng.random() < 0.85:
            v = rng.randint(66, 84) if first else rng.randint(46, 64)
            return leaf(vehicle, v)
        return rest()
    def ghost_fn(first):
        if rng.random() < 0.42:
            return leaf(rng.choice(aux), rng.randint(38, 62))
        return rest()

    lanes = [cont(emit_lane(tree, 1, kick_fn)),
             cont(emit_lane(tree, 2, snare_fn)),
             cont(emit_lane(tree, depth - 1, ride_fn))]
    if rng.random() < 0.7:
        lanes.append(cont(emit_lane(tree, depth, ghost_fn)))
    lanes[0]["rolled"] = True
    return {"midi_number": 0, "velocity": 0, "timing": 1.0, "channel": 9,
            "child_direction": "sidebyside", "children": lanes,
            "start_time": 0.0, "end_time": 0.0, "name": name}, aux

# --- groove style: unequal groupings of EQUAL pulses -------------------------
# The historical shape of unconventional-but-funky rhythm (aksak, clave):
# the loop holds N equal pulses (N can be odd-ball: 18, 20...), the tree's top
# partitions them into groups of 2s/3s/4s (kick on group starts, snare inside
# groups off the starts), the ride plays the pulse itself accented by the
# grouping, and BELOW the pulse the tree stays free (leans, ghost flurries).
# Half 2 of the loop repeats half 1 with one mutated group: call & response.

def partition_pulses(rng, total):
    groups = []
    left = total
    while left > 0:
        g = rng.choice([2, 3, 3, 2, 4] if left >= 4 else ([left] if left <= 3 else [2]))
        g = min(g, left)
        groups.append(g)
        left -= g
    return groups

def make_half_score(rng, groups):
    score = []
    for g in groups:
        pulses = []
        for k in range(g):
            snare = None
            if k > 0 and rng.random() < 0.38:
                snare = rng.randint(96, 112) if rng.random() < 0.45 else rng.randint(52, 76)
            ghost = rng.random() < 0.30
            pulses.append({"snare": snare, "ghost": ghost})
        # pulse shares within the group (swing lean, shared by ALL lanes)
        shares = [1.0] * g
        if rng.random() < 0.30 and g >= 2:
            lean = rng.uniform(1.08, 1.22)
            for k in range(0, g - 1, 2):
                shares[k] = lean; shares[k + 1] = 2 - lean
        score.append({"size": g, "pulses": pulses, "shares": shares,
                      "kick": rng.random() > 0.15})
    score[0]["kick"] = True
    return score

def make_groove_beat(name, rng, barsecs=8):
    aux = rng.sample(COLORS, rng.choice([2, 3]))
    N = rng.choices([32, 24, 20, 16, 18], weights=[4, 3, 2, 1, 1])[0]
    half = N // 2
    groups = partition_pulses(rng, half)
    score1 = make_half_score(rng, groups)
    # half 2 = half 1 with ONE group mutated (content redraw; sometimes resize
    # two adjacent groups, preserving the pulse total)
    import copy as _c
    score2 = _c.deepcopy(score1)
    gi = rng.randrange(len(score2))
    if rng.random() < 0.5 and len(score2) >= 2:
        gj = (gi + 1) % len(score2)
        tot = score2[gi]["size"] + score2[gj]["size"]
        a = rng.randint(max(2, tot - 4), min(4, tot - 2)) if tot >= 4 else score2[gi]["size"]
        score2[gi] = make_half_score(rng, [a])[0]
        score2[gj] = make_half_score(rng, [tot - a])[0]
    else:
        score2[gi] = make_half_score(rng, [score2[gi]["size"]])[0]
    vehicle = rng.choices([42, 51, 70], weights=[5, 3, 2])[0]

    def emit(voice_fn):
        halves = []
        for score in (score1, score2):
            gconts = []
            for grp in score:
                cells = []
                for k in range(grp["size"]):
                    cells.append({**voice_fn(grp, k), "timing": grp["shares"][k]})
                gconts.append(cont(cells, float(grp["size"])))
            halves.append(cont(gconts, 1.0))
        return cont(halves)

    def kick_fn(grp, k):
        if k == 0 and grp["kick"]:
            return leaf(36, rng.randint(98, 114))
        return rest()
    def snare_fn(grp, k):
        v = grp["pulses"][k]["snare"]
        return leaf(38 if (v or 0) > 90 or rng.random() < 0.8 else 37, v) if v else rest()
    def ride_fn(grp, k):
        v = rng.randint(70, 86) if k == 0 else rng.randint(48, 64)
        return leaf(vehicle, v)
    def ghost_fn(grp, k):
        if grp["pulses"][k]["ghost"]:
            n = rng.choice([2, 3])
            sh = [float(rng.choice([1, 1, 2])) for _ in range(n)]
            kids = [leaf(rng.choice(aux), rng.randint(36, 60), sh[j]) if rng.random() < 0.6
                    else rest(sh[j]) for j in range(n)]
            return cont(kids)
        return rest()

    lanes = [emit(kick_fn), emit(snare_fn), emit(ride_fn), emit(ghost_fn)]
    lanes[0]["rolled"] = True
    return {"midi_number": 0, "velocity": 0, "timing": 1.0, "channel": 9,
            "child_direction": "sidebyside", "children": lanes,
            "start_time": 0.0, "end_time": 0.0, "name": name}, aux

def walker(kind, aux, rng):
    recent = []
    home = {"buzz": 38, "over": rng.choice([36, 41, 43]),
            "build": rng.choice([38, 38, 45, 43, 36])}.get(kind, 38)
    pos = [rng.choice([1, 2])]
    def wp(prog):
        if kind == "tumble":
            if rng.random() < 0.3: pos[0] = max(0, min(2, pos[0] + rng.choice([-1, 1])))
            else: pos[0] = max(0, min(2, pos[0] - 1))
            p = TOMS[pos[0]]
            r = rng.random()
            if r < 0.10 and aux: p = rng.choice(aux)
            elif r < 0.18: p = 38
        else:
            p_home = {"buzz": 0.30 + 0.55 * prog, "over": 0.5,
                      "build": 0.25 + 0.65 * prog}[kind]
            if rng.random() < p_home: p = home
            else:
                r = rng.random()
                if r < 0.35: p = rng.choice(TOMS)
                elif r < 0.55: p = 37
                elif r < 0.72: p = 36 if home != 36 else 41
                elif r < 0.85: p = 39
                else: p = rng.choice(aux) if aux else 38
        if len(recent) >= 2 and recent[-1] == recent[-2] == p:
            p = rng.choice([x for x in TOMS + [38] if x != p])
        recent.append(p)
        return p
    return wp

def make_roll(name, kind, aux, rng, spill=False, over=False, barsecs=4):
    f = 4 / barsecs        # bar-fraction scale: rolls keep absolute size
    wp = walker(kind, aux, rng)
    pcs = [rest(0.0), rest(0.0), rest(0.0)]
    for si in range(2):                                   # two sounding slots
        prog = si / 1.0
        hits = rng.choice([1, 2, 2, 3])
        shares = [float(rng.choice([1, 1, 2, 3])) for _ in range(hits)]
        v0, v1 = 70, 112
        leaves = [leaf(wp(prog), max(30, min(118,
                    int(v0 + (v1 - v0) * (si + h / hits) / 2) + rng.randint(-6, 6))),
                    shares[h]) for h in range(hits)]
        pcs.append(cont(leaves, 0.0625 * f) if hits > 1 else
                   {**leaves[0], "timing": 0.0625 * f})
    pcs.append(rest(0.0625 * f))                          # anchor (slot 6)
    m = {"midi_number": 0, "velocity": 0, "timing": 1.0, "channel": 9,
         "child_direction": "sequential", "children": None, "prechildren": pcs,
         "start_time": 0.0, "end_time": 0.0, "name": name,
         "overwrite_whitelist": list(range(35, 82)) if over else [42, 46]}
    if spill:
        cells = []
        for ci in range(2):
            decay = ci / 2
            pair = rng.random() < 0.55
            ll = [leaf(wp(1.0 - decay), max(30, min(105,
                     int(84 - 40 * decay) + rng.randint(-5, 5))),
                     float(rng.choice([1, 1, 2]))) for _ in range(2 if pair else 1)]
            cells.append(cont(ll) if pair else ll[0])
        pcs.append(cont(cells, 2 / 16.0 * f))
        pcs.append(rest(0.5 / 16.0 * f))
        m["ancestor_overwrite_level"] = 2
        m["end_of_silence_prechild"] = 8
    return m

def main():
    song = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260710
    barsecs = float(sys.argv[4]) if len(sys.argv) > 4 else 4
    bars_per_beat = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    style = sys.argv[6] if len(sys.argv) > 6 else "base"
    measures = []
    calls = []
    kinds = [("buzz", False, False), ("tumble", True, False),
             ("over", False, True), ("build", False, False)]
    for i in range(1, n + 1):
        rng = random.Random(seed ^ (i * 0x9e3779b1))
        if style == "tree":
            beat, aux = make_tree_beat(f"{song}b{i}", rng, barsecs)
        elif style == "groove":
            beat, aux = make_groove_beat(f"{song}b{i}", rng, barsecs)
        else:
            beat, aux = make_beat(f"{song}b{i}", rng, barsecs, style)
        measures.append(beat)
        for j, (kind, spill, over) in enumerate(kinds, 1):
            measures.append(make_roll(f"{song}r{i}_{j}", kind, aux, rng,
                                      spill=spill, over=over, barsecs=barsecs))
        if bars_per_beat == 2:
            calls.append({"target": f"{song}b{i}", "function": "once"})
            calls.append({"target": f"{song}b{i}", "function": "once",
                          "then": {"function": "roll",
                                   "target": f"{song}r{i}_2", "amount": 1}})
        else:
            for j in range(1, 5):
                calls.append({"target": f"{song}b{i}", "function": "once",
                              "then": {"function": "roll",
                                       "target": f"{song}r{i}_{j}", "amount": 1}})
    json.dump(measures, open(f"measures.{song}.json", "w", encoding="utf-8"), indent=1)
    json.dump(calls, open(f"calllist.{song}.browse.jsonc", "w", encoding="utf-8"), indent=1)
    print(f"{song}: {n} beats, {n*4} rolls, {len(calls)} bars ({len(calls)*4.0:.0f}s)")

if __name__ == "__main__":
    main()
