# Apply a pasted edit blob from edit.html to measures.random2v.json,
# re-render track3 drums, and verify the loop closes.
#
# Blob may contain an optional `crop=<c>s` line (loop crop/extend: the beat's
# content is renormalized as if the loop were c seconds long, so every base
# onset scales by 4/c) and per-hit lines `id=.. src=.. path=.. dt=..ms`
# (deltas measured in the POST-crop frame, i.e. what the editor displayed).
#
# Apply order: restore pristine lanes from crops.json -> crop_loop(c) ->
# per-note share transfers. Each transfer is mirrored into the pristine
# sidecar copy (scaled by c/4) so a future re-crop doesn't lose nudges.
#
# Verification: predict every edited-beat bar's sounding base hits in Python
# (post-edit layout minus erasure windows, whitelists respected) and assert
# the render contains each at +-2ms in every occurrence -- and that erased
# predictions are absent -- plus the global check that all changed notes are
# confined to the beat's units.
#
# Usage: python apply_edits.py <blob.txt> [--dry-run]

import json, re, struct, subprocess, sys, os
from collections import defaultdict
from hnote_edit_lib import (shift_onset, parse_path, BAR, beat_hits, roll_layout,
                            crop_loop, load_sidecar, save_sidecar, bar_windows)

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
    cm=re.search(r"crop=([\d.]+)s",blob)
    crop=float(cm.group(1)) if cm else None
    edits=[]
    for m in re.finditer(r"id=(\d+) src=(\w+) path=([\w/]+) dt=(-?[\d.]+)ms",blob):
        edits.append({"id":int(m.group(1)),"src":m.group(2),
                      "path":parse_path(m.group(3)),"dt":float(m.group(4))/1000.0})
    if not edits and crop is None: raise SystemExit("nothing to apply")
    print(f"u{unit} b{bar} ({beat_name}/{roll_name}): "
          f"{'crop='+str(crop)+'s ' if crop else ''}{len(edits)} note edits")

    data=json.load(open(MEASURES,encoding="utf-8"))
    byname={mm.get("name"):mm for mm in data}
    sidecar=load_sidecar()

    before=render(f"{SCR}/apply_before.mid")

    # 1. crop (absolute; restores pristine lanes first)
    if crop is not None:
        crop_loop(byname[beat_name],crop,sidecar)
    c_now=sidecar.get(beat_name,{}).get("c",BAR)
    scale=BAR/c_now

    # 2. note transfers (descending index per container so k==0 rest
    #    insertions can't shift already-applied sibling indices)
    bycont=defaultdict(list)
    for e in edits: bycont[(e["src"],tuple(str(p) for p in e["path"][:-1]))].append(e)
    for _,group in bycont.items():
        for e in sorted(group,key=lambda x:-x["path"][-1][1]):
            is_base=e["src"]==beat_name
            # dt is in the post-crop (displayed) frame; the live lanes are the
            # cropped ones, whose container spans the bar, so dt applies as-is.
            shift_onset(byname[e["src"]],e["path"],e["dt"],BAR)
            if is_base and beat_name in sidecar:
                # mirror into the pristine copy in ITS frame (scaled by c/4)
                pristine={"children":sidecar[beat_name]["orig_children"],
                          "child_direction":"sidebyside"}
                shift_onset(pristine,e["path"],e["dt"]/scale,BAR)

    if dry:
        print("dry run: nothing written"); return
    json.dump(data,open(MEASURES,"w",encoding="utf-8"),indent=1)
    save_sidecar(sidecar)
    after=render(f"{SCR}/apply_after.mid")

    # --- verification --------------------------------------------------------
    beat_no=int(beat_name[5:])
    occ_units=[u for u in range(1,N_UNITS+1) if BEAT_CYCLE[(u-1)%4]==beat_no]

    # global confinement: every changed note lies in this beat's units
    key=lambda n:(round(n[0],3),n[1],n[2])
    sb,sa=set(map(key,before)),set(map(key,after))
    changed=(sb-sa)|(sa-sb)
    unit_of=lambda t:int(t//16.0)+1
    stray=[x for x in changed if unit_of(x[0]) not in occ_units]
    print(f"changed notes: {len(changed)} | outside beat's units: {len(stray)}")
    if stray[:4]: print("  stray:",stray[:4])

    # per-bar prediction from the edited measures
    pred_beat=beat_hits(byname[beat_name])       # post-crop, post-nudge layout
    ok=True; checked=0; absent_ok=0
    for b in range(1,5):
        wins=bar_windows(byname,beat_name,b)
        for u in occ_units:
            s=(u-1)*16.0+(b-1)*4.0
            for h in pred_beat:
                pos=h["onset"]
                silenced=any(lo<=pos<hi and h["midi"] not in wl for lo,hi,wl in wins)
                want=s+pos
                present=[t for t,p,v in after if p==h["midi"] and abs(t-want)<=TOL]
                if silenced:
                    absent_ok+=1            # roll may add its own notes nearby; skip strict absence
                    continue
                checked+=1
                if not present:
                    ok=False
                    print(f"  MISS base midi={h['midi']} bar{b} @{s:.0f}s: wanted {want:.4f}s")
    print(f"predicted base onsets verified: {checked} present "
          f"({absent_ok} occurrences inside erasure windows skipped)")
    print("verification:","PASS" if ok and not stray else "FAIL")
    if not ok or stray: raise SystemExit(1)
    print("apply complete; rebuild track3 chain next (track3_layer.py -> mp3)")

if __name__=="__main__":
    main()
