# Layer a Philip Glass-style melodic fabric over random_beats_spill.mid.
# Deterministic (seeded). Reads the drum render, generates four melodic voices,
# writes random_beats_glass.mid (format 0, 480 PPQ, fixed tempo, like midi_file.rs).
#
# Design:
#   V1 ch0 e-piano   : continuous 8th-note arpeggio, additive/subtractive cell
#                      process (grow, shrink, reverse a step at a time), phase
#                      carries across bars so the stream never restarts.
#   V2 ch1 choir     : two-tone drone, one long note pair every 4-8 bars,
#                      moving only when the collection drifts.
#   V3 ch2 flute     : sparse high descant, present in slow arcs (in for ~40
#                      bars, out for ~30), one long tone every 2-4 beats.
#   V4 ch3 warm bass : root pulse every 2 bars, half-bar durations.
# Harmony: a 4-tone collection starting A-C-E-G; every ~8 bars one tone moves
# by 1-2 semitones (distinct tones, range-clamped). Minimal-motion drift, no
# cadences, no progression.

import struct, random

SRC = "random_beats_spill.mid"
OUT = "random_beats_glass.mid"
PPQ = 480
TEMPO = 500000            # 120 bpm quarter -> 1 tick = 1/960 s
BAR = 4.0
NBARS = 400
SEED = 0x91a55

def parse(path):
    d = open(path, "rb").read()
    ppq = struct.unpack(">H", d[12:14])[0]
    i = d.index(b"MTrk") + 8
    end = i + struct.unpack(">I", d[i-4:i])[0]
    t = 0; tempo = 500000; run = None
    ons = []; offs = []
    while i < end:
        dv = 0
        while True:
            b = d[i]; i += 1; dv = (dv << 7) | (b & 0x7f)
            if not b & 0x80: break
        t += dv
        b = d[i]
        if b == 0xFF:
            mt = d[i+1]; ln = d[i+2]
            if mt == 0x51: tempo = int.from_bytes(d[i+3:i+3+ln], "big")
            i += 3 + ln; run = None
        elif b in (0xF0, 0xF7):
            i += 2 + d[i+1]; run = None
        else:
            if b & 0x80: st = b; i += 1; run = st
            else: st = run
            hi = st & 0xF0
            if hi in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                d1, d2 = d[i], d[i+1]; i += 2
                sec = t * tempo / ppq / 1e6
                if hi == 0x90 and d2 > 0: ons.append((sec, st & 0x0F, d1, d2))
                elif hi in (0x80, 0x90): offs.append((sec, st & 0x0F, d1))
            else:
                i += 1
    return ons, offs

rng = random.Random(SEED)

# --- harmonic drift ---------------------------------------------------------
coll = [57, 60, 64, 67]                       # A3 C4 E4 G4
def ok(c):
    # keep the sonority open: distinct pitch classes, steps of a 2nd..4th
    # between neighbours, whole thing within an octave
    if len(set(p % 12 for p in c)) < 4: return False
    gaps = [b - a for a, b in zip(c, c[1:])]
    return all(2 <= g <= 5 for g in gaps) and c[-1] - c[0] <= 12
coll_by_bar = []
next_shift = rng.randint(6, 12)
for bar in range(NBARS):
    if bar == next_shift:
        for _ in range(40):
            k = rng.randrange(4)
            step = rng.choice([-2, -1, 1, 2])
            cand = sorted(coll[:k] + [coll[k] + step] + coll[k+1:])
            if 53 <= cand[0] and cand[-1] <= 72 and ok(cand):
                coll = cand
                break
        next_shift = bar + rng.randint(6, 12)
    coll_by_bar.append(list(coll))

events = []   # (sec, ch, pitch, vel, dur)

