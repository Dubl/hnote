# Apply a splice.html blob: build the composite measure (host + guest windows,
# ALIGNED slices - the guest's own [a,b) material appears at [a,b)), fource it,
# render, and verify segment-by-segment against measures.polytest.json layout.
#
# Usage: python apply_splice.py "<blob>" [--name spliced1]
# Blob: hnote splice v1 host=ptest3(4:5) guest=ptest10(5:9) windows=[1.2,3.4);[5,6.2)

import json, re, struct, subprocess, sys, os

BAR = 8.0
EPS = 0.005

def leaf(m, v, t=1.0):
    return {"midi_number": m, "velocity": v, "timing": t, "channel": 9, "children": None}
def cont(children, t=1.0, d="sequential"):
    return {"midi_number": 0, "velocity": 0, "timing": t, "channel": 9,
            "child_direction": d, "children": children}
def rest(t=1.0): return leaf(0, 0, t)

def walk(n, start, end, out):
    if n.get("midi_number"): out.append((start, n["midi_number"], n.get("velocity", 0)))
    kids = n.get("children") or []
    if not kids: return
    if n.get("child_direction") == "sidebyside":
        for c in kids: walk(c, start, end, out)
    else:
        tot = sum(c.get("timing", 0.0) for c in kids)
        cur = start
        for j, c in enumerate(kids):
            ce = end if j == len(kids) - 1 else cur + (end - start) * c.get("timing", 0.0) / tot
            walk(c, cur, ce, out)
            cur = ce

def slice_lanes(byname, src, t0, t1):
    w = t1 - t0
    hits = []
    walk(byname[src], 0.0, BAR, hits)
    hits = [(t - t0, p, v) for t, p, v in hits if p and t0 - 1e-9 <= t < t1 - 0.004]
    voices = {}
    for t, p, v in sorted(hits): voices.setdefault(p, []).append((t, v))
    lanes = []
    for p, evs in voices.items():
        cells = []; prev = 0.0
        for t, v in evs:
            if t - prev > 1e-6: cells.append(rest(t - prev))
            cells.append(leaf(p, v, 0.02)); prev = t + 0.02
        if w - prev > 1e-6: cells.append(rest(w - prev))
        lanes.append(cont(cells))
    return cont(lanes, d="sidebyside") if lanes else cont([rest(1.0)], d="sidebyside")

def main():
    blob = sys.argv[1]
    name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "spliced1"
    m = re.search(r"host=(\w+)\([\d:]+\) guest=(\w+)\([\d:]+\) windows=(.+)", blob)
    host, guest = m.group(1), m.group(2)
    wins = [(float(a), float(b)) for a, b in re.findall(r"\[([\d.]+),([\d.]+)\)", m.group(3))]
    wins.sort()
    print(f"{name}: host {host}, guest {guest}, windows {wins}")

    data = json.load(open("measures.polytest.json", encoding="utf-8"))
    byname = {mm.get("name"): mm for mm in data}
    # covering window [wins[0][0]-EPS, wins[-1][1]-EPS); content alternates
    # guest slices (aligned) and host re-supply in the gaps
    W0, W1 = wins[0][0] - EPS, wins[-1][1] - EPS
    segs = []          # (src, t0, t1) in absolute measure time
    cur = W0
    for a, b in wins:
        if a - cur > 0.01: segs.append((host, cur, a))
        segs.append((guest, a, min(b, W1)))
        cur = b
    if W1 - cur > 0.01: segs.append((host, cur, W1))
    content = cont([{**slice_lanes(byname, s, t0, t1), "timing": (t1 - t0)}
                    for s, t0, t1 in segs], t=(W1 - W0) / BAR)
    hostm = json.loads(json.dumps(byname[host]))
    hostm["children"][0]["rolled"] = True
    hostm["name"] = f"{name}_host"
    sp = {"midi_number": 0, "velocity": 0, "timing": 1.0, "channel": 9,
          "child_direction": "sequential", "children": None,
          "prechildren": [content, rest((BAR - W1) / BAR), rest(0.0), rest(0.0),
                          rest(0.0), rest(0.0)],
          "start_time": 0.0, "end_time": 0.0, "name": f"{name}_sp",
          "end_of_silence_prechild": 2, "overwrite_whitelist": []}
    measures = data + [hostm, sp]
    calls = [{"target": f"{name}_host", "function": "once",
              "then": {"function": "roll", "target": f"{name}_sp", "amount": 1}}] * 4
    json.dump(measures, open(f"measures.{name}.json", "w", encoding="utf-8"), indent=1)
    json.dump(calls, open(f"calllist.{name}.jsonc", "w", encoding="utf-8"), indent=1)

    r = subprocess.run([sys.executable, "build_track.py", name, f"calllist.{name}.jsonc",
                        "--measures", f"measures.{name}.json", "--no-melody",
                        "--duration", "32"], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(r.stdout[-500:] + r.stderr[-500:])
    print(r.stdout.strip().splitlines()[-1])

    # verify: predicted = host outside wins + guest inside wins (aligned)
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
    on = parse_mid(f"{name}.mid")
    hh = []; walk(byname[host], 0.0, BAR, hh)
    gh = []; walk(byname[guest], 0.0, BAR, gh)
    def inwin(t): return any(a - EPS - 1e-9 <= t < b - EPS for a, b in wins)
    pred = sorted([(t, p) for t, p, v in hh if p and not inwin(t)] +
                  [(t, p) for t, p, v in gh if p and inwin(t)])
    scale = 1.0  # aligned slices at their own positions; sub-slices keep absolute time
    ok = 0
    for bar in range(4):
        got = sorted((t - bar*BAR, p) for t, p in on if bar*BAR - 0.003 <= t < (bar+1)*BAR - 0.003)
        pool = list(got); good = len(got) == len(pred)
        if good:
            for tt, pp in pred:
                mm2 = [j for j, (t2, p2) in enumerate(pool) if p2 == pp and abs(t2-tt) <= 0.03]
                if not mm2: good = False; break
                pool.pop(mm2[0])
        ok += good
    print(f"verification: {ok}/4 bars match host-outside + guest-inside prediction")
    if ok < 4: raise SystemExit(1)

if __name__ == "__main__":
    main()
