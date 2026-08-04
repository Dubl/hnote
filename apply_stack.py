# Compile a stack.html blob into a real HNote measure, render, and verify the
# realized sequence exactly. The stack is pure numbers: motif + periods
# (outermost first), each level = [child x k, cut(child)] built with the
# trim + proportional-share primitive. Element children (restart phase) are
# sub-loops inside one pulse cell, cut at the slot's tick count.
#
# v2 additions: LANES (a tab = chord of stacks, lane 1 = the ruler; other
# lanes tile and are CUT at lane 1's bar -> sidebyside root, the canonical
# HNote beat shape), signed symbols (negative = ghost, vel 52), top-level
# rests (symbol 0), per-lane phase, variable pulse.
#
# Usage: python apply_stack.py "<blob>" [--name stack1]
# Blobs: hnote stack v1 pulse=0.25 periods=[16,8] motif=[1,2,3] child2=[S=2,m=[4,5]]
#        hnote stack v2 pulse=0.11 lane1={periods=[16] motif=[3,0]} lane2={...}

import json, math, re, struct, subprocess, sys

SOUNDS = [36, 38, 42, 46, 75, 49, 40, 35]   # K S H O V C N B(sub)
GHOST_VEL = 52

def leaf(m, v, t=1.0):
    return {"midi_number": m, "velocity": v, "timing": t, "channel": 9, "children": None}
def cont(children, t=1.0):
    return {"midi_number": 0, "velocity": 0, "timing": t, "channel": 9,
            "child_direction": "sequential", "children": children}

def fold(t, periods, mlen, offs=None, steps=None, b=0):
    # each level may carry an offset INTO the level below: x = x%P + o,
    # and the offset may STEP per bar: o(b) = o + b*step
    for k, P in enumerate(periods):
        o = (offs[k] if offs and k < len(offs) else 0) or 0
        d = (steps[k] if steps and k < len(steps) else 0) or 0
        t = t % P + o + b * d
    return t % mlen

