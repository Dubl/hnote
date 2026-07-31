# HNote — working notes for Claude

HNote is a recursive, ratio-based music representation (see `variation
spec.md`). Long-term goal: the **driver** — hold an invariant at any altitude
of the tree, regenerate below it. The listen → tag → edit → regenerate loop
shipped in July 2026 (tracks 1–6 on the Pages site).

## The loop, end to end

1. **Generate/compose**: measures JSON (beats + roll measures) + calllist
   JSONC (1 `once` call = 1 bar = 4.0s; chain `{"function":"roll","target":...}`
   to attach a roll to that bar).
2. **Build**: `python build_track.py <name> <calllist> [--measures FILE]
   [--no-melody]` → renders drums via the Rust engine, layers the Glass
   melody (`melody_layer.py`, deterministic), renders MP3 via `tools/`
   (one-time: `python setup_audio_tools.py`; ffmpeg on PATH).
3. **Publish**: card in `index.html` (MP3 `<audio preload=none>` + lazy
   `<midi-player data-src=...>` — NEVER eager-load players or add
   `midi-visualizer`, both crash phones). Point `tag.html`'s audio src at the
   new MP3. `git add -f` any `.json`/`.jsonc` (gitignored by default), push,
   then poll `https://dubl.github.io/hnote/<file>` until Content-Length
   matches local.
4. **Tag**: user listens on `tag.html`, pastes the tag blob in chat.
5. **Edit**: `python bar_export.py <unit> <bar>` surfaces a bar into
   `edit.html` (nudge onsets, crop loop, mute roll; gapless Web Audio
   looper). User pastes the edit blob; `python apply_edits.py <blob.txt>`
   applies + re-renders + closed-loop verifies. `crops.json` sidecar stores
   pristine copies (crop is absolute, not cumulative; nudges scale with crop).

## Architecture facts that everything rests on

- Sequential children lay out by **normalized shares**
  (`layout_children_sequentially_in_range`, src/types.rs). Onset k is the
  boundary between siblings k−1 and k → `share[k-1]+=d, share[k]-=d` moves
  exactly one onset. First-child onsets can only be delayed (leading rest).
- **Loop length = share mass**: trim trailing shares → pattern stretches in
  its unchanged 4s slot; append trailing rest → compresses.
- Rolls are prechildren anchored at bar end (anchor #6 hardcoded in
  Call::Roll; anchor slot STARTS at bar end). Erasure window =
  [pc0.start, pc[eos−1].start); `overwrite_whitelist` passes through (hats
  [42,46] by convention; whitelist 35..81 = non-silencing roll);
  `ancestor_overwrite_level: 2` + `end_of_silence_prechild: 8` = erasure past
  the bar line. Mute a roll = zero prechildren + whitelist 35..81 (data only).
- **Splice pattern** (discovered 2026-07-10, splicetest.*): a roll can start
  AND end mid-parent — prechildren `[content, trailing rest, 0-width pads,
  anchor]` with `end_of_silence_prechild` aimed at the trailing rest. The
  erasure window equals the content span; the base resumes at the window's
  half-open end. "Overwrite section [a,b) of beat A with a slice of beat B"
  is therefore pure data: content = B's slice sized (b-a), trailing rest =
  bar_end - b. Verified exact (0 leaked, boundary hits survive).
- Beat measure shape: sidebyside root, 3–4 sequential lanes (kick/snare lane
  carries `"rolled": true`), flat cells with uniform shares, rests explicit.

## Verification norms (non-negotiable)

- Machine-verify every render before pushing: predicted onsets ±2ms (MIDI
  tick ≈ 1.04ms), tolerance **multiset** matching (never exact-rounding or
  order-sensitive comparison), changes confined to the edited scope.
- The canonical Levee render is the engine regression gate: re-render
  `calllist.jsonc` + `measures.json` (452.174s) → must match
  `WhenTheLeveeBreaks.mid` 1748/1748. Run it after ANY engine change.
- Derive selection lists from pristine/pre-rewrite data — classifying
  measures by content after a rewrite has polluted its own criterion twice.
