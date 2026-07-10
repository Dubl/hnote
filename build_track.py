# One-command track pipeline: drums render -> optional melody layer -> MP3.
#
#   python build_track.py <name> <calllist> [--measures FILE] [--bars N]
#                         [--no-melody]
#
# Produces: build/<name>_drums.mid, <name>.mid (or drums-only), <name>.mp3.
# Bars default to the number of calls in the calllist (1 call = 1 bar = 4s;
# a call with a roll chain still renders one bar). Audio tools come from
# ./tools/ (run setup_audio_tools.py once); ffmpeg from PATH.

import argparse, glob, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")

def find_fluidsynth():
    hits = glob.glob(os.path.join(ROOT, "tools", "**", "fluidsynth.exe"), recursive=True)
    return hits[0] if hits else None

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(map(str,cmd))}\n{r.stdout[-800:]}{r.stderr[-800:]}")
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("calllist")
    ap.add_argument("--measures", default="measures.random2v.json")
    ap.add_argument("--bars", type=int)
    ap.add_argument("--no-melody", action="store_true")
    ap.add_argument("--barsecs", type=float, default=4.0)
    ap.add_argument("--duration", type=float, help="explicit song seconds (variable-length bars)")
    a = ap.parse_args()

    bars = a.bars or len(json.load(open(a.calllist, encoding="utf-8")))
    dur = a.duration or bars * a.barsecs
    os.makedirs(BUILD, exist_ok=True)
    drums = os.path.join(BUILD, f"{a.name}_drums.mid")

    exe = os.path.join(ROOT, "target", "release", "hnote.exe")
    if not os.path.exists(exe):
        run(["cargo", "build", "--release"])
    out = run([exe, "generate_midi_file", drums, str(dur), a.calllist, a.measures])
    print(out.strip().splitlines()[-1])

    final = f"{a.name}.mid"
    if a.no_melody:
        shutil.copy(drums, final)
    else:
        run([sys.executable, os.path.join(ROOT, "melody_layer.py"), drums, final, str(bars)])
    print("wrote", final)

    fs = find_fluidsynth()
    sf2 = os.path.join(ROOT, "tools", "GeneralUser-GS.sf2")
    if fs and os.path.exists(sf2):
        wav = os.path.join(BUILD, f"{a.name}.wav")
        run([fs, "-ni", "-F", wav, "-r", "44100", "-g", "0.7", sf2, final])
        run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame", "-q:a", "4", f"{a.name}.mp3"])
        print("wrote", f"{a.name}.mp3")
    else:
        print("audio tools missing - run setup_audio_tools.py for MP3 output")

if __name__ == "__main__":
    main()
