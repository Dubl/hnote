# Fresh song generator: N beats + the short-roll arc, with everything learned
# from song 1 baked in — per-beat seeded kits, multi-instrument walkers with
# no-three-in-a-row, uneven timing shares, short rolls (~2 sixteenths at the
# bar end), roll 2 spilling past the bar line, roll 3 playing over the base.
#
# Usage: python generate_song.py <song> [nbeats] [seed]
# Writes measures.<song>.json and calllist.<song>.browse.jsonc
# (4 bars per beat: rolls 1-4 = buzz / spiller / over-base stab / build).

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

def make_beat(name, rng):
    aux = rng.sample(COLORS, rng.choice([2, 2, 3]))
    # lane A: kick/snare (rolled)
    cells = []
    for i in range(BAR_SHARES_A):
        beat16 = i // 2
        if i % 8 == 0:                                   # downbeat-ish kicks
            cells.append(leaf(36, rng.randint(95, 110), 0.5))
        elif beat16 in (4, 12) and i % 2 == 0:           # backbeat snares
            cells.append(leaf(38, rng.randint(98, 112), 0.5))
        elif rng.random() < 0.16:
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
    # lane B: hats, irregular density
    cells = []
    for i in range(BAR_SHARES_H):
        r = rng.random()
        if r < 0.52:
            p = 46 if rng.random() < 0.07 else 42
            cells.append(leaf(p, rng.randint(44, 72), 0.5))
        else:
            cells.append(rest(0.5))
    laneB = cont(cells)
    # aux lanes
    def aux_lane(inst, dens):
        cells = []
        for i in range(BAR_SHARES_X):
            if rng.random() < dens:
                cells.append(leaf(inst, rng.randint(55, 85), 0.0625))
            else:
                cells.append(rest(0.0625))
        return cont(cells)
    lanes = [laneA, laneB, aux_lane(aux[0], 0.22)]
    if len(aux) > 2 or rng.random() < 0.5:
        lanes.append(aux_lane(aux[1], 0.13))
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

def make_roll(name, kind, aux, rng, spill=False, over=False):
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
        pcs.append(cont(leaves, 0.0625) if hits > 1 else
                   {**leaves[0], "timing": 0.0625})
    pcs.append(rest(0.0625))                              # anchor (slot 6)
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
        pcs.append(cont(cells, 2 / 16.0))
        pcs.append(rest(0.5 / 16.0))
        m["ancestor_overwrite_level"] = 2
        m["end_of_silence_prechild"] = 8
    return m

def main():
    song = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260710
    measures = []
    calls = []
    kinds = [("buzz", False, False), ("tumble", True, False),
             ("over", False, True), ("build", False, False)]
    for i in range(1, n + 1):
        rng = random.Random(seed ^ (i * 0x9e3779b1))
        beat, aux = make_beat(f"{song}b{i}", rng)
        measures.append(beat)
        for j, (kind, spill, over) in enumerate(kinds, 1):
            measures.append(make_roll(f"{song}r{i}_{j}", kind, aux, rng,
                                      spill=spill, over=over))
            calls.append({"target": f"{song}b{i}", "function": "once",
                          "then": {"function": "roll",
                                   "target": f"{song}r{i}_{j}", "amount": 1}})
    json.dump(measures, open(f"measures.{song}.json", "w", encoding="utf-8"), indent=1)
    json.dump(calls, open(f"calllist.{song}.browse.jsonc", "w", encoding="utf-8"), indent=1)
    print(f"{song}: {n} beats, {n*4} rolls, {len(calls)} bars ({len(calls)*4.0:.0f}s)")

if __name__ == "__main__":
    main()
