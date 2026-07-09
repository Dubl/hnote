# Surface one bar of track 3 into the timing editor.
# Usage: python bar_export.py <unit 1-37> <bar 1-4>
# Writes edit_data.js for edit.html and prints a summary.

import json, sys
from hnote_edit_lib import (BAR, beat_hits, roll_layout, container_at,
                            container_children_spans, path_str)

BEAT_CYCLE = [70, 87, 96, 98]

def main():
    unit, bar = int(sys.argv[1]), int(sys.argv[2])
    beat_no = BEAT_CYCLE[(unit - 1) % 4]
    beat_name, roll_name = f"rbeat{beat_no}", f"rroll{beat_no}_{bar}"
    data = json.load(open("measures.random2v.json", encoding="utf-8"))
    byname = {m.get("name"): m for m in data}
    beat, roll = byname[beat_name], byname[roll_name]

    bhits = beat_hits(beat)
    rhits, _, window = roll_layout(roll)
    wl = set(roll.get("overwrite_whitelist") or [])
    lo, hi = window

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

    n_erased = 0
    for h in bhits:
        if lo <= h["onset"] < hi and h["midi"] not in wl:
            n_erased += 1
            continue                       # erased by the roll; not sounding
        add(h, beat_name, beat)
    n_spill = 0
    for h in rhits:
        if h["onset"] >= BAR - 1e-9:
            n_spill += 1
            continue                       # spill/anchor lands in the next bar
        add(h, roll_name, roll)

    payload = {"unit": unit, "bar": bar, "beat": beat_name, "roll": roll_name,
               "barlen": BAR, "hits": hits}
    with open("edit_data.js", "w", encoding="utf-8") as f:
        f.write("const EDIT = " + json.dumps(payload) + ";\n")
    print(f"exported u{unit} b{bar}: beat {beat_name} + roll {roll_name}")
    print(f"  {len(hits)} editable hits ({n_erased} base hits erased by roll, "
          f"{n_spill} roll hits beyond the bar excluded)")
    print(f"  erasure window [{lo:.3f}, {hi:.3f})s, whitelist {sorted(wl)[:4]}{'...' if len(wl)>4 else ''}")

if __name__ == "__main__":
    main()
