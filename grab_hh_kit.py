# Build the stack kit from the "Hardcore Gabber Rave Soundfont" by
# LousyBastard (musical-artifacts.com/artifacts/8125, CC-BY 3.0).
# Renders every candidate preset through FluidSynth, measures the trimmed
# samples, picks per slot, writes stack_samples/pNN.mp3.
#
# Kit slots: 36 K kick, 38 S clap, 42 H closed hat, 46 O open hat,
#            75 V rave lead stab, 49 C big FX, 40 N snare.
# Override any pick: python grab_hh_kit.py --kick 7 --clap 3 --stab 12 ...
import argparse, math, os, struct, subprocess, sys, wave

SF = "tools/HardcoreGabber_v1.sf2"
FS = "tools/fluidsynth/fluidsynth-v2.5.6-win10-x64-cpp11/bin/fluidsynth.exe"
SP = os.environ.get("TEMP", ".") + "/hhkit"
os.makedirs(SP, exist_ok=True)

def presets():
    d = open(SF, "rb").read()
    i = d.index(b"phdr")
    size = struct.unpack("<I", d[i+4:i+8])[0]
    out = []
    for k in range(size // 38 - 1):
        off = i + 8 + k * 38
        name = d[off:off+20].split(b"\0")[0].decode("latin1")
        preset, bank = struct.unpack("<HH", d[off+20:off+24])
        out.append((name, bank, preset))
    return out

def midi_for(bank, prog, gate):
    tr = bytearray()
    tr += bytes([0, 0xB0, 0x00, bank, 0, 0xB0, 0x20, 0x00, 0, 0xC0, prog])
    tr += bytes([0, 0x90, 60, 127])
    ticks = int(gate * 960)                    # PPQ 480 @ 120bpm -> 960 ticks/s
    def vlq(n):
        b = [n & 0x7F]; n >>= 7
        while n: b.append(0x80 | (n & 0x7F)); n >>= 7
        return bytes(reversed(b))
    tr += vlq(ticks) + bytes([0x80, 60, 0])
    tr += vlq(1440) + bytes([0xFF, 0x2F, 0])   # +1.5s tail
    return (b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480)
            + b"MTrk" + struct.pack(">I", len(tr)) + bytes(tr))

def render(name, bank, prog, gate):
    mp = f"{SP}/{name}.mid"; wp = f"{SP}/{name}.wav"
    open(mp, "wb").write(midi_for(bank, prog, gate))
    r = subprocess.run([os.path.abspath(FS), "-ni", "-F", wp, "-r", "44100",
                        "-o", "synth.gain=0.7", os.path.abspath(SF), os.path.abspath(mp)],
                       capture_output=True)
    assert r.returncode == 0, name
    w = wave.open(wp); fr = w.readframes(w.getnframes()); w.close()
    v = struct.unpack(f"<{len(fr)//2}h", fr)
    mono = [(v[i] + v[i+1]) / 2 / 32768 for i in range(0, len(v) - 1, 2)]
    i0 = 0
    while i0 < len(mono) and abs(mono[i0]) < 0.01: i0 += 1
    if i0 >= len(mono): return None
    mono = mono[i0:]
    i1 = len(mono)
    while i1 > 1 and abs(mono[i1-1]) < 0.004: i1 -= 1
    mono = mono[:i1]
    if len(mono) < 200: return None
    rms = math.sqrt(sum(x*x for x in mono) / len(mono))
    zc = sum(1 for i in range(1, len(mono)) if mono[i-1] < 0 <= mono[i]) / (len(mono)/44100)
    return {"name": name, "dur": len(mono)/44100, "rms": rms, "zcr": zc, "pcm": mono}

def pick(cands, key):
    return max(cands, key=key)

def main():
    ap = argparse.ArgumentParser()
    for s in ["kick", "clap", "hat", "openhat", "stab", "fx", "snare"]:
        ap.add_argument(f"--{s}", type=int, default=0, help="1-based preset number override")
    args = ap.parse_args()

    ps = presets()
    cat = {}
    for name, bank, prog in ps:
        cat.setdefault(name.split("_")[0], []).append((name, bank, prog))

    rendered = {}
    for group, gate in [("Kick", 1.0), ("Clap", 1.0), ("Hihat", 1.0),
                        ("Snare", 1.0), ("FX", 1.5), ("Lead", 0.16)]:
        rs = []
        for name, bank, prog in cat[group]:
            r = render(name, bank, prog, gate)
            if r: rs.append(r)
        rendered[group] = rs
        print(f"{group}: {len(rs)} usable renders")

    def override(group, n):
        if not n: return None
        want = f"{group}_{n:02d}"
        for r in rendered[group]:
            if r["name"] == want: return r
        raise SystemExit(f"override {want} not found/usable")

    hats = sorted(rendered["Hihat"], key=lambda r: r["dur"])
    picks = {
        36: override("Kick", args.kick) or pick([r for r in rendered["Kick"] if 0.08 < r["dur"] < 0.8]
                                               or rendered["Kick"], lambda r: r["rms"]),
        38: override("Clap", args.clap) or pick(rendered["Clap"], lambda r: r["rms"]),
        42: override("Hihat", args.hat) or hats[0],
        46: override("Hihat", args.openhat) or hats[-1],
        75: override("Lead", args.stab) or pick(rendered["Lead"], lambda r: r["rms"]),
        49: override("FX", args.fx) or pick(rendered["FX"], lambda r: r["dur"]),
        40: override("Snare", args.snare) or pick(rendered["Snare"], lambda r: r["rms"]),
    }

    for note, r in picks.items():
        pcm = r["pcm"][:int(1.6*44100)]
        n = len(pcm)
        fade = min(int(0.006*44100), n)
        for i in range(fade):                   # click-free tail
            pcm[n-1-i] *= i / fade
        peak = max(abs(x) for x in pcm) or 1.0
        raw = b"".join(struct.pack("<h", int(max(-1, min(1, x/peak*0.92))*32767)) for x in pcm)
        wp = f"{SP}/out{note}.wav"
        w = wave.open(wp, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes(raw); w.close()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wp,
                        "-codec:a", "libmp3lame", "-b:a", "192k",
                        f"stack_samples/p{note}.mp3"], check=True)
        print(f"p{note} <- {r['name']}  ({r['dur']:.2f}s, rms {r['rms']:.3f}, zcr {r['zcr']:.0f})")
    print("happy hardcore kit written to stack_samples/")

if __name__ == "__main__":
    main()
