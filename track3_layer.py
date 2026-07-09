# Curated track 3 (4 cycled bases, short rolls): good-tagged drum bases + a melody built from the states of
# good-tagged melody bars.
#
# The Glass layer (glass_layer.py, seed 0x91a55) is deterministic, so we re-run
# its state generation to recover, for each absolute bar of the original track,
# the (collection, pattern) that was sounding. The user tagged specific bars
# melody-good; we take those states and compose the new track's fabric from
# them: hold a state for 2 bars, flip back to the previous state now and then
# ("flip back and forth between some"), and otherwise progress down the list.
# Voices (chord pulses / drone / descant / doubled bass) as in glass_layer.py.

import struct, random, math

DRUMS = "C:/Users/Jon/AppData/Local/Temp/claude/c--Users-Jon-hello-rust/74145bec-53c1-49e9-91f2-ffec1255555d/scratchpad/track3_drums.mid"
OUT = "track3.mid"
PPQ = 480; TEMPO = 500000; BAR = 4.0
SRC_NBARS = 400
GOOD_MELODY_BARS = sorted(set([
    # (unit-1)*4 + (bar-1) from the tag list
    1, 2, 14, 26, 30, 39, 69, 89, 128, 161, 166, 204, 208, 213, 214, 216,
    235, 237, 239, 244, 249, 265, 266, 271, 291, 292, 301, 305, 308, 321,
    337, 345, 346, 347, 373, 395,
]))
N_UNITS = 37
NBARS = N_UNITS * 4

# --- replay glass_layer state generation (same seed, same draw order) --------
rng = random.Random(0x91a55)
coll = [57, 60, 64, 67]
def ok(c):
    if len(set(p % 12 for p in c)) < 4: return False
    gaps = [b - a for a, b in zip(c, c[1:])]
    return all(2 <= g <= 5 for g in gaps) and c[-1] - c[0] <= 12
coll_by_bar = []
next_shift = rng.randint(6, 12)
for bar in range(SRC_NBARS):
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
pattern = [0, 1, 2, 3]
pattern_by_bar = []
next_mut = rng.randint(2, 4)
for bar in range(SRC_NBARS):
    if bar == next_mut:
        r = rng.random()
        if r < 0.40 and len(pattern) < 10:
            pattern = pattern + [pattern[-2] if len(pattern) > 1 else 0]
        elif r < 0.65 and len(pattern) > 3:
            pattern = pattern[:-1]
        elif r < 0.85:
            pattern = pattern[1:] + pattern[:1]
        else:
            pattern = pattern[::-1]
        next_mut = bar + rng.randint(2, 4)
    pattern_by_bar.append(list(pattern))

states = [(coll_by_bar[b], pattern_by_bar[b]) for b in GOOD_MELODY_BARS]

# --- compose the state timeline: hold 2 bars, flip back sometimes, progress --
rng2 = random.Random(0x7a92)
timeline = []
k = 0
while len(timeline) < NBARS:
    timeline += [states[k % len(states)]] * 2
    if k > 0 and rng2.random() < 0.45:                     # flip back
        timeline += [states[(k - 1) % len(states)]] * 2
        if rng2.random() < 0.5:                            # and forth again
            timeline += [states[k % len(states)]] * 2
    k += 1
timeline = timeline[:NBARS]

events = []   # (sec, ch, pitch, vel, dur)
# --- V1: chord pulses --------------------------------------------------------
pulse = 0.25
phase = 0
for bar in range(NBARS):
    c, pat = timeline[bar]
    swell = 46 + 10 * math.sin(2 * math.pi * bar / 64.0)
    for kk in range(int(BAR / pulse)):
        idx = pat[phase % len(pat)]
        phase += 1
        oct_up = 12 if (phase // (len(pat) * 16)) % 3 == 2 else 0
        v = int(swell + rng2.randint(-4, 4))
        top = c[idx] + 12
        chord = [top]
        for step in (1, 2):
            tone = c[(idx - step) % 4]
            while tone >= chord[-1]: tone -= 12
            chord.append(tone)
        for vi, p in enumerate(chord):
            events.append((bar * BAR + kk * pulse, 0, p + oct_up,
                           max(28, v - (0 if vi == 0 else 6)), pulse * 0.9))
# --- V2: drone ---------------------------------------------------------------
bar = 0
while bar < NBARS:
    span = min(rng2.randint(4, 8), NBARS - bar)
    c, _ = timeline[bar]
    events.append((bar * BAR, 1, c[0] - 12, 38, span * BAR - 0.2))
    events.append((bar * BAR, 1, c[2], 34, span * BAR - 0.2))
    bar += span
# --- V3: descant arcs --------------------------------------------------------
bar = rng2.randint(4, 10)
present = True
while bar < NBARS:
    span = rng2.randint(20, 30) if present else rng2.randint(12, 20)
    if present:
        b = bar
        while b < min(bar + span, NBARS):
            c, _ = timeline[int(b)]
            p = rng2.choice(c) + 12 + rng2.choice([0, 0, 12])
            events.append((b * BAR + rng2.choice([0, 1, 2, 3]) * 1.0, 2, p,
                           rng2.randint(40, 52), rng2.choice([1.0, 1.5, 2.0, 3.0])))
            b += rng2.choice([1, 1, 2])
    bar += span
    present = not present
# --- V4: bass, loud, octave-doubled ------------------------------------------
def bass_hit(t, pitch, vel, dur):
    events.append((t, 3, pitch, vel, dur))
    if pitch - 12 >= 19:
        events.append((t, 3, pitch - 12, vel - 6, dur))
for bar in range(0, NBARS, 2):
    c, _ = timeline[bar]
    bass_hit(bar * BAR, c[0] - 24, 96, 2.0)
    if rng2.random() < 0.35:
        bass_hit(bar * BAR + 2.0, c[1] - 24, 84, 1.5)

# --- merge with drums, write -------------------------------------------------
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

ons, offs = parse(DRUMS)
msgs = []
def tick(sec): return int(round(sec * 1e6 * PPQ / TEMPO))
msgs.append((0, 0, bytes([0xFF, 0x51, 0x03]) + TEMPO.to_bytes(3, "big")))
for ch, prog in ((0, 4), (1, 52), (2, 92), (3, 38)):
    msgs.append((0, 0, bytes([0xC0 | ch, prog])))
for sec, ch, p, v in ons: msgs.append((tick(sec), 2, bytes([0x90 | ch, p, v])))
for sec, ch, p in offs: msgs.append((tick(sec), 1, bytes([0x80 | ch, p, 0])))
for sec, ch, p, v, dur in events:
    msgs.append((tick(sec), 2, bytes([0x90 | ch, p, v])))
    msgs.append((tick(sec + dur), 1, bytes([0x80 | ch, p, 0])))
msgs.sort(key=lambda m: (m[0], m[1]))
track = bytearray(); last = 0
for tk, _, b in msgs:
    dv = tk - last; last = tk
    stack = [dv & 0x7f]; dv >>= 7
    while dv: stack.append(0x80 | (dv & 0x7f)); dv >>= 7
    track.extend(reversed(stack)); track.extend(b)
track.extend(b"\x00\xff\x2f\x00")
with open(OUT, "wb") as f:
    f.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ))
    f.write(b"MTrk" + struct.pack(">I", len(track)) + track)
print(f"wrote {OUT}: {len(ons)} drum notes + {len(events)} melody notes, {NBARS} bars")