- Edit at the right altitude; never regenerate what should be edited in
  place (a regeneration once destroyed per-beat variety the user valued).

## File map (song 1 era)

- Engine: `src/` (`generate_midi_file <out> <secs> <calllist> <measures>`).
- Canonical: `measures.json`, `calllist.jsonc`, `levee_*.mid` — immutable.
- Song 1 lineage: `measures.random2g.json` (rich) → `measures.random2v.json`
  (spillover + all editor state) with `calllist.track{2..6}.jsonc`,
  `track{n}.mid/.mp3`. Good beats (track-5 tags): riders
  14,19,34,36,38,44,59,62,67,72,73,87,94,98,99; transitions
  17,24,26,27,30,45,51,55,65,70,76,78,82,85,91,93,100.
- Tooling: `hnote_edit_lib.py`, `bar_export.py`, `apply_edits.py`,
  `edit.html`, `tag.html`, `melody_layer.py`, `build_track.py`,
  `setup_audio_tools.py`. **Stack sequencer** (the cut-off core as pure
  numbers): `stack.html` composes periods+motif+element-children; its Copy
  Stack blob compiles via `apply_stack.py "<blob>" --name <n>` into a nested
  HNote tree (realization = fold through nested moduli, restart semantics),
  rendered + verified automatically. stack.html v4 has an **ORCH layer** with
  NO cutoff mechanism (redundant at arrangement scale — Jon composes the
  sequence directly): symbols are **chains** = phrases of uberloop bars
  (1=ABA; letters A–D = tabs, M = mix; each letter plays ONE full bar of that
  uberloop at its own length — variable lengths compose, all boundaries stay
  on the 0.25s grid because bar lens are dyadic). Orch motif (≤32 spots) =
  sequence of chain numbers. Live tap on a chain = **inject then resume**
  (chain plays once at the next boundary — quantize bar/pulse — then the
  written motif continues where it was headed; a tap mid-injection pre-empts).
  Sub-motif symbol 0 = rest. Per-uberloop **phase** (the pulse the loop
  starts on; rotation, accents travel with content; blob `phase=N`, compiled
  as [drop_unit tail, trim_unit head]). Per-child **sub-motif phase** `p`
  (index offset `m[(j+p)%|m|]`; cell accent stays positional; blob
  `childN=[S=…,m=[…],p=…]`; when |m|>S, p selects which slice of m sounds).
  Tabs go up to 8 (A–H; chain alphabet A–H + a–h). **The vertical axis**
  (state v6): a tab = chord of stacks — primary + up to 3 `lanes`, each a
  full {motif,periods,children,phase}; lane 1 is the ruler, others tile and
  are CUT at its bar (realizeTabHits). Signed symbols: negative = ghost
  (vel 52), 0 = rest at motif level too; motif cap 32. Global `pulse`
  (BPM stepper; 15/bpm = pulse-as-16th). **Per-level offsets** (`offs[k]`
  per period, ‹ › steppers): each level reads INTO the level below at
  offset o — fold becomes `x = x%P + o` per level, wrap at the next
  modulo. A small period on top + its offset = a sliding window over the
  beat (4@5 over 16 = elements 5–8), Jon's window concept done natively
  (the bolt-on `win` operator was built then REVERTED in favor of this).
  Blob: `periods=[4@5,16]`; compiled as per-level unit rotation
  (drop+trim before reps). **Stepping offsets** (`steps[k]`, blob `P@o+Δ`,
  the +Δ button per period row): o(b)=o+b·Δ per bar — the loop cycles
  through the level below; tab loop = full cycle (C = lcm of
  span/gcd(Δ,span) per level), letter/mix lengths follow. Jon's
  "cycle the motifs over four uberloops" without duplication: variants
  side by side in one motif, `5@0+5` selects the next window each bar.
  **Timeline / ornaments** (state v7): one-offs are TIMELINE citizens, not
  loop citizens (lane-modes over/mask were built then REVERTED on this
  insight). Chains hold ≤4 letters ("phrases", convention) and carry
  `orns`: one-offs at STRUCTURAL addresses {li,bar,u} with act
  add/mute/ghost + signed sym — applied to that chain's occurrence only;
  underlying loops stay pristine; ⧉ copies a chain WITH its one-offs.
  Tap a chain number while stopped = its timeline view (every address,
  base content as faint dots, ° marks ornamented chains in the realized
  string); while playing = inject (unchanged). Blob `hnote orch v4 …
  ornN=[li.bar.u:s|-s|xS|~S,…]`. Ornaments are score-layer, outside the
  loop algebra (spec §6). Ornament adds may carry a sub-motif cell (burst,
  blob `*S;m;p;pre`). **Prenotes** (`pre` on any sub-motif cell, child or
  burst): the first `pre` ticks lead INTO the anchor (anchor tick takes
  the accent; pickups wrap to the bar/letter end) — the tree's
  prechildren concept rediscovered. **Spillover** (2026-07-30): when
  |m| > S the extra notes EXTEND past the cell at the tick rate (union,
  no erasure; wrap at bar/letter) — pre reaches backward, spill forward.
  Both compiled as parallel OVERFLOW LANES (sidebyside siblings, greedy
  packing; closed-loop verified incl. steps+phase). **Copy setup / Load
  setup**: Copy emits the ENTIRE configuration as `hnote setup v7 {json}`
  (the persisted state IS the format); Load pastes any-version state
  through migrateFrom (validates+clamps; stops playback first).
  apply_stack accepts setup blobs directly (`--tab A` picks the tab).
  The old per-view blobs remain emittable but the setup blob is primary.
  Kit + SOUNDS grew: 49 crash 'C',
  40 snare 'N' (7 voices). Blob `hnote stack v2 … lane1={…} lane2={…}`.
  apply_stack compiles lanes to a sidebyside root (the canonical beat
  shape) and now compiles the ACCENT RULE into the tree (116 bar-start
  patched pre-rotation, 102 mi=0, 88 else; verification includes
  velocities — flat-96 divergence found and fixed 2026-07-25).
  **STACK-ALGEBRA.md** = the distilled spec (objects, realize equations,
  blob grammar, laws, default profile); `conformance.json` = 16 vectors,
  times as exact ×840 integers at pulse=1, DUAL-generated
  (gen_conformance.py = Python reference, conformance_check.js recomputes
  via sliced page JS + adds mix vectors; only agreement ships). Any new
  implementation of the algebra must reproduce the vectors exactly.
  `amen_test.py` = acceptance test: the Amen break as 3 tabs (bar 4 = lane
  phase 14 displacement), 136 bpm, verified onset+pitch+velocity vs the
  transcription table; amen_kit.mp3 on the index.
  **Per-base mixes** (`winsBy`, state v5): EVERY tab has its own mix (own
  window layout, ground = that tab). MIX view's ground chips pick which mix
  you're editing (`wins` is bound to `winsBy[mixBase]`). Chain letters:
  A–D = plain uberloop bar, **a–d = that base's MIX bar** (M is gone;
  migrated to lowercase of the old base). Windows aimed at their own ground
  are inert. Orch blob v3 carries `winsA=[…] winsB=[…]` per non-empty base. Engine verified by `orch_sim.js` (slices the
  shipped PURE-STATE/realization/ORCH-CORE regions out of stack.html — run it
  after ANY stack.html engine change). Orch blob `hnote orch v2 …`
  (apply_orch.py compiler = follow-up). Drum kit = synthesized 808/909
  `stack_samples/` (gen_stack_samples.py; voices 36/38/42/46/75). NOTE: `bar_export.py` maps unit→beat via track-3's
  cycle [70,87,96,98]; for other beats pass the unit that maps to the beat
  you want, or generalize it.
- Memory: `~/.claude/projects/.../memory/` has project state + what the
  project means to the user.

## New-song convention

Name things `measures.<song>.json`, `calllist.<song>.<track>.jsonc`,
`<song>_t<n>.mid/.mp3`. Start from a fresh beat generator (per-beat rng
seeds, multi-voice walkers with uneven shares — see the roll engines
described in git history around "Complexify"/"scatter-to-snare"), publish a
browsing render, tag, curate, refine.
