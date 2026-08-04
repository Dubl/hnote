# Apply a kit blob from kit.html: copy the chosen candidates into
# stack_samples/pNN.mp3. Usage: python apply_kit.py "hnote kit v1 kick=kick_1 ..."
# (Deep-house kit restore: python gen_stack_samples.py)
import re, shutil, subprocess, sys

MIDI = {"kick": 36, "clap": 38, "snare": 40, "hatc": 42,
        "hato": 46, "rim": 75, "crash": 49, "sub": 35}

def main():
    blob = sys.argv[1]
    picks = dict(re.findall(r"(\w+)=([\w-]+)", blob))
    picks.pop("v1", None)
    for slot, midi in MIDI.items():
        stem = picks.get(slot)
        if not stem:
            print(f"{slot}: no pick, leaving p{midi} as-is")
            continue
        src = f"kit_candidates/{stem}.mp3"
        dst = f"stack_samples/p{midi}.mp3"
        shutil.copyfile(src, dst)
        r = subprocess.run(["ffmpeg", "-loglevel", "info", "-i", dst,
                            "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True)
        vol = [l for l in r.stderr.splitlines() if "max_volume" in l]
        print(f"p{midi} <- {stem}  ({vol[0].split('] ')[-1] if vol else '?'})")
    print("kit applied to stack_samples/ - commit and push to go live")

if __name__ == "__main__":
    main()
