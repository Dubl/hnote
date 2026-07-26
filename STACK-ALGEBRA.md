# The Stack Algebra — specification v1

An implementation-independent definition of the loop algebra developed in
HNote's Stack Sequencer (July 2026). Anything that satisfies this document
— any language, any engine — plays the same music from the same blobs.
Reference implementations: `stack.html` (JS), `apply_stack.py` (Python),
the HNote Rust engine via compiled share-trees. Conformance vectors:
`conformance.json` (see §8).

## 1. Objects

A **loop** is a pair (L, E): a length L > 0 in *pulses*, and a finite
multiset E of events (τ, s, w) with time τ ∈ [0, L) in pulses, sound s
(a positive integer), and weight w (an integer velocity 1–127 under the
default profile, §7). All times are exact rationals; every τ produced by
this algebra has a denominator dividing 840 (= lcm 1..8) per pulse.

A **pulse** π > 0 is a duration in seconds bound at render time
(π = 15/bpm treats a pulse as a sixteenth). The algebra is independent
of π; realized seconds are τ·π.

## 2. Stack expressions

A **stack** is:

    stack = ( periods  = [P₁ … Pₙ]      Pᵢ ≥ 2, outermost first (n ≥ 0)
            , offs     = [o₁ … oₙ]      oᵢ ≥ 0 (absent ⇒ 0)
            , motif    = [m₁ … m_k]     k ≥ 1, mᵢ ∈ {−V … V} (0 = rest,
                                        negative = ghost of |mᵢ|, V = voice count)
            , children = { i ↦ (S, m, p) }   for motif indices i (0-based):
                                        S ∈ 1..8 slot ticks, m a sub-motif of
                                        symbols as above, p ≥ 0 sub-phase
            , phase    = φ ≥ 0 )

A **tab** is a non-empty list of stacks [stack⁰ … stackᴸ] (L ≤ 3);
stack⁰ is the **ruler**.

## 3. Realization of one stack — realize(stack) = (top, E)

    top    = P₁ if n ≥ 1 else k
    fold(t) = ((…((t mod P₁ + o₁) mod P₂ + o₂)… mod Pₙ + oₙ)) mod k
    pos(t)  = (t − φ) mod top                      -- phase rotates OUTPUT position
    accent(t, mi) = 116 if t = 0 ; 102 if mi = 0 ; 88 otherwise   (profile §7)

For each t ∈ [0, top), with mi = fold(t):

  * if children[mi] = (S, m, p) exists (regardless of motif[mi]):
    for j ∈ [0, S): let σ = m[(j + p) mod |m|]. If σ ≠ 0, emit
        ( pos(t) + j/S,  |σ|,  52 if σ < 0
                               else accent(t,mi) if j = 0
                               else max(52, accent(t,mi) − 26) )
  * else let σ = motif[mi]. If σ ≠ 0, emit
        ( pos(t),  |σ|,  52 if σ < 0 else accent(t,mi) )

Notes. Offsets make each level read INTO the level below at position oᵢ,
wrapping at the next modulo — a small period on top plus its offset is a
sliding window over the level below (periods [4@5,16] plays elements
5–8 of the 16). Phase rotates the finished loop — accents travel with
content. Children restart on every visit (the tail of m beyond S is
silent unless sub-phase p slides it into reach).

## 4. Tabs (lanes) — realizeTab(tab) = (top⁰, E)

Let (top⁰, E⁰) = realize(stack⁰). For each lane i ≥ 1 with
(topⁱ, Eⁱ) = realize(stackⁱ): tile Eⁱ at b = 0, topⁱ, 2·topⁱ, …
emitting (b + τ, s, w) for every event while b + τ < top⁰ (strictly;
half-open). The tab's loop is E⁰ ∪ all tiled lane events, length top⁰.
Lanes longer than the ruler are cut; shorter lanes repeat and are cut
mid-tile — the cut-off principle applied vertically.

## 5. Mixes — realizeMix(tabs, wins, g)

Ground g is a tab index; wins an ORDERED list of windows (tab, a, b),
a < b in SECONDS (bind π first). Active windows: those with tab ≠ g and
a valid tab. winAt(x) = the FIRST active window with a ≤ x < b.

  * ground events (τ·π = x): kept iff winAt(x) = none
  * per active window w = (T, a, b): tile tab T's loop from 0 at its own
    length; keep tiled events x ∈ [a, b) with winAt(x) = w

The mix's length is the ground tab's length.

## 6. Sequences (chains / arrangement)

A **letter** denotes a loop: uppercase A… = a tab's loop; lowercase a… =
the mix grounded on that tab (with that ground's window list). A
**chain** is a word of letters = concatenation of their loops (each
letter contributes one full bar at its own length). An **arrangement**
is a sequence of chain references, concatenated likewise. Live
performance semantics (quantized injection, pre-emption) are an
operational layer above this algebra and are specified by the reference
implementation, not this document.

## 7. Default profile (conventions riding on the algebra, swappable)

  * Voices (V = 7): 1→36 kick, 2→38 clap, 3→42 closed hat, 4→46 open
    hat, 5→75 rim, 6→49 crash, 7→40 snare. MIDI channel 10.
  * Velocities: bar-start 116, motif-head 102, body 88, child tick
    decrement 26 (floor 52), ghost 52.
  * A conformant implementation may substitute profiles but must
    reproduce the default profile for conformance testing.

## 8. Notation (blob grammar) and conformance

    stack-blob  = "hnote stack" ("v1"|"v2") "pulse=" num body
    body(v1)    = lane-body                       -- single lane
    body(v2)    = "lane1={" lane-body "}" ["lane2={" lane-body "}" …]
    lane-body   = "periods=[" P("@"o)? ("," P("@"o)?)* "]"
                  "motif=[" int ("," int)* "]"
                  ("child" i "=[S=" S ",m=[" ints "]" (",p=" p)? "]")*
                  ("phase=" φ)? 
    mix-blob    = "hnote stackmix v1 pulse=" num ("base=" letter)?
                  (letter "={" body "}")+ "wins=[" (letter":"a"-"b)* "]"
    orch-blob   = "hnote orch v3 pulse=" num "motif=[" ints "]"
                  ("chain" i "=" letters)+ "q=" ("bar"|"pulse")
                  (letter "={" body "}")+ ("wins" letter "=[" … "]")*

`conformance.json` contains vectors {name, blob or structures, pulse: 1,
bar840, hits: [[τ·840, sound, vel] …]} with all τ·840 exact integers.
An implementation conforms iff it reproduces every vector's hit multiset
exactly. Vectors are dual-generated: computed by the Python reference and
independently recomputed by the JS reference; only agreement is recorded.

## 9. Laws (identities any implementation must satisfy)

  1. phase φ then φ′ ≡ phase (φ+φ′) mod top; phase top ≡ identity.
  2. offset composition: level offset o then o′ into span S ≡ (o+o′) mod S
     at realization (wrap at the next modulo).
  3. window = offset ∘ cut: periods [W@a, S, …] realizes the slice
     [a, a+W) (mod S) of the loop below — no separate crop operator.
  4. A period equal to the span below with offset 0 is an identity level.
  5. A tab with only its ruler ≡ the ruler stack.
  6. Chain concatenation is associative; the empty chain is not
     representable (chains have ≥ 1 letter).
  7. A mix with no active windows ≡ its ground tab.
  8. Rest symbols and cut/tiling commute: silence needs no special case.
