# The Amen break, natively: acceptance test for the vertical axis.
# Three tabs compiled via apply_stack (each self-verified 4/4), then the
# 4-bar break assembled (A A B C), rendered at 136bpm, and every onset
# machine-verified against the handwritten transcription table below.
#
# Voices: 1=36 kick, 3=42 ride/hat, 6=49 crash, 7=40 snare (negative=ghost).
# Bar 4 is bars-1/2's kick+snare lanes at lane phase 14 (= displaced +2
# pulses, an 8th late) - the break's signature stumble via our own phase.
import json, struct, subprocess, sys

P = 15 / 136                      # pulse = a 16th at 136 bpm

KICK = "motif=[1,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0]"
SN_A = "motif=[0,0,0,0,7,0,0,-7,0,-7,0,0,7,0,0,-7]"
SN_B = "motif=[0,0,0,0,7,0,0,-7,0,-7,0,0,0,0,7,0]"
RIDE4 = "motif=[3,0,3,0,3,0,3,0,6,0,3,0,3,0,3,0]"

BLOBS = {
    "amenA": f"hnote stack v2 pulse={P} lane1={{periods=[16] motif=[3,0]}} "
             f"lane2={{periods=[16] {KICK}}} lane3={{periods=[16] {SN_A}}}",
    "amenB": f"hnote stack v2 pulse={P} lane1={{periods=[16] motif=[3,0]}} "
             f"lane2={{periods=[16] {KICK}}} lane3={{periods=[16] {SN_B}}}",
    "amenC": f"hnote stack v2 pulse={P} lane1={{periods=[16] {RIDE4}}} "
             f"lane2={{periods=[16] {KICK} phase=14}} lane3={{periods=[16] {SN_A} phase=14}}",
}

# ---- the transcription table (bar-relative pulse index, midi, velocity) ----
RIDE13 = [(0, 42, 116)] + [(k, 42, 102) for k in range(2, 16, 2)]
KICK13 = [(0, 36, 116), (2, 36, 88), (10, 36, 88), (11, 36, 88)]
SNARE_A = [(4, 40, 88), (7, 40, 52), (9, 40, 52), (12, 40, 88), (15, 40, 52)]
SNARE_B = [(4, 40, 88), (7, 40, 52), (9, 40, 52), (14, 40, 88)]
RIDE_4 = [(0, 42, 116)] + [(k, 42, 88) for k in range(2, 16, 2) if k != 8] + [(8, 49, 88)]
KICK_4 = [(2, 36, 116), (4, 36, 88), (12, 36, 88), (13, 36, 88)]
SNARE_4 = [(1, 40, 52), (6, 40, 88), (9, 40, 52), (11, 40, 52), (14, 40, 88)]
BARS = [RIDE13 + KICK13 + SNARE_A,
        RIDE13 + KICK13 + SNARE_A,
        RIDE13 + KICK13 + SNARE_B,
        RIDE_4 + KICK_4 + SNARE_4]

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
            if d[i+1] == 0x51: tempo = int.from_bytes(d[i+3:i+6], "big")
            i += 3 + d[i+2]; run = None
        elif b in (0xF0, 0xF7): i += 2 + d[i+1]; run = None
        else:
            if b & 0x80: st = b; i += 1; run = st
            else: st = run
            if st & 0xF0 in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                d1, d2 = d[i], d[i+1]; i += 2
                if st & 0xF0 == 0x90 and d2 > 0: on.append((t*tempo/ppq/1e6, d1, d2))
            else: i += 1
    return on

def main():
    for name, blob in BLOBS.items():
        r = subprocess.run([sys.executable, "apply_stack.py", blob, "--name", name],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"{name} compile failed:\n{r.stdout[-800:]}{r.stderr[-400:]}")
        print(f"{name}: {r.stdout.strip().splitlines()[-1]}")

    measures = [json.load(open(f"measures.{n}.json", encoding="utf-8"))[0] for n in BLOBS]
    json.dump(measures, open("measures.amen.json", "w", encoding="utf-8"), indent=1)
    calls = [{"target": t, "function": "once"} for t in ["amenA", "amenA", "amenB", "amenC"]]
    json.dump(calls, open("calllist.amen.jsonc", "w", encoding="utf-8"), indent=1)
    barlen = 16 * P
    r = subprocess.run([sys.executable, "build_track.py", "amen", "calllist.amen.jsonc",
                        "--measures", "measures.amen.json", "--no-melody",
                        "--duration", str(4 * barlen)], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(r.stdout[-800:] + r.stderr[-400:])
    print(r.stdout.strip().splitlines()[-1])

    on = parse_mid("amen.mid")
    ok = 0
    for bar in range(4):
        got = sorted((t - bar*barlen, p, v) for t, p, v in on
                     if bar*barlen - 0.003 <= t < (bar+1)*barlen - 0.003)
        want = sorted((k * P, p, v) for k, p, v in BARS[bar])
        pool = list(got); good = len(got) == len(want)
        if good:
            for tt, pp, vv in want:
                m = [j for j, (t2, p2, v2) in enumerate(pool)
                     if p2 == pp and v2 == vv and abs(t2 - tt) <= 0.0025]
                if not m:
                    good = False
                    print(f"  bar {bar+1}: missing {pp} v{vv} @ {tt:.4f}s")
                    break
                pool.pop(m[0])
        else:
            print(f"  bar {bar+1}: count got {len(got)} want {len(want)}")
        ok += good
    print(f"AMEN VERIFICATION: {ok}/4 bars match the transcription exactly (t+pitch+vel)")
    if ok < 4: raise SystemExit(1)

if __name__ == "__main__":
    main()