# --- V1: additive arpeggio --------------------------------------------------
pattern = [0, 1, 2, 3]
next_mut = rng.randint(2, 4)
pulse = 0.25
phase = 0
import math
for bar in range(NBARS):
    if bar == next_mut:
        r = rng.random()
        if r < 0.40 and len(pattern) < 10:          # grow: mirror-step
            pattern = pattern + [pattern[-2] if len(pattern) > 1 else 0]
        elif r < 0.65 and len(pattern) > 3:         # shrink
            pattern = pattern[:-1]
        elif r < 0.85:                              # rotate
            pattern = pattern[1:] + pattern[:1]
        else:                                       # reverse
            pattern = pattern[::-1]
        next_mut = bar + rng.randint(2, 4)
    c = coll_by_bar[bar]
    swell = 46 + 10 * math.sin(2 * math.pi * bar / 64.0)
    for k in range(int(BAR / pulse)):
        idx = pattern[phase % len(pattern)]
        phase += 1
        oct_up = 12 if (phase // (len(pattern) * 16)) % 3 == 2 else 0
        v = int(swell + rng.randint(-4, 4))
        # pulse a 3-voice chord: an inversion of the collection with the
        # pattern-selected tone on top, voices stacked strictly descending
        # from it so the additive process still draws the top-line contour
        top = c[idx] + 12
        chord = [top]
        for step in (1, 2):
            tone = c[(idx - step) % 4]
            while tone >= chord[-1]: tone -= 12
            chord.append(tone)
        for vi, p in enumerate(chord):
            events.append((bar * BAR + k * pulse, 0, p + oct_up,
                           max(28, v - (0 if vi == 0 else 6)), pulse * 0.9))

# --- V2: drone --------------------------------------------------------------
bar = 0
while bar < NBARS:
    span = rng.randint(4, 8)
    span = min(span, NBARS - bar)
    c = coll_by_bar[bar]
    low, high = c[0] - 12, c[2]
    events.append((bar * BAR, 1, low, 38, span * BAR - 0.2))
    events.append((bar * BAR, 1, high, 34, span * BAR - 0.2))
    bar += span

# --- V3: flute arcs ---------------------------------------------------------
bar = rng.randint(8, 16)
present = True
while bar < NBARS:
    span = rng.randint(30, 45) if present else rng.randint(20, 35)
    if present:
        b = bar
        while b < min(bar + span, NBARS):
            c = coll_by_bar[int(b)]
            p = rng.choice(c) + 12 + rng.choice([0, 0, 12])
            dur = rng.choice([1.0, 1.5, 2.0, 3.0])
            events.append((b * BAR + rng.choice([0, 1, 2, 3]) * 1.0, 2, p, rng.randint(40, 52), dur))
            b += rng.choice([1, 1, 2])
    bar += span
    present = not present

# --- V4: bass pulse (prominent, octave-doubled) ------------------------------
def bass_hit(t, pitch, vel, dur):
    events.append((t, 3, pitch, vel, dur))
    if pitch - 12 >= 19:                       # sub-octave double
        events.append((t, 3, pitch - 12, vel - 6, dur))
for bar in range(0, NBARS, 2):
    c = coll_by_bar[bar]
    bass_hit(bar * BAR, c[0] - 24, 96, 2.0)
    if rng.random() < 0.35:
        bass_hit(bar * BAR + 2.0, c[1] - 24, 84, 1.5)

# --- merge with drums and write ---------------------------------------------
ons, offs = parse(SRC)
msgs = []                                  # (tick, order, bytes)
def tick(sec): return int(round(sec * 1e6 * PPQ / TEMPO))

msgs.append((0, 0, bytes([0xFF, 0x51, 0x03]) + TEMPO.to_bytes(3, "big")))
for ch, prog in ((0, 4), (1, 52), (2, 92), (3, 38)):   # epiano, choir, bowed-glass pad, synth bass
    msgs.append((0, 0, bytes([0xC0 | ch, prog])))
for sec, ch, p, v in ons:
    msgs.append((tick(sec), 2, bytes([0x90 | ch, p, v])))
for sec, ch, p in offs:
    msgs.append((tick(sec), 1, bytes([0x80 | ch, p, 0])))
for sec, ch, p, v, dur in events:
    msgs.append((tick(sec), 2, bytes([0x90 | ch, p, v])))
    msgs.append((tick(sec + dur), 1, bytes([0x80 | ch, p, 0])))

msgs.sort(key=lambda m: (m[0], m[1]))
track = bytearray()
last = 0
for tk, _, b in msgs:
    dv = tk - last; last = tk
    stack = [dv & 0x7f]; dv >>= 7
    while dv: stack.append(0x80 | (dv & 0x7f)); dv >>= 7
    track.extend(reversed(stack)); track.extend(b)
track.extend(b"\x00\xff\x2f\x00")
with open(OUT, "wb") as f:
    f.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ))
    f.write(b"MTrk" + struct.pack(">I", len(track)) + track)
print(f"wrote {OUT}: {len(ons)} drum notes + {len(events)} melody notes")
