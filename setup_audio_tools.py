# One-time fetch of the audio tools into ./tools/ (gitignored):
#   - FluidSynth (win64) for MIDI -> WAV
#   - GeneralUser GS soundfont
# ffmpeg is expected on PATH (or edit FFMPEG in build_track.py).
# Usage: python setup_audio_tools.py

import io, json, os, urllib.request, zipfile

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")

def fetch(url):
    print("fetching", url)
    with urllib.request.urlopen(url) as r:
        return r.read()

def main():
    os.makedirs(TOOLS, exist_ok=True)
    sf2 = os.path.join(TOOLS, "GeneralUser-GS.sf2")
    if not os.path.exists(sf2):
        open(sf2, "wb").write(fetch(
            "https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/GeneralUser-GS.sf2"))
    rel = json.loads(fetch(
        "https://api.github.com/repos/FluidSynth/fluidsynth/releases/latest").decode())
    url = next(a["browser_download_url"] for a in rel["assets"]
               if "win10-x64" in a["name"] and a["name"].endswith(".zip"))
    if not any(n.startswith("fluidsynth") for n in os.listdir(TOOLS)):
        zipfile.ZipFile(io.BytesIO(fetch(url))).extractall(os.path.join(TOOLS, "fluidsynth"))
    # locate the exe
    for root, _, files in os.walk(TOOLS):
        if "fluidsynth.exe" in files:
            print("fluidsynth at", os.path.join(root, "fluidsynth.exe"))
    print("soundfont at", sf2)

if __name__ == "__main__":
    main()
