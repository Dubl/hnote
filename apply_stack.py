# Compile a stack.html blob into a real HNote measure, render, and verify the
# realized sequence exactly. The stack is pure numbers: motif + periods
# (outermost first), each level = [child x k, cut(child)] built with the
# trim + proportional-share primitive. Element children (restart phase) are
# sub-loops inside one pulse cell, cut at the slot's tick count.
#
# Usage: python apply_stack.py "<blob>" [--name stack1]
# Blob:  hnote stack v1 pulse=0.25 periods=[16,8] motif=[1,2,3] child2=[S=2,m=[4,5]]

import json, re, struct, subprocess, sys

SOUNDS = [36, 38, 42, 56, 75]

def leaf(m, v, t=1.0):
    return {"midi_number": m, "velocity": v, "timing": t, "channel": 9, "children": None}
def cont(children, t=1.0):
    return {"midi_number": 0, "velocity": 0, "timing": t, "channel": 9,
            "child_direction": "sequential", "children": children}

def fold(t, periods, mlen):
    for P in periods: t %= P
    return t % mlen

def realize(pulse, periods, motif, children):
    top = periods[0] if periods else len(motif)
    hits = []
    for t in range(top):
        mi = fold(t, periods, len(motif))
        ch = children.get(mi)
        base = t * pulse
        accent = 116 if t == 0 else (102 if mi == 0 else 88)
        if ch:
            sub = pulse / ch["S"]
            for j in range(ch["S"]):
                sym = ch["m"][j % len(ch["m"])]
                hits.append((base + j * sub, SOUNDS[sym - 1], accent if j == 0 else max(52, accent - 26)))
        else:
            hits.append((base, SOUNDS[motif[mi] - 1], accent))
    return hits, top

def build_measure(name, pulse, periods, motif, children):
    """Nested tree: motif node -> wrap in each period (inside-out), trimming."""
    def motif_cell(mi, vel):
        ch = children.get(mi)
        if not ch:
            return leaf(SOUNDS[motif[mi] - 1], vel, 1.0)
        kids = [leaf(SOUNDS[ch["m"][j % len(ch["m"])] - 1],
                     vel if j == 0 else max(52, vel - 26), 1.0)
                for j in range(ch["S"])]
        return cont(kids, 1.0)

    def make_unit(pulses_list):
        """A sequence of motif indices -> node with share = pulse count."""
        return cont([motif_cell(mi, 96) for mi in pulses_list], float(len(pulses_list)))

    # innermost unit = motif
    unit_seq = list(range(len(motif)))               # motif indices per pulse
    node = make_unit(unit_seq)
    span = len(unit_seq)
    for P in reversed(periods):                       # wrap inside-out
        reps, rem = divmod(P, span)
        kids = [json.loads(json.dumps(node)) for _ in range(reps)]
        if rem:
            cut_seq = [fold(t, [], span) for t in range(rem)]   # t mod span within unit
            # trim: realize the unit's first `rem` pulses by refolding through
            # the unit's own structure (the unit spans `span` pulses of known
            # motif indices - recompute them)
            kids.append(trim_unit(node, rem))
        node = cont(kids, float(P))
        span = P
    node["name"] = name
    root = {"midi_number": 0, "velocity": 0, "timing": float(span * pulse), "channel": 9,
            "child_direction": "sidebyside", "children": [node],
            "start_time": 0.0, "end_time": 0.0, "name": name}
    # the lane holding everything must be a plain child list under sidebyside root
    node["timing"] = 1.0
    return root, span

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
                if st & 0xF0 == 0x90 and d2 > 0: on.append((t*tempo/ppq/1e6, d1))
            else: i += 1
    return on

def main():
    blob = sys.argv[1]
    name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "stack1"
    pulse = float(re.search(r"pulse=([\d.]+)", blob).group(1))
    periods = [int(x) for x in re.search(r"periods=\[([\d,]*)\]", blob).group(1).split(",") if x]
    motif = [int(x) for x in re.search(r"motif=\[([\d,]+)\]", blob).group(1).split(",")]
    children = {}
    for m in re.finditer(r"child(\d+)=\[S=(\d+),m=\[([\d,]+)\]\]", blob):
        children[int(m.group(1)) - 1] = {"S": int(m.group(2)),
                                         "m": [int(x) for x in m.group(3).split(",")]}
    print(f"{name}: periods {periods}, motif {motif}, children {children}")

    measure, top = build_measure(name, pulse, periods, motif, children)
    calls = [{"target": name, "function": "once"}] * 4
    json.dump([measure], open(f"measures.{name}.json", "w", encoding="utf-8"), indent=1)
    json.dump(calls, open(f"calllist.{name}.jsonc", "w", encoding="utf-8"), indent=1)
    dur = top * pulse * 4
    r = subprocess.run([sys.executable, "build_track.py", name, f"calllist.{name}.jsonc",
                        "--measures", f"measures.{name}.json", "--no-melody",
                        "--duration", str(dur)], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(r.stdout[-600:] + r.stderr[-600:])
    print(r.stdout.strip().splitlines()[-1])

    pred, _ = realize(pulse, periods, motif, children)
    on = parse_mid(f"{name}.mid")
    barlen = top * pulse
    ok = 0
    for bar in range(4):
        got = sorted((t - bar*barlen, p) for t, p in on
                     if bar*barlen - 0.003 <= t < (bar+1)*barlen - 0.003)
        want = sorted((t, p) for t, p, v in pred)
        pool = list(got); good = len(got) == len(want)
        if good:
            for tt, pp in want:
                m = [j for j, (t2, p2) in enumerate(pool) if p2 == pp and abs(t2-tt) <= 0.0025]
                if not m: good = False; break
                pool.pop(m[0])
        ok += good
    print(f"verification: {ok}/4 bars match the realized stack exactly")
    if ok < 4: raise SystemExit(1)

if __name__ == "__main__":
    main()
