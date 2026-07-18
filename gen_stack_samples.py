# Synthesize the stack.html drum kit: 808/909-flavored, deep-house/grime
# voicing. Pure python + wave; mp3 via ffmpeg. Voices match SOUNDS in
# stack.html: 36 kick, 38 snare(clap), 42 hat, 56 cowbell, 75 rim/clave.
# Output: stack_samples/p{n}.mp3 (self-hosted; page falls back to magenta).
import math, os, random, struct, subprocess, wave

SR = 44100
random.seed(3608)   # deterministic kit

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

def kick():
    # deep-house kick: 95->42Hz sweep, soft drive, long sub tail
    n = int(0.50 * SR); out = []; ph = 0.0
    for i in range(n):
        t = i / SR
        f = 42 + 53 * math.exp(-t / 0.020)
        ph += 2 * math.pi * f / SR
        x = math.sin(ph) * env(t, 0.16)
        x += 0.35 * (random.random() * 2 - 1) * env(t, 0.004)   # click transient
        out.append(math.tanh(1.9 * x))
    return out

def clap():
    # grime clap-snare: triple noise burst into bandpassed body + 190Hz thump
    n = int(0.35 * SR); noise = []
    for i in range(n):
        t = i / SR
        if t < 0.030: e = env(t % 0.011, 0.0045)
        else:         e = 0.9 * env(t - 0.030, 0.075)
        noise.append((random.random() * 2 - 1) * e)
    body = biquad_bp(noise, 1300, 1.1)
    out = []
    for i in range(n):
        t = i / SR
        thump = 0.5 * math.sin(2 * math.pi * 190 * t) * env(t, 0.045)
        out.append(math.tanh(2.2 * (1.6 * body[i] + thump)))
    return out

def hat():
    # crisp closed hat: metallic squares + highpassed noise, fast decay
    freqs = [3113, 4160, 5333, 6217, 7597, 8412]
    n = int(0.12 * SR); raw = []
    for i in range(n):
        t = i / SR
        m = sum((1 if math.sin(2 * math.pi * f * t) > 0 else -1) for f in freqs) / len(freqs)
        raw.append((0.6 * m + 0.7 * (random.random() * 2 - 1)) * env(t, 0.028))
    return hp1(hp1(raw, 7000), 7000)

def cowbell():
    # 808 cowbell: detuned squares 540+800Hz through a mid bandpass
    n = int(0.28 * SR); raw = []
    for i in range(n):
        t = i / SR
        s = (1 if math.sin(2 * math.pi * 540 * t) > 0 else -1) * 0.6 \
          + (1 if math.sin(2 * math.pi * 800 * t) > 0 else -1) * 0.4
        e = env(t, 0.012) * 0.7 + env(t, 0.055) * 0.5
        raw.append(s * e)
    return biquad_bp(raw, 660, 2.2)

def rim():
    # 808 rimshot: bright ping + woody knock, very short
    n = int(0.10 * SR); out = []
    for i in range(n):
        t = i / SR
        x = 0.8 * math.sin(2 * math.pi * 1720 * t) * env(t, 0.0045)
        x += 0.6 * math.sin(2 * math.pi * 455 * t) * env(t, 0.020)
        x += 0.3 * (random.random() * 2 - 1) * env(t, 0.002)
        out.append(math.tanh(2.0 * x))
    return out

VOICES = {36: kick, 38: clap, 42: hat, 56: cowbell, 75: rim}
os.makedirs("stack_samples", exist_ok=True)
for p, fn in VOICES.items():
    x = fn()
    peak = max(abs(v) for v in x) or 1.0
    pcm = b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * 0.92)) * 32767)) for v in x)
    wavp = f"stack_samples/p{p}.wav"
    w = wave.open(wavp, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm); w.close()
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wavp,
                        "-codec:a", "libmp3lame", "-b:a", "192k", f"stack_samples/p{p}.mp3"])
    assert r.returncode == 0
    os.remove(wavp)
    print(f"p{p}: {len(x)/SR:.2f}s  peak-normalized to -0.7dB")
print("kit written to stack_samples/")
