# Surface one bar of track 3 into the timing editor.
# Usage: python bar_export.py <unit 1-37> <bar 1-4>
# Writes edit_data.js for edit.html and prints a summary.
#
# Hits are exported from the beat's PRISTINE (pre-crop) lanes; the active
# crop c is exported separately and the editor applies it as a view
# transform (displayed onset = original * bar/c). Erasure windows are
# exported so the editor can ghost/drop silenced hits client-side.

import json, sys, copy
from hnote_edit_lib import (BAR, beat_hits, roll_layout, container_children_spans,
                            path_str, load_sidecar, bar_windows)

BEAT_CYCLE = [70, 87, 96, 98]

def main():
    unit, bar = int(sys.argv[1]), int(sys.argv[2])
    beat_no = BEAT_CYCLE[(unit - 1) % 4]
    beat_name, roll_name = f"rbeat{beat_no}", f"rroll{beat_no}_{bar}"
    data = json.load(open("measures.random2v.json", encoding="utf-8"))
    byname = {m.get("name"): m for m in data}
    beat, roll = byname[beat_name], byname[roll_name]

    sidecar = load_sidecar()
    crop = sidecar.get(beat_name, {}).get("c", BAR)
    pristine = copy.deepcopy(beat)
    if beat_name in sidecar:
        pristine["children"] = copy.deepcopy(sidecar[beat_name]["orig_children"])

    bhits = beat_hits(pristine)
    rhits, _, _ = roll_layout(roll)
    wins = bar_windows(byname, beat_name, bar)

    hits = []
    def add(h, src, measure):
        cpath = h["path"][:-1]
        k = h["path"][-1][1]
        spans = container_children_spans(measure, cpath)
        earlier = None if k == 0 else spans[k - 1][0] + 0.002
        later = spans[k][1] - 0.002
        hits.append({
            "id": len(hits), "src": src, "path": path_str(h["path"]),
            "midi": h["midi"], "vel": h["vel"],
            "onset": round(h["onset"], 5),
            "min": None if earlier is None else round(earlier, 5),
            "max": round(later, 5),
        })

    for h in bhits:
        add(h, beat_name, pristine)      # windows applied client-side (crop-aware)
    n_spill = 0
    for h in rhits:
        if h["onset"] >= BAR - 1e-9:
            n_spill += 1
            continue
        add(h, roll_name, roll)

    payload = {"unit": unit, "bar": bar, "beat": beat_name, "roll": roll_name,
               "barlen": BAR, "crop": crop,
               "windows": [[round(lo, 5), round(hi, 5), sorted(wl)] for lo, hi, wl in wins],
               "hits": hits}
    with open("edit_data.js", "w", encoding="utf-8") as f:
        f.write("const EDIT = " + json.dumps(payload) + ";\n")
    print(f"exported u{unit} b{bar}: beat {beat_name} (crop {crop}s) + roll {roll_name}")
    print(f"  {len(hits)} hits ({n_spill} roll hits beyond the bar excluded)")
    for lo, hi, wl in wins:
        print(f"  erasure window [{lo:.3f}, {hi:.3f})s, whitelist {sorted(wl)[:4]}{'...' if len(wl) > 4 else ''}")

if __name__ == "__main__":
    main()
