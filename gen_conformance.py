# Generate conformance vectors for STACK-ALGEBRA.md from the Python
# reference (apply_stack). Times are stored as exact integers x840 (pulse=1;
# every legal time has denominator dividing 840 = lcm 1..8). After this,
# conformance_check.js recomputes every vector with the JS reference sliced
# out of stack.html and appends dual-verified mix vectors - only agreement
# ships.
import json, sys
from apply_stack import parse_blob, realize_tab

AMEN_KICK = "motif=[1,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0]"
AMEN_SN = "motif=[0,0,0,0,7,0,0,-7,0,-7,0,0,7,0,0,-7]"

CASES = [
    ("cutoff-core", "hnote stack v1 pulse=1 periods=[16,9,5,3] motif=[2,1,1]"),
    ("child-basic", "hnote stack v1 pulse=1 periods=[12,5] motif=[1,3,2] child2=[S=2,m=[4,5]]"),
    ("child-rest-subphase", "hnote stack v1 pulse=1 periods=[10] motif=[2,1] child1=[S=3,m=[1,0,4],p=1]"),
    ("child-septuplet", "hnote stack v1 pulse=1 periods=[8] motif=[1,2] child2=[S=7,m=[3,0,-3]]"),
    ("ghosts-rests", "hnote stack v1 pulse=1 periods=[9] motif=[1,0,-7,3,0,-2]"),
    ("phase", "hnote stack v1 pulse=1 periods=[16,9,5,3] motif=[2,1,1] phase=7"),
    ("offset-slide", "hnote stack v1 pulse=1 periods=[4@5,16] motif=[1,0,7,0,3,1,-7,3,1,0,7,7,3,-7,0,1]"),
    ("offset-wrap", "hnote stack v1 pulse=1 periods=[4@14,16] motif=[1,0,7,0,3,1,-7,3,1,0,7,7,3,-7,0,1]"),
    ("offset-inner", "hnote stack v1 pulse=1 periods=[10,7@3] motif=[1,2,3,4]"),
    ("offset-plus-phase", "hnote stack v1 pulse=1 periods=[6@2,12] motif=[1,0,3,0,7,0,2,0,3,3,0,-7] phase=4"),
    ("lanes-cut-tile", "hnote stack v2 pulse=1 lane1={periods=[16] motif=[1,2,3]} "
                       "lane2={periods=[10] motif=[4,0]} lane3={periods=[24] motif=[5,0,0,-2]}"),
    ("lanes-operators", "hnote stack v2 pulse=1 lane1={periods=[12] motif=[1,0,2]} "
                        "lane2={periods=[4@5,16] motif=[3,0,3,0,3,0,3,0,6,0,3,0,3,0,3,0]} "
                        "lane3={periods=[9] motif=[0,7,-7] phase=2}"),
    ("amen-cell", f"hnote stack v2 pulse=1 lane1={{periods=[16] motif=[3,0]}} "
                  f"lane2={{periods=[16] {AMEN_KICK}}} lane3={{periods=[16] {AMEN_SN}}}"),
    ("amen-bar4-displaced", f"hnote stack v2 pulse=1 "
                            f"lane1={{periods=[16] motif=[3,0,3,0,3,0,3,0,6,0,3,0,3,0,3,0]}} "
                            f"lane2={{periods=[16] {AMEN_KICK} phase=14}} "
                            f"lane3={{periods=[16] {AMEN_SN} phase=14}}"),
    ("step-motif-cycle", "hnote stack v2 pulse=1 lane1={periods=[8] motif=[0,0,7,0]} "
                         "lane2={periods=[5@0+5] "
                         "motif=[1,0,0,0,0,1,0,0,-1,0,1,0,-1,0,0,1,-1,0,-1,0]}"),
    ("step-coprime", "hnote stack v1 pulse=1 periods=[4@0+3,16] "
                     "motif=[1,0,7,0,3,1,-7,3,1,0,7,7,3,-7,0,1]"),
    ("child-prenotes", "hnote stack v1 pulse=1 periods=[10] motif=[2,1] "
                       "child1=[S=4,m=[3,-3,1,0],p=0,pre=2]"),
    ("prenote-wrap-and-phase", "hnote stack v1 pulse=1 periods=[8] motif=[1,4] "
                               "child1=[S=3,m=[7,-7,2],pre=1] phase=3"),
    ("spillover", "hnote stack v1 pulse=1 periods=[10] motif=[1,0,3,0,0] "
                  "child3=[S=2,m=[7,-7,7,0,2]]"),
    ("spill-pre-wrap", "hnote stack v1 pulse=1 periods=[6] motif=[1,2,3] "
                       "child3=[S=3,m=[5,-5,5,5,-5],pre=1] phase=2"),
]

def x840(t, name):
    x = t * 840
    assert abs(x - round(x)) < 1e-6, (name, t)
    return int(round(x))

vectors = []
for name, blob in CASES:
    pulse, lanes = parse_blob(blob)
    assert pulse == 1.0
    hits, top = realize_tab(1.0, lanes)
    structures = [{"periods": p, "offs": o, "steps": st, "motif": m,
                   "children": {str(k): v for k, v in c.items()}, "phase": ph}
                  for (p, m, c, ph, o, st) in lanes]
    vectors.append({
        "name": name, "kind": "tab", "blob": blob, "pulse": 1,
        "lanes": structures, "bar840": top * 840,
        "hits": sorted([x840(t, name), p, v] for t, p, v in hits),
    })
    print(f"{name}: {len(vectors[-1]['hits'])} events, bar {top} pulses")

json.dump({"spec": "STACK-ALGEBRA.md v1", "scale": 840, "vectors": vectors},
          open("conformance.json", "w", encoding="utf-8"), indent=1)
print(f"wrote conformance.json ({len(vectors)} tab vectors; run conformance_check.js next)")
