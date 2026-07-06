# Post-render transform for the levee_solo experiment:
#  1. Unconventional drum kit: remap ch9 notes (elec kick/snare, maracas hats,
#     china/splash crashes, conga toms).
#  2. Key modulation arch across sections: E->G->A->G->B->A->G->D->E
#     (melodic channels 1-5 transposed per bar; note-offs follow their note-on).
#  3. Instrument evolution: per-channel program trajectories that morph away
#     and return (e.g. Crystal -> Sitar -> Kalimba -> Crystal).
# Usage: python solo_post.py levee_solo.mid

import struct, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "levee_solo.mid"
BAR = 4 * 0.869565
TPS = 480 * 1_000_000 / 500_000  # ticks per second at the writer's fixed tempo

DRUM_MAP = {35:36, 38:40, 42:70, 57:52, 49:55, 41:64, 43:63, 45:62}

def key_offset(bar):  # 1-indexed bar -> semitone offset from E
    if bar <= 20: return 0    # E
    if bar <= 25: return 3    # G
    if bar <= 39: return 5    # A
    if bar <= 47: return 3    # G
    if bar <= 55: return 7    # B
    if bar <= 69: return 5    # A
    if bar <= 74: return 3    # G
    if bar <= 92: return -2   # D
    return 0                  # home: E

# (channel, bar, program) — tick-0 entries replace the writer's defaults
PROGRAM_PLAN = [
    (1,1,38),(1,48,39),(1,75,87),(1,105,38),      # synth bass 1 -> 2 -> bass+lead -> back
    (2,1,86),(2,26,84),(2,56,80),(2,93,86),       # fifths -> charang -> square -> back
    (3,1,93),(3,46,95),(3,75,89),(3,105,93),      # metallic -> sweep -> warm -> back
    (4,1,98),(4,40,104),(4,70,108),(4,93,98),     # crystal -> sitar -> kalimba -> back
    (5,1,101),(5,48,103),(5,75,102),(5,105,101),  # goblins -> sci-fi -> echoes -> back
]

def vlq(v):
    out = [v & 0x7F]; v >>= 7
    while v: out.append((v & 0x7F) | 0x80); v >>= 7
    return bytes(reversed(out))

d = open(PATH, "rb").read()
div = struct.unpack(">H", d[12:14])[0]
tlen = struct.unpack(">I", d[18:22])[0]
body = d[22:22+tlen]

# ---- parse ----
events = []  # (tick, order, kind, data...)
i = 0; tick = 0; run = None
def rd_vlq(b, i):
    v = 0
    while True:
        v = (v << 7) | (b[i] & 0x7F)
        if not b[i] & 0x80: return v, i + 1
        i += 1
while i < len(body):
    dt, i = rd_vlq(body, i); tick += dt
    st = body[i]
    if st & 0x80: run = st; i += 1
    else: st = run
    if st == 0xFF:
        mt = body[i]; i += 1; ln, i = rd_vlq(body, i)
        events.append((tick, 0, "meta", mt, body[i:i+ln])); i += ln
    elif st in (0xF0, 0xF7):
        ln, i = rd_vlq(body, i); i += ln
    elif st & 0xF0 == 0xC0:
        i += 1  # drop original program changes; the plan replaces them
    else:
        events.append((tick, 1, "ch", st, body[i], body[i+1])); i += 2

# ---- transform notes ----
active = {}  # (ch, orig_note) -> transposed note
out_ev = []
for tick, order, kind, *rest in events:
    if kind == "meta":
        mt, data = rest
        if mt == 0x2F: continue  # re-added at the end
        out_ev.append((tick, 0, bytes([0xFF, mt]) + vlq(len(data)) + bytes(data)))
        continue
    st, n, v = rest
    ch = st & 0x0F; hi = st & 0xF0
    if hi in (0x80, 0x90):
        is_on = hi == 0x90 and v > 0
        if ch == 9:
            n2 = DRUM_MAP.get(n, n)
        elif 1 <= ch <= 5:
            if is_on:
                bar = int((tick / TPS) / BAR) + 1
                n2 = max(0, min(127, n + key_offset(bar)))
                active[(ch, n)] = n2
            else:
                n2 = active.pop((ch, n), n)
        else:
            n2 = n
        out_ev.append((tick, 2 if is_on else 1, bytes([st, n2, v])))
    else:
        out_ev.append((tick, 1, bytes([st, n, v])))

# ---- program plan ----
for ch, bar, prog in PROGRAM_PLAN:
    t = 0 if bar == 1 else int(round((bar - 1) * BAR * TPS))
    out_ev.append((t, 0, bytes([0xC0 | ch, prog])))

out_ev.sort(key=lambda e: (e[0], e[1]))

# ---- serialize ----
track = bytearray(); last = 0
for tick, order, data in out_ev:
    track += vlq(tick - last) + data; last = tick
track += vlq(0) + bytes([0xFF, 0x2F, 0x00])

out = bytearray()
out += b"MThd" + struct.pack(">IHHH", 6, 0, 1, div)
out += b"MTrk" + struct.pack(">I", len(track)) + track
open(PATH, "wb").write(out)
print(f"transformed {PATH}: {len([e for e in out_ev if e[2][0]&0xF0==0x90])} note-ons, "
      f"{len(PROGRAM_PLAN)} program changes, drums remapped, keys modulated")
