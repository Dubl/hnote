# Jungle/DnB kit CANDIDATES: several synthesized options per slot, all run
# through the genre's degradation chain (12-bit-ish quantize, sample-hold
# downsample, saturation, high rolloff - the SP1200/vinyl character).
# Output: kit_candidates/<slot>_<n>.mp3 + manifest.json for kit.html.
# The chosen kit is applied later by apply_kit.py; the deep-house kit stays
# regenerable via gen_stack_samples.py (untouched).
import json, math, os, random, struct, subprocess, wave

SR = 44100
random.seed(9104)

def env(t, tau): return math.exp(-t / tau)

def biquad_bp(x, f0, Q):
    w0 = 2 * math.pi * f0 / SR
    alpha = math.sin(w0) / (2 * Q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * math.cos(w0), 1 - alpha
    y, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for xn in x:
        yn = (b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0
        y.append(yn); x2, x1 = x1, xn; y2, y1 = y1, yn
    return y

def hp1(x, fc):
    rc = 1 / (2 * math.pi * fc); dt = 1 / SR; a = rc / (rc + dt)
    y, px, py = [], 0.0, 0.0
    for xn in x:
        py = a * (py + xn - px); px = xn; y.append(py)
    return y

def degrade(x, bits=12, sr2=26000, drive=1.4, lp=10000):
    out, ph, held, step = [], 1.0, 0.0, sr2 / SR
    for v in x:                                   # sample-hold downsample
        ph += step
        if ph >= 1.0: ph -= 1.0; held = v
        out.append(held)
    q = float(2 ** (bits - 1))
    out = [math.floor(v * q) / q for v in out]    # bit quantize
    out = [math.tanh(drive * v) for v in out]     # saturation
    rc = 1 / (2 * math.pi * lp); dt = 1 / SR; a = dt / (rc + dt)
    y, res = 0.0, []
    for v in out:                                 # high rolloff
        y += a * (v - y); res.append(y)
    return res

def kick(f0, f1, ptau, atau, dur, knock=0.0):
    n = int(dur * SR); out = []; ph = 0.0
    for i in range(n):
        t = i / SR
        f = f1 + (f0 - f1) * math.exp(-t / ptau)
        ph += 2 * math.pi * f / SR
        x = math.sin(ph) * env(t, atau)
        if knock: x += knock * math.sin(2 * math.pi * 190 * t) * env(t, 0.02)
        x += 0.3 * (random.random() * 2 - 1) * env(t, 0.003)
        out.append(x)
    return out

def snare(shellfs, shelltau, noisef, noiseq, noisetau, dur, snap=0.5):
    n = int(dur * SR)
    noise = [(random.random() * 2 - 1) for _ in range(n)]
    buzz = biquad_bp(noise, noisef, noiseq)
    out = []
    for i in range(n):
        t = i / SR
        shell = sum(0.5 * math.sin(2 * math.pi * f * t) * env(t, shelltau) for f in shellfs)
        out.append(shell + snap * noise[i] * env(t, 0.004) + 1.6 * buzz[i] * env(t, noisetau))
    return out

def clap(bodyf, tail, dur):
    n = int(dur * SR); noise = []
    for i in range(n):
        t = i / SR
        e = env(t % 0.010, 0.004) if t < 0.028 else 0.9 * env(t - 0.028, tail)
        noise.append((random.random() * 2 - 1) * e)
    return biquad_bp(noise, bodyf, 1.0)

def hat(metal, hpf, tau, dur):
    freqs = [3113, 4160, 5333, 6217, 7597, 8412]
    n = int(dur * SR); raw = []
    for i in range(n):
        t = i / SR
        m = sum((1 if math.sin(2 * math.pi * f * t) > 0 else -1) for f in freqs) / len(freqs)
        raw.append((metal * m + 0.8 * (random.random() * 2 - 1)) * env(t, tau))
    return hp1(hp1(raw, hpf), hpf)

def rim(pingf, knockf, dur):
    n = int(dur * SR); out = []
    for i in range(n):
        t = i / SR
        out.append(0.8 * math.sin(2 * math.pi * pingf * t) * env(t, 0.005)
                   + 0.6 * math.sin(2 * math.pi * knockf * t) * env(t, 0.02)
                   + 0.3 * (random.random() * 2 - 1) * env(t, 0.002))
    return out

def crash(tau, lpf, dur):
    n = int(dur * SR); raw = []
    freqs = [2417, 3221, 4109, 5561, 6733, 7919]
    for i in range(n):
        t = i / SR
        m = sum((1 if math.sin(2 * math.pi * f * t) > 0 else -1) for f in freqs) / len(freqs)
        raw.append((0.4 * m + 0.9 * (random.random() * 2 - 1)) * (env(t, tau) + 0.3 * env(t, tau * 2.5)))
    return hp1(raw, lpf)

def sub(f0, f1, ptau, atau, dur, drive):
    n = int(dur * SR); out = []; ph = 0.0
    for i in range(n):
        t = i / SR
        f = f1 + (f0 - f1) * math.exp(-t / ptau) if f0 != f1 else f0
        ph += 2 * math.pi * f / SR
        x = math.tanh(drive * math.sin(ph)) * env(t, atau)
        x += 0.15 * (random.random() * 2 - 1) * env(t, 0.002)
        out.append(x)
    return out

CANDS = {
  "kick": [
    ("tight",  lambda: degrade(kick(120, 55, 0.012, 0.045, 0.18), 12, 26000, 1.6)),
    ("knock",  lambda: degrade(kick(95, 58, 0.02, 0.06, 0.25, knock=0.5), 12, 26000, 1.5)),
    ("boom",   lambda: degrade(kick(100, 48, 0.018, 0.09, 0.35), 12, 22000, 1.3)),
  ],
  "snare": [
    ("crack",  lambda: degrade(snare([220, 330], 0.03, 1500, 0.9, 0.07, 0.28), 10, 26000, 1.8)),
    ("paper",  lambda: degrade(snare([280], 0.02, 2400, 0.8, 0.05, 0.22, snap=0.7), 11, 24000, 1.6)),
    ("think",  lambda: degrade(snare([180, 240], 0.045, 1100, 1.1, 0.10, 0.32), 12, 26000, 1.5)),
    ("high",   lambda: degrade(snare([320, 480], 0.08, 2000, 1.0, 0.08, 0.30), 11, 26000, 1.6)),
  ],
  "clap": [
    ("tightclap", lambda: degrade(clap(1400, 0.05, 0.22), 11, 24000, 1.9)),
    ("claplayer", lambda: degrade([a + 0.5 * b for a, b in zip(clap(1300, 0.07, 0.3),
                       snare([200], 0.04, 1600, 1.0, 0.06, 0.3))], 12, 26000, 1.5)),
    ("snapclap",  lambda: degrade(clap(1800, 0.04, 0.18), 10, 22000, 2.0)),
  ],
  "hatc": [
    ("dusty",  lambda: degrade(hat(0.3, 6500, 0.020, 0.10), 10, 22000, 1.5, 9000)),
    ("metal",  lambda: degrade(hat(0.7, 7000, 0.025, 0.12), 12, 26000, 1.4)),
    ("soft",   lambda: degrade(hat(0.2, 4500, 0.030, 0.12), 12, 24000, 1.1, 8000)),
  ],
  "hato": [
    ("dustyO", lambda: degrade(hat(0.3, 6000, 0.12, 0.45), 10, 22000, 1.4, 9000)),
    ("metalO", lambda: degrade(hat(0.7, 6500, 0.18, 0.55), 12, 26000, 1.3)),
  ],
  "rim": [
    ("classic", lambda: degrade(rim(1720, 455, 0.10), 12, 26000, 1.6)),
    ("woody",   lambda: degrade(rim(2100, 800, 0.08), 11, 24000, 1.7)),
  ],
  "crash": [
    ("wash",   lambda: degrade(crash(0.45, 3800, 1.4), 11, 24000, 1.3, 9000)),
    ("darkw",  lambda: degrade(crash(0.35, 2800, 1.2), 10, 20000, 1.4, 6500)),
  ],
  "sub": [
    ("sine",   lambda: degrade(sub(43.7, 43.7, 1, 0.5, 1.0, 1.2), 14, 32000, 1.0, 8000)),
    ("drop",   lambda: degrade(sub(80, 45, 0.05, 0.4, 0.9, 1.4), 14, 32000, 1.0, 8000)),
    ("satsub", lambda: degrade(sub(50, 50, 1, 0.35, 0.8, 2.6), 13, 30000, 1.0, 6000)),
  ],
}

os.makedirs("kit_candidates", exist_ok=True)
manifest = {}
for slot, items in CANDS.items():
    manifest[slot] = []
    for i, (label, fn) in enumerate(items, 1):
        x = fn()
        i0 = 0
        while i0 < len(x) and abs(x[i0]) < 0.01: i0 += 1
        x = x[i0:] if i0 < len(x) else x
        n = len(x); fade = min(int(0.006 * SR), n)
        for k in range(fade): x[n - 1 - k] *= k / fade
        peak = max(abs(v) for v in x) or 1.0
        pcm = b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * 0.92)) * 32767)) for v in x)
        name = f"{slot}_{i}"
        wavp = f"kit_candidates/{name}.wav"
        w = wave.open(wavp, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm); w.close()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wavp,
                        "-codec:a", "libmp3lame", "-b:a", "192k",
                        f"kit_candidates/{name}.mp3"], check=True)
        os.remove(wavp)
        manifest[slot].append({"file": f"{name}.mp3", "label": label})
        print(f"{name} ({label}): {len(x)/SR:.2f}s")
json.dump(manifest, open("kit_candidates/manifest.json", "w", encoding="utf-8"), indent=1)
print("candidates + manifest written to kit_candidates/")
