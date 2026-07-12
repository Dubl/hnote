# Bouncy electronic bass for the cut-off loops test: octave-bounce pulses on
# GM synth bass 2 (hard/electronic), phase-reset at every motif start so the
# bounce is amputated exactly where the loop is. Reads the drums-only render,
# writes cutoff.mid with the bass merged on ch3.
#
# Usage: python cutoff_bass.py

import json, struct

PULSE = 0.25
PPQ = 480; TEMPO = 500000

# (name, bar_pulses, symbol sequence) — symbol 1 marks a motif start
def seqs():
    def sn(motif, runs, keep, m):
        one = []
        for r in range(runs):
            one += motif if r < runs - 1 else motif[:keep]
        return one * m
    return [
        ("cut1", sn([1,2,3],3,2,2)),
        ("cut2", sn([1,2,3,4],3,3,2)),
        ("cut3", sn([1,2],4,1,2)),
        ("cut4", sn([1,2,3,4,5],2,4,2)),
        ("cut5", sn([1,2],3,1,2)),
        ("cut6", sn([1,2],3,1,2)),
        ("cut7", sn([1,2,3],3,2,1)*2 + sn([1,2,3],3,2,1)[:7]),
    ]

ROOTS = {"cut1":28, "cut2":31, "cut3":33, "cut4":26, "cut5":29, "cut6":26, "cut7":28}

def parse(path):
    d = open(path, "rb").read(); ppq = struct.unpack(">H", d[12:14])[0]
    i = d.index(b"MTrk") + 8; end = i + struct.unpack(">I", d[i-4:i])[0]
    t = 0; tempo = 500000; run = None; ons = []; offs = []
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
            hi = st & 0xF0
            if hi in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                d1, d2 = d[i], d[i+1]; i += 2
                sec = t * tempo / ppq / 1e6
                if hi == 0x90 and d2 > 0: ons.append((sec, st & 0x0F, d1, d2))
                elif hi in (0x80, 0x90): offs.append((sec, st & 0x0F, d1))
            else: i += 1
    return ons, offs

def main():
    events = []                                # (t, pitch, vel, dur)
    t0 = 0.0
    for name, sym in seqs():
        root = ROOTS[name]
        barlen = len(sym) * PULSE
        for bar in range(4):
            phase = 0
            for k, s in enumerate(sym):
                if s == 1: phase = 0           # the bounce is amputated with the run
                p = root if phase % 2 == 0 else root + 12
                v = 112 if s == 1 else (98 if phase % 2 == 0 else 90)
                events.append((t0 + bar*barlen + k*PULSE, p, v, 0.14))
                phase += 1
        t0 += barlen * 4

    ons, offs = parse("build/cutoff_drums.mid")
    msgs = []
    def tick(sec): return int(round(sec * 1e6 * PPQ / TEMPO))
    msgs.append((0, 0, bytes([0xFF, 0x51, 0x03]) + TEMPO.to_bytes(3, "big")))
    msgs.append((0, 0, bytes([0xC3, 39])))     # ch3: synth bass 2
    for sec, ch, p, v in ons: msgs.append((tick(sec), 2, bytes([0x90 | ch, p, v])))
    for sec, ch, p in offs: msgs.append((tick(sec), 1, bytes([0x80 | ch, p, 0])))
    for sec, p, v, dur in events:
        msgs.append((tick(sec), 2, bytes([0x93, p, v])))
        msgs.append((tick(sec + dur), 1, bytes([0x83, p, 0])))
    msgs.sort(key=lambda m: (m[0], m[1]))
    track = bytearray(); last = 0
    for tk, _, b in msgs:
        dv = tk - last; last = tk
        stack = [dv & 0x7f]; dv >>= 7
        while dv: stack.append(0x80 | (dv & 0x7f)); dv >>= 7
        track.extend(reversed(stack)); track.extend(b)
    track.extend(b"\x00\xff\x2f\x00")
    with open("cutoff.mid", "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ))
        f.write(b"MTrk" + struct.pack(">I", len(track)) + track)
    print(f"cutoff.mid: drums + {len(events)} bass notes")

if __name__ == "__main__":
    main()
