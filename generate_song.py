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

def make_beat(name, rng, barsecs=4, style="base"):
    scale = barsecs / 4
    drive = style == "drive"
    vary = style == "vary"
    aux = rng.sample(COLORS, rng.choice([2, 2, 3]))
    ghost_p = 0.30 if drive else 0.16
    # lane A: kick/snare (rolled)
    cells = []
    n_a = int(BAR_SHARES_A * scale)
    if vary:                                # per-beat structural identity
        kt = rng.choice(list(KICK_TEMPLATES))
        st = rng.choice(list(SNARE_TEMPLATES))
        kicks = set(KICK_TEMPLATES[kt](n_a))
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
    for i in range(n_a):
        if i in kicks:
            cells.append(leaf(36, rng.randint(102, 115) if drive else rng.randint(95, 110), 0.5))
        elif i in snares:
            cells.append(leaf(snares[i], rng.randint(105, 118) if drive else rng.randint(98, 112), 0.5))
        elif i in syncs:                                 # hard syncopated accents
            p = 36 if rng.random() < 0.6 else 38
            cells.append(leaf(p, rng.randint(96, 112), 0.5))
        elif rng.random() < ghost_p:
            p = 36 if rng.random() < 0.55 else 38
            v = rng.randint(40, 70) if p == 38 else rng.randint(70, 95)
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
        accent = rng.choice([3, 4, 6])
    else:
        vehicle, dens, accent = 42, (0.86 if drive else 0.52), 4
    cells = []
    for i in range(int(BAR_SHARES_H * scale)):
        r = rng.random()
        if r < dens:
            p = 46 if (vehicle == 42 and rng.random() < 0.05) else vehicle
            if drive or vary:
                v = rng.randint(68, 84) if i % accent == 0 else rng.randint(46, 62)
            else:
                v = rng.randint(44, 72)
            cells.append(leaf(p, v, 0.5))
        else:
            cells.append(rest(0.5))
    laneB = cont(cells)
    if vary and rng.random() < 0.30:        # swing: uneven 32nd pairs, 16th grid intact
        sw = rng.uniform(1.10, 1.25)
        for lane_cells in (cells,):
            for k in range(0, len(lane_cells) - 1, 2):
                lane_cells[k]["timing"] = 0.5 * sw
                lane_cells[k+1]["timing"] = 0.5 * (2 - sw)
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