def cycle_of(periods, mlen, steps):
    """Bars until the stepping offsets return home."""
    C = 1
    for k in range(len(periods)):
        span = periods[k + 1] if k + 1 < len(periods) else mlen
        d = ((steps[k] if steps and k < len(steps) else 0) or 0) % span
        if d:
            C = C * (span // math.gcd(d, span)) // math.gcd(C, span // math.gcd(d, span))
    return C

def realize(pulse, periods, motif, children, phase=0, offs=None, steps=None, b=0):
    top = periods[0] if periods else len(motif)
    ph = phase % top
    hits = []
    for t in range(top):
        mi = fold(t, periods, len(motif), offs, steps, b)
        ch = children.get(mi)
        base = ((t - ph) % top) * pulse          # phase = pulse the loop starts on
        accent = 116 if t == 0 else (102 if mi == 0 else 88)
        if ch:
            sub = pulse / ch["S"]
            pre = ch.get("pre", 0) % ch["S"]
            N = max(ch["S"], len(ch["m"]))       # extra notes SPILL past the cell
            for j in range(N):
                sym = ch["m"][(j + ch.get("p", 0)) % len(ch["m"])]
                if not sym:
                    continue                     # 0 = rest
                vel = GHOST_VEL if sym < 0 else (accent if j == pre else max(52, accent - 26))
                at = (base + (j - pre) * sub) % (top * pulse)   # wrap both directions
                hits.append((at, SOUNDS[abs(sym) - 1], vel))
        else:
            sym = motif[mi]
            if not sym:
                continue                         # 0 = rest at the top level too
            hits.append((base, SOUNDS[abs(sym) - 1], GHOST_VEL if sym < 0 else accent))
    return hits, top

def lane_cycle(ln):
    periods, motif, children, phase, offs, steps = ln
    return cycle_of(periods, len(motif), steps)

def tab_cycle(lanes):
    C = 1
    for ln in lanes:
        c = lane_cycle(ln)
        C = C * c // math.gcd(C, c)
    return C

def realize_tab(pulse, lanes):
    """lanes: [(periods, motif, children, phase, offs, steps), ...];
    lane 0 is the ruler. Stepping offsets -> the loop is the full cycle."""
    top0 = lanes[0][0][0] if lanes[0][0] else len(lanes[0][1])
    C = tab_cycle(lanes)
    bar = top0 * pulse
    out = []
    for b in range(C):
        base = b * bar
        h0, _ = realize(pulse, *lanes[0], b=b)
        out += [(base + t, p, v) for t, p, v in h0]
        for ln in lanes[1:]:
            h, t = realize(pulse, *ln, b=b)
            lb = t * pulse
            bb = 0.0
            while bb < bar - 1e-9:               # tile, cut at the ruler's bar
                for (tt, p, v) in h:
                    if bb + tt < bar - 1e-9:
                        out.append((base + bb + tt, p, v))
                bb += lb
    return out, top0 * C

def build_lane(pulse, periods, motif, children, phase=0, offs=None):
    """Nested tree for one lane: motif node -> wrap in each period (inside-out)."""
    def motif_cell(mi, vel):
        ch = children.get(mi)
        if not ch:
            sym = motif[mi]
            if not sym:
                return leaf(0, 0, 1.0)           # explicit rest cell
            return leaf(SOUNDS[abs(sym) - 1], GHOST_VEL if sym < 0 else vel, 1.0)
        kids = []
        pre = ch.get("pre", 0) % ch["S"]
        N = max(ch["S"], len(ch["m"]))
        for k in range(ch["S"]):
            j = k + pre                          # out-of-cell ticks ride the overflow lanes
            if j >= N:
                kids.append(leaf(0, 0, 1.0)); continue
            sym = ch["m"][(j + ch.get("p", 0)) % len(ch["m"])]
            if sym:
                v = GHOST_VEL if sym < 0 else (vel if j == pre else max(52, vel - 26))
                kids.append(leaf(SOUNDS[abs(sym) - 1], v, 1.0))
            else:
                kids.append(leaf(0, 0, 1.0))     # 0 = explicit rest cell
        return cont(kids, 1.0)

    def replace_first_cell(n, cell):
        kids = n["children"]
        k = kids[0]
        if k.get("children") is None or k["timing"] == 1.0:
            kids[0] = cell
        else:
            replace_first_cell(k, cell)

    unit_seq = list(range(len(motif)))
    node = cont([motif_cell(mi, 102 if mi == 0 else 88) for mi in unit_seq],
                float(len(unit_seq)))
    span = len(unit_seq)
    for k in range(len(periods) - 1, -1, -1):     # wrap inside-out
        P = periods[k]
        o = ((offs[k] if offs and k < len(offs) else 0) or 0) % span
        base = node if not o else cont([drop_unit(node, o), trim_unit(node, o)], float(span))
        reps, rem = divmod(P, span)
        kids = [json.loads(json.dumps(base)) for _ in range(reps)]
        if rem:
            kids.append(trim_unit(base, rem))
        node = cont(kids, float(P))
        span = P
    # bar-start accent: patch the t=0 cell (its motif index depends on offsets)
    replace_first_cell(node, motif_cell(fold(0, periods, len(motif), offs), 116))
    ph = phase % span
    if ph:  # rotate: start on pulse ph -> [tail (span-ph pulses), head (ph pulses)]
        node = cont([drop_unit(node, ph), trim_unit(node, ph)], float(span))
    return node, span

def build_overflow_bars(pulse, periods, motif, children, phase=0, offs=None):
    """Out-of-cell sub-motif ticks (prenotes backward, spillover forward) as
    parallel overflow lanes. Each source cell's ticks are grouped by target
    pulse; groups are packed greedily into as few lanes as collisions allow.
    Returns (list of lane nodes, span) - list may be empty."""
    top = periods[0] if periods else len(motif)
    ph = phase % top
    lanes = []                                   # each: dict target-pulse -> cell node
    for t in range(top):
        mi = fold(t, periods, len(motif), offs)
        ch = children.get(mi)
        if not ch:
            continue
        S = ch["S"]
        pre = ch.get("pre", 0) % S
        N = max(S, len(ch["m"]))
        pos = (t - ph) % top
        accent = 116 if t == 0 else (102 if mi == 0 else 88)
        groups = {}                              # pulse offset -> {slot: leaf}
        for j in range(N):
            rel = j - pre
            if 0 <= rel < S:
                continue                         # in-cell: handled by motif_cell
            sym = ch["m"][(j + ch.get("p", 0)) % len(ch["m"])]
            if not sym:
                continue
            v = GHOST_VEL if sym < 0 else max(52, accent - 26)
            groups.setdefault(rel // S, {})[rel % S] = leaf(SOUNDS[abs(sym) - 1], v, 1.0)
        for off, slots in groups.items():
            q = (pos + off) % top
            kids = [slots.get(k, leaf(0, 0, 1.0)) for k in range(S)]
            cell = cont(kids, 1.0)
            for lane in lanes:                   # greedy packing
                if q not in lane:
                    lane[q] = cell
                    break
            else:
                lanes.append({q: cell})
    nodes = [cont([lane.get(q, leaf(0, 0, 1.0)) for q in range(top)], float(top))
             for lane in lanes]
    return nodes, top

def fit_to(node, own_span, span_target):
    """Tile/cut a lane node so it spans exactly span_target pulses."""
    if own_span == span_target:
        return json.loads(json.dumps(node))
    reps, rem = divmod(span_target, own_span)
    kids = [json.loads(json.dumps(node)) for _ in range(reps)]
    if rem:
        kids.append(trim_unit(node, rem))
    return cont(kids, float(span_target))

def build_measure(name, pulse, lanes):
    """lanes -> sidebyside root with one sequential lane node each (the
    canonical HNote beat shape). Lane 0 is the ruler. Stepping offsets
    unroll: C bar-trees per lane, each built with that bar's offsets."""
    top0 = lanes[0][0][0] if lanes[0][0] else len(lanes[0][1])
    C = tab_cycle(lanes)
    kids = []
    for ln in lanes:
        periods, motif, children, phase, offs, steps = ln
        bars, over_bars = [], []
        for b in range(C):
            offs_b = [((offs[k] if offs and k < len(offs) else 0) or 0)
                      + b * ((steps[k] if steps and k < len(steps) else 0) or 0)
                      for k in range(len(periods))]
            node, span = build_lane(pulse, periods, motif, children, phase, offs_b)
            bars.append(fit_to(node, span, top0))
            onodes, ospan = build_overflow_bars(pulse, periods, motif, children, phase, offs_b)
            over_bars.append([fit_to(n, ospan, top0) for n in onodes])
        lane_node = bars[0] if C == 1 else cont(bars, float(C * top0))
        lane_node["timing"] = 1.0
        kids.append(lane_node)
        M = max((len(x) for x in over_bars), default=0)
        for mi_ in range(M):                      # overflow lanes (prenotes + spillover)
            def rest_bar():
                return cont([leaf(0, 0, 1.0) for _ in range(top0)], float(top0))
            bars_m = [over_bars[b][mi_] if mi_ < len(over_bars[b]) else rest_bar()
                      for b in range(C)]
            gl = bars_m[0] if C == 1 else cont(bars_m, float(C * top0))
            gl["timing"] = 1.0
            kids.append(gl)
    root = {"midi_number": 0, "velocity": 0, "timing": float(C * top0 * pulse), "channel": 9,
            "child_direction": "sidebyside", "children": kids,
            "start_time": 0.0, "end_time": 0.0, "name": name}
    return root, C * top0

def drop_unit(node, pulses):
    """Deep-copy node with its first `pulses` pulses removed (integer shares)."""
    node = json.loads(json.dumps(node))
    kids = node["children"]
    span = 0
    out = []
    left = pulses
    for k in kids:
        kspan = 1
        if k.get("children") and k["timing"] != 1.0:
            kspan = int(round(k["timing"]))
        span += kspan
        if left <= 0:
            out.append(k)
        elif kspan <= left:
            left -= kspan                       # drop whole child
        else:
            out.append(drop_unit(k, left)); left = 0
    node["children"] = out
    node["timing"] = float(span - pulses)
    return node

def trim_unit(node, pulses):
    """Deep-copy node truncated to its first `pulses` pulses (integer shares)."""
    node = json.loads(json.dumps(node))
    kids = node["children"]
    out = []
    left = pulses
    for k in kids:
        kspan = int(round(k["timing"])) if k.get("children") else 1
        if k.get("children") and k["timing"] == 1.0:
            kspan = 1                                  # element-child cell spans 1 pulse
        elif k.get("children"):
            kspan = int(round(k["timing"]))
        if left <= 0: break
        if kspan <= left:
            out.append(k); left -= kspan
        else:
            out.append(trim_unit(k, left)); left = 0
    node["children"] = out
    node["timing"] = float(pulses)
    return node

def parse_mid(path):
    d = open(path, "rb").read(); ppq = struct.unpack(">H", d[12:14])[0]
    i = d.index(b"MTrk") + 8; end = i + struct.unpack(">I", d[i-4:i])[0]
    t = 0; tempo = 500000; on = []; run = None
    while i < end:
        dv = 0
        while True:
            b = d[i]; i += 1; dv = (dv << 7) | (b & 0x7f)
            if not b & 0x80: break
        t += dv; b = d[i]
        if b == 0xFF:
            mt = d[i+1]; ln = d[i+2]
            if mt == 0x51: tempo = int.from_bytes(d[i+3:i+3+ln], "big")
            i += 3 + ln; run = None
        elif b in (0xF0, 0xF7): i += 2 + d[i+1]; run = None
        else:
            if b & 0x80: st = b; i += 1; run = st
            else: st = run
            if st & 0xF0 in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                d1, d2 = d[i], d[i+1]; i += 2
                if st & 0xF0 == 0x90 and d2 > 0: on.append((t*tempo/ppq/1e6, d1, d2))
            else: i += 1
    return on

def parse_lane(body):
    periods, offs, steps = [], [], []
    for tok in re.search(r"periods=\[([\d@+,]*)\]", body).group(1).split(","):
        if not tok: continue
        m = re.match(r"(\d+)(?:@(\d+))?(?:\+(\d+))?$", tok)
        periods.append(int(m.group(1))); offs.append(int(m.group(2) or 0))
        steps.append(int(m.group(3) or 0))
    motif = [int(x) for x in re.search(r"motif=\[([-\d,]+)\]", body).group(1).split(",")]
    children = {}
    for m in re.finditer(r"child(\d+)=\[S=(\d+),m=\[([-\d,]+)\](?:,p=(\d+))?(?:,pre=(\d+))?\]", body):
        children[int(m.group(1)) - 1] = {"S": int(m.group(2)),
                                         "m": [int(x) for x in m.group(3).split(",")],
                                         "p": int(m.group(4) or 0),
                                         "pre": int(m.group(5) or 0)}
    phm = re.search(r"phase=(\d+)", body)
    return (periods, motif, children, int(phm.group(1)) if phm else 0, offs, steps)

def parse_blob(blob, tab="A"):
    s = blob.strip()
    if s.startswith("hnote setup") or s.startswith("{"):
        # full-page setup blob (Copy setup): compile one tab from the state JSON
        state = json.loads(s[s.find("{"):])
        t = state["stacks"]["ABCDEFGH".index(tab)]
        def lane_tuple(l):
            ch = {int(k): v for k, v in (l.get("children") or {}).items()}
            return (l.get("periods") or [], l["motif"], ch, l.get("phase", 0) or 0,
                    l.get("offs") or [], l.get("steps") or [])
        lanes = [lane_tuple(t)] + [lane_tuple(x) for x in (t.get("lanes") or [])]
        return float(state.get("pulse", 0.25)), lanes
    pulse = float(re.search(r"pulse=([\d.]+)", blob).group(1))
    lane_bodies = re.findall(r"lane\d+=\{([^{}]*)\}", blob)
    lanes = [parse_lane(b) for b in lane_bodies] if lane_bodies else [parse_lane(blob)]
    return pulse, lanes

def main():
    blob = sys.argv[1]
    name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "stack1"
    tab = sys.argv[sys.argv.index("--tab") + 1] if "--tab" in sys.argv else "A"
    pulse, lanes = parse_blob(blob, tab)
    print(f"{name}: pulse {pulse}, {len(lanes)} lane(s)")
    for i, (periods, motif, children, phase, offs, steps) in enumerate(lanes):
        print(f"  lane{i+1}: periods {periods}, offs {offs}, steps {steps}, "
              f"motif {motif}, children {children}, phase {phase}")

    measure, top = build_measure(name, pulse, lanes)
    calls = [{"target": name, "function": "once"}] * 4
    json.dump([measure], open(f"measures.{name}.json", "w", encoding="utf-8"), indent=1)
    json.dump(calls, open(f"calllist.{name}.jsonc", "w", encoding="utf-8"), indent=1)
    dur = top * pulse * 4
    r = subprocess.run([sys.executable, "build_track.py", name, f"calllist.{name}.jsonc",
                        "--measures", f"measures.{name}.json", "--no-melody",
                        "--duration", str(dur)], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(r.stdout[-600:] + r.stderr[-600:])
    print(r.stdout.strip().splitlines()[-1])

    pred, _ = realize_tab(pulse, lanes)
    on = parse_mid(f"{name}.mid")
    barlen = top * pulse
    ok = 0
    for bar in range(4):
        got = sorted((t - bar*barlen, p, v) for t, p, v in on
                     if bar*barlen - 0.003 <= t < (bar+1)*barlen - 0.003)
        want = sorted(pred)
        pool = list(got); good = len(got) == len(want)
        if good:
            for tt, pp, vv in want:
                m = [j for j, (t2, p2, v2) in enumerate(pool)
                     if p2 == pp and v2 == vv and abs(t2-tt) <= 0.0025]
                if not m: good = False; break
                pool.pop(m[0])
        ok += good
    print(f"verification: {ok}/4 bars match the realized tab exactly (times+pitches+velocities)")
    if ok < 4: raise SystemExit(1)

if __name__ == "__main__":
    main()
