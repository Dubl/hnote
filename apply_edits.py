# Apply a pasted edit blob from edit.html to measures.random2v.json,
# re-render track3 drums, and verify the loop closes: every edited onset lands
# at its target (+-2ms, MIDI tick resolution) in EVERY occurrence of the beat,
# and every other onset in the track is unchanged.
#
# Usage: python apply_edits.py <blob.txt> [--dry-run]
# The blob is the clipboard text from edit.html's "Copy edits".

import json, re, struct, subprocess, sys, os
from collections import defaultdict
from hnote_edit_lib import shift_onset, parse_path, BAR

SCR = os.environ.get("HNOTE_SCRATCH",
    r"C:/Users/Jon/AppData/Local/Temp/claude/c--Users-Jon-hello-rust/74145bec-53c1-49e9-91f2-ffec1255555d/scratchpad")
MEASURES = "measures.random2v.json"
CALLS = "calllist.track3.jsonc"
BEAT_CYCLE = [70, 87, 96, 98]
N_UNITS = 37
TOL = 0.0021

def parse_mid(path):
    d=open(path,"rb").read(); ppq=struct.unpack(">H",d[12:14])[0]
    i=d.index(b"MTrk")+8; end=i+struct.unpack(">I",d[i-4:i])[0]
    t=0;tempo=500000;on=[];run=None
    while i<end:
        dv=0
        while True:
            b=d[i];i+=1;dv=(dv<<7)|(b&0x7f)
            if not b&0x80:break
        t+=dv;b=d[i]
        if b==0xFF:
            mt=d[i+1];ln=d[i+2]
            if mt==0x51:tempo=int.from_bytes(d[i+3:i+3+ln],"big")
            i+=3+ln;run=None
        elif b in(0xF0,0xF7):i+=2+d[i+1];run=None
        else:
            if b&0x80:st=b;i+=1;run=st
            else:st=run
            if st&0xF0 in(0x80,0x90,0xA0,0xB0,0xE0):
                d1,d2=d[i],d[i+1];i+=2
                if st&0xF0==0x90 and d2>0:on.append((t*tempo/ppq/1e6,d1,d2))
            else:i+=1
    return on

def render(out):
    r=subprocess.run(["./target/release/hnote.exe","generate_midi_file",out,
                      str(N_UNITS*16.0),CALLS,MEASURES],capture_output=True,text=True)
    if r.returncode!=0: raise SystemExit("render failed:\n"+r.stdout[-500:]+r.stderr[-500:])
    return parse_mid(out)

def main():
    blob=open(sys.argv[1],encoding="utf-8").read()
    dry="--dry-run" in sys.argv
    head=re.search(r"\(u(\d+) b(\d+), beat (\w+), roll (\w+)\)",blob)
    if not head: raise SystemExit("bad blob header")
    unit,bar,beat_name,roll_name=int(head.group(1)),int(head.group(2)),head.group(3),head.group(4)
    edits=[]
    for m in re.finditer(r"id=(\d+) src=(\w+) path=([\w/]+) dt=(-?[\d.]+)ms",blob):
        edits.append({"id":int(m.group(1)),"src":m.group(2),
                      "path":parse_path(m.group(3)),"dt":float(m.group(4))/1000.0})
    if not edits: raise SystemExit("no edits in blob")
    print(f"{len(edits)} edits for u{unit} b{bar} ({beat_name} / {roll_name})")

    data=json.load(open(MEASURES,encoding="utf-8"))
    byname={mm.get("name"):mm for mm in data}

    # expected onsets BEFORE edits, from the export math (source of truth for targets)
    from hnote_edit_lib import beat_hits, roll_layout
    bh={tuple(h["path"]):h for h in beat_hits(byname[beat_name])}
    rh={tuple(h["path"]):h for h in roll_layout(byname[roll_name])[0]}
    for e in edits:
        base=(bh if e["src"]==beat_name else rh).get(tuple(e["path"]))
        if base is None: raise SystemExit(f"edit path not found: {e}")
        e["target_pos"]=base["onset"]+e["dt"]  # position within the bar
        e["midi"]=base["midi"]

    before=render(f"{SCR}/apply_before.mid")

    # group per (measure, container) and apply in descending child index so a
    # k==0 rest insertion can't invalidate earlier-applied sibling paths
    bycont=defaultdict(list)
    for e in edits: bycont[(e["src"],tuple(str(p) for p in e["path"][:-1]))].append(e)
    for _,group in bycont.items():
        for e in sorted(group,key=lambda x:-x["path"][-1][1]):
            shift_onset(byname[e["src"]],e["path"],e["dt"],BAR)

    if dry:
        print("dry run: measures not written"); return
    json.dump(data,open(MEASURES,"w",encoding="utf-8"),indent=1)
    after=render(f"{SCR}/apply_after.mid")

    # --- closed-loop verification -------------------------------------------
    # Beat edits are pattern-wide: the hit moves in EVERY bar of every unit
    # playing this beat. Roll edits occur only in bar `bar` of those units.
    beat_no=int(beat_name[5:])
    occ_units=[u for u in range(1,N_UNITS+1) if BEAT_CYCLE[(u-1)%4]==beat_no]
    def occ_starts(src):
        if src==beat_name:
            return [(u-1)*16.0+b*4.0 for u in occ_units for b in range(4)]
        return [(u-1)*16.0+(bar-1)*4.0 for u in occ_units]
    key=lambda n:(round(n[0],3),n[1],n[2])
    sb,sa=set(map(key,before)),set(map(key,after))
    changed=(sb-sa)|(sa-sb)
    allowed=set()
    for e in edits:
        for s in occ_starts(e["src"]): allowed.add(s)
    def in_occ(t): return any(s-0.01<=t<s+BAR+1.0 for s in allowed)
    stray=[x for x in changed if not in_occ(x[0])]
    print(f"changed notes: {len(changed)} | outside edited-source bars: {len(stray)}")
    if stray[:4]: print("  stray:",stray[:4])
    # presence-matched: wherever the hit sounded before (some occurrences are
    # erased by that bar's roll), expect it at the target after
    ok=True; checked=0
    for e in edits:
        for s in occ_starts(e["src"]):
            had=[t for t,p,v in before if p==e["midi"]
                 and abs(t-(s+e["target_pos"]-e["dt"]))<=TOL]
            if not had: continue           # erased in this occurrence
            checked+=1
            want=s+e["target_pos"]
            hit=[t for t,p,v in after if p==e["midi"] and abs(t-want)<=TOL]
            if not hit:
                ok=False
                print(f"  MISS id={e['id']} midi={e['midi']} occurrence @{s:.0f}s: wanted {want:.4f}s")
    print(f"landed on target in {checked} occurrences checked")
    print("verification:", "PASS" if ok and not stray else "FAIL")
    if not ok or stray: raise SystemExit(1)
    print("apply complete; rebuild track3 chain next (track3_layer.py -> mp3)")

if __name__=="__main__":
    main()
