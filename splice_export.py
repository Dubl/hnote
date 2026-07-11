# Export the pure polyrhythm measures into splice_data.js for splice.html.
# Each beat: name, ratio label, and its flat hit list [t, midi, vel] over the
# 8s measure (computed with the standard layout walk).

import json

BAR = 8.0
RATIOS = [(2,3),(3,4),(4,5),(5,6),(2,5),(3,5),(4,7),(5,7),(3,7),(5,9),
          (2,3,4),(3,4,5),(4,5,6),(2,5,7),(3,5,7),(4,6,9)]

def walk(n, start, end, out):
    if n.get("midi_number"): out.append((start, n["midi_number"], n.get("velocity", 0)))
    kids = n.get("children") or []
    if not kids: return
    if n.get("child_direction") == "sidebyside":
        for c in kids: walk(c, start, end, out)
    else:
        tot = sum(c.get("timing", 0.0) for c in kids)
        cur = start
        for j, c in enumerate(kids):
            ce = end if j == len(kids) - 1 else cur + (end - start) * c.get("timing", 0.0) / tot
            walk(c, cur, ce, out)
            cur = ce

def main():
    data = json.load(open("measures.polytest.json", encoding="utf-8"))
    byname = {m.get("name"): m for m in data}
    beats = []
    for i, r in enumerate(RATIOS, 1):
        hits = []
        walk(byname[f"ptest{i}"], 0.0, BAR, hits)
        beats.append({"name": f"ptest{i}",
                      "ratio": ":".join(map(str, sorted(r))),
                      "hits": [[round(t, 4), p, v] for t, p, v in sorted(hits) if p]})
    payload = {"barlen": BAR, "beats": beats}
    with open("splice_data.js", "w", encoding="utf-8") as f:
        f.write("const SPL = " + json.dumps(payload) + ";\n")
    print(f"{len(beats)} beats exported, {sum(len(b['hits']) for b in beats)} hits")

if __name__ == "__main__":
    main()
