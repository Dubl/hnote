# Export the 7 cutoff uberloops (drums + phase-resetting bass) as
# perform_data.js for perform.html, verifying against cutoff.mid en route.
# Usage: python make_perform_data.py

import json, struct

PULSE = 0.25
V = {1: 36, 2: 38, 3: 42, 4: 56, 5: 75}

def sn(motif, runs, keep, m):
    one = []
    for r in range(runs):
        one += motif if r < runs - 1 else motif[:keep]
    return one * m

SPECS = [
    ("cut1", "(123 123 12) x2", sn([1,2,3],3,2,2), 28),
    ("cut2", "(1234 1234 123) x2", sn([1,2,3,4],3,3,2), 31),
    ("cut3", "(12 12 12 1) x2", sn([1,2],4,1,2), 33),
    ("cut4", "(12345 1234) x2", sn([1,2,3,4,5],2,4,2), 26),
    ("cut5", "(12 12 1) x2 + hat clock", sn([1,2],3,1,2), 29),
    ("cut6", "two lanes, different cuts", sn([1,2],3,1,2), 26),
    ("cut7", "depth-2: A A A-cut", sn([1,2,3],3,2,1)*2 + sn([1,2,3],3,2,1)[:7], 28),
]

def parse(path):
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
                if st & 0xF0 == 0x90 and d2 > 0:
                    on.append((t * tempo / ppq / 1e6, st & 0x0F, d1, d2))
            else: i += 1
    return on

def main():
    ref = parse("cutoff.mid")
    beats = []
    t0 = 0.0
    ok = True
    for name, desc, sym, root in SPECS:
        barlen = len(sym) * PULSE
        # take bar 1 of this uberloop from the shipped render (drums + bass)
        hits = sorted([round(t - t0, 4), p, v, ch]
                      for t, ch, p, v in ref if t0 - 0.002 <= t < t0 + barlen - 0.002)
        # regenerate bass independently and check it matches the render's ch3
        phase = 0; bass_pred = []
        for k, s in enumerate(sym):
            if s == 1: phase = 0
            p = root if phase % 2 == 0 else root + 12
            bass_pred.append((round(k * PULSE, 4), p))
            phase += 1
        bass_got = sorted((t, p) for t, p, v, ch in hits if ch == 3)
        match = len(bass_got) == len(bass_pred) and all(
            pg == pp and abs(tg - tp) <= 0.002
            for (tg, pg), (tp, pp) in zip(bass_got, sorted(bass_pred)))
        if not match:
            ok = False
            print(f"{name}: BASS MISMATCH ({len(bass_got)} vs {len(bass_pred)})")
        beats.append({"name": name, "desc": desc, "barlen": barlen, "hits": hits})
        t0 += barlen * 4
    with open("perform_data.js", "w", encoding="utf-8") as f:
        f.write("const PERF = " + json.dumps({"pulse": PULSE, "beats": beats}) + ";\n")
    total = sum(len(b["hits"]) for b in beats)
    print(f"perform_data.js: {len(beats)} uberloops, {total} hits, bass verified: {ok}")
    if not ok: raise SystemExit(1)

if __name__ == "__main__":
    main()
