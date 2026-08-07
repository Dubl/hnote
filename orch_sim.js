// Verification harness for stack.html's ORCH engine (v2: chains of uberloop bars).
// Slices the SHIPPED code (PURE-STATE + realization + ORCH-CORE markers) out of
// the html, runs it in a vm with a mocked jittered clock, and asserts the hit
// set + letter timeline against an independently-expanded oracle.
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, 'stack.html'), 'utf8');

function slice(a, b) {
  const i = html.indexOf(a), j = html.indexOf(b);
  if (i < 0 || j < 0) throw new Error('marker missing: ' + a);
  return html.slice(i + a.length, j);
}
const pureState = slice('/* PURE-STATE-BEGIN */', '/* PURE-STATE-END */');
const pure      = slice('// --- realization ---', '// --- tabs ---');
const core      = slice('/* ORCH-CORE-BEGIN */', '/* ORCH-CORE-END */');

const PREAMBLE = `
let stacks=[], wins=[], winsBy=[[],[],[],[]], dirty=true, hits=[], looplen=0;
let t0=0, schedUntil=0, segStart=0, oQueue=null, q='bar', mixBase=0;
let orch=null, orchCache=null;
let wi=0, inj=null, activeChain=0, curLetter='A', curLen=1, curHits=[];
let phLog=[];
let breath=null, cycLen=0, cycPhase=0, curPhase0=0, curDelta0=0, curWarpLen=1, curRate=1, curInj=false;
`;
const EPILOGUE = `
__api.buildCache = () => {
  orchCache=buildOrchCache(); cycLen=orchCache.cycLen;
  if(wi>=orchCache.seq.length) wi=0;
  const e=orchCache.seq[(wi-1+orchCache.seq.length)%orchCache.seq.length];
  if(e&&e.L===curLetter){ curHits=e.hits; curLen=e.len;
    curWarpLen=curInj?curRate*curLen:curLen+breathDelta(curPhase0+curLen)-curDelta0; }
};
__api.init = (o) => { stacks=o.stacks; winsBy=o.winsBy||[[],[],[],[]]; orch=o.orch; q=o.q; t0=o.t0;
  PULSE=o.pulse||0.25; breath=o.breath||null;
  materializeComposites();
  mixBase=o.mixBase||0; wins=winsBy[mixBase]||[];
  schedUntil=t0; wi=0; inj=null; oQueue=null; cycPhase=0;
  orchCache=buildOrchCache(); cycLen=orchCache.cycLen;
  advance(t0); };
__api.materialize = () => materializeComposites();
__api.tap = (i) => { oQueue=i; };
__api.get = () => ({t0, schedUntil, segStart, wi, inj: inj?{idx:inj.idx,n:inj.list.length}:null,
  oQueue, curLetter, curLen, activeChain, q});
__api.call = (now, until) => scheduleOrch(now, until);
__api.letterHits = (L) => letterHits(L);
__api.letterLen = (L) => letterLen(L);
__api.buildOrchCache = () => buildOrchCache();
__api.isoWin = (f, o) => isoWin(f, o);
__api.migrate = (a, b, c, d, e, f, g, h) => migrateFrom(a, b, c, d, e, f, g, h);
`;

function makeEngine() {
  const played = [], events = [];
  const sandbox = {
    PULSE: 0.25, SOUNDS: [[36,'K'],[38,'S'],[42,'H'],[46,'O'],[75,'V'],[49,'C'],[40,'N'],[35,'B']],
    TABN: ['A','B','C','D','E','F','G','H'], UPS: 'ABCDEFGH', LOS: 'abcdefgh',
    CHAINMAX: 12, PHRASEMAX: 4, Math, JSON,
    playHit: (at, p, v) => played.push([at, p, v]),
    onSwitch: () => {},
    __api: {},
  };
  vm.createContext(sandbox);
  vm.runInContext(PREAMBLE + pureState + pure + core + EPILOGUE, sandbox);
  sandbox.onSwitch = (B) => {
    const g = sandbox.__api.get();
    events.push({ t: B, letter: g.curLetter, chain: g.activeChain, segStart: g.segStart });
  };
  return { api: sandbox.__api, played, events, sandbox };
}

function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

// ---------- independent oracle ----------
// Mirrors the pointer rules (they ARE the spec) but expands each letter's bar
// analytically as one unit, independent of the engine's chunked scheduling.
function oracle(cfg, steps) {
  const t0 = cfg.t0;
  let q = cfg.q;
  let cache = build();
  let su = t0, wiO = 0, injO = null, quO = null;
  let letter = null, chainNo = 0, seg = t0, len = 0, hs = [];
  const hits = [], events = [];
  function build() { return cfg.buildOrchCache(); }
  // independent breath mirror (must match the sliced page warp exactly)
  const br = cfg.breath, cycLenO = cache.cycLen || 0;
  let cycPhaseO = 0, curWarpLenO = 0, curPhase0O = 0, curDelta0O = 0, curInjO = false, curRateO = 1;
  const bOn = () => br && br.on && cycLenO > 0 && (br.depth || 0) > 0;
  const bDelta = (u) => { if (!bOn()) return 0; const A = br.depth, n = Math.max(1, br.n || 1),
    ph = br.phase || 0, Le = cycLenO / n;
    return (A * Le / (2 * Math.PI)) * (Math.cos(2 * Math.PI * ph) - Math.cos(2 * Math.PI * (u / Le + ph))); };
  const bRate = (u) => { if (!bOn()) return 1; const A = br.depth, n = Math.max(1, br.n || 1),
    ph = br.phase || 0, Le = cycLenO / n; return 1 + A * Math.sin(2 * Math.PI * (u / Le + ph)); };
  function adv(B) {
    if (injO && injO.idx >= injO.list.length) injO = null;
    if (quO != null) {
      const list = cache.chainSeqs[quO];
      injO = { list: (list && list.length) ? list : [cache.seq[0]], idx: 0 };
      quO = null;
    }
    let e, wasInj;
    if (injO) { e = injO.list[injO.idx++]; wasInj = true; }
    else { e = cache.seq[wiO]; wiO = (wiO + 1) % cache.seq.length; wasInj = false; }
    letter = e.L; chainNo = e.chain; len = e.len; hs = e.hits; seg = B; curInjO = wasInj;
    if (wasInj) { curRateO = bRate(cycPhaseO); curPhase0O = cycPhaseO; curDelta0O = 0;
      curWarpLenO = curRateO * len; }
    else { curRateO = 1; curPhase0O = cycPhaseO; curDelta0O = bDelta(cycPhaseO);
      curWarpLenO = len + bDelta(cycPhaseO + len) - curDelta0O;
      if (cycLenO > 0) { cycPhaseO += len;
        if (cycPhaseO >= cycLenO - 1e-6) { cycPhaseO -= cycLenO; if (Math.abs(cycPhaseO) < 1e-6) cycPhaseO = 0; } } }
    events.push({ t: B, letter, chain: chainNo, segStart: seg });
  }
  adv(t0);
  for (const step of steps) {
    if (step.tap !== undefined) { quO = step.tap; continue; }
    if (step.edit) { step.edit(); cache = build(); if (wiO >= cache.seq.length) wiO = 0;
      const e2 = cache.seq[(wiO - 1 + cache.seq.length) % cache.seq.length];
      if (e2 && e2.L === letter) { len = e2.len; hs = e2.hits;
        curWarpLenO = curInjO ? curRateO*len : len + bDelta(curPhase0O+len) - curDelta0O; } continue; }
    const { now, until } = step;
    for (;;) {
      let b = seg + curWarpLenO;                     // warped wall length of this bar
      if (quO != null && q === 'pulse') {
        const pu = cfg.pulse;
        const p = t0 + Math.ceil((Math.max(su, now) - t0) / pu - 1e-9) * pu;
        if (p < b - 1e-6) b = p;
      }
      const to = Math.min(until, b);
      if (to > su + 1e-9) {
        for (const [t, p, v] of hs) {
          const at = curInjO ? seg + curRateO * t
                             : seg + t + bDelta(curPhase0O + t) - curDelta0O;
          if (at >= su - 1e-9 && at < to - 1e-9) hits.push([at, p, v]);
        }
        su = to;
      }
      if (b <= until + 1e-9) { adv(b); su = b; }
      else break;
    }
  }
  return { hits, events };
}

// ---------- assertions ----------
let failures = 0;
function check(name, cond, detail) {
  if (!cond) { failures++; console.log(`  FAIL ${name}${detail ? ' - ' + detail : ''}`); }
}
function matchHits(name, got, want) {
  check(name + ':count', got.length === want.length, `got ${got.length} want ${want.length}`);
  const key = h => `${h[0].toFixed(6)}|${h[1]}|${h[2]}`;
  const g = got.map(key).sort(), w = want.map(key).sort();
  for (let i = 0; i < Math.min(g.length, w.length); i++) {
    if (g[i] !== w[i]) { check(name + ':hit', false, `first mismatch @${i}: got ${g[i]} want ${w[i]}`); return; }
  }
}
function matchEvents(name, got, want) {
  check(name + ':evcount', got.length === want.length, `got ${got.length} want ${want.length}`);
  for (let i = 0; i < Math.min(got.length, want.length); i++) {
    const a = got[i], b = want[i];
    if (Math.abs(a.t - b.t) > 1e-6 || a.letter !== b.letter || a.chain !== b.chain) {
      check(name + ':ev', false, `ev ${i}: got t=${a.t.toFixed(4)} ${a.letter}(${a.chain}) want t=${b.t.toFixed(4)} ${b.letter}(${b.chain})`);
      return;
    }
  }
}

// ---------- scenario driver ----------
function stack(motif, periods, children) { return { motif, periods, children: children || {} }; }
const CH = (...ls) => ({ seq: ls, orns: [] });
function run(name, cfg0, opts) {
  const eng = makeEngine();
  const cfg = {
    stacks: cfg0.stacks, winsBy: cfg0.winsBy || [[],[],[],[]], orch: cfg0.orch,
    q: cfg0.q || 'bar', t0: cfg0.t0 ?? 100.12, pulse: cfg0.pulse || 0.25, breath: cfg0.breath,
    letterHits: eng.api.letterHits, letterLen: eng.api.letterLen,
    buildOrchCache: eng.api.buildOrchCache,
  };
  eng.api.init({ stacks: cfg.stacks, winsBy: cfg.winsBy, orch: cfg.orch, q: cfg.q, t0: cfg.t0,
    mixBase: cfg0.mixBase || 0, pulse: cfg.pulse, breath: cfg.breath });
  const snap = JSON.stringify({ stacks: cfg.stacks, winsBy: cfg.winsBy, orch: cfg.orch });
  const launchEv = eng.events.splice(0);          // advance(t0) fires one event pre-steps
  const r = rng(cfg0.seed ?? 42);
  const dur = cfg0.dur ?? 60;
  const steps = [];
  let now = cfg.t0 - 0.12;
  const acts = opts?.actions ?? [];
  let ai = 0, prevSched = cfg.t0;
  while (now < cfg.t0 - 0.12 + dur) {
    now += (cfg0.coarse ? 0.15 : 0.04 + r() * 0.03) + (r() < 0.06 ? 0.12 + r() * 0.08 : 0);
    while (ai < acts.length && now >= acts[ai].at) {
      const a = acts[ai++];
      if (a.tap !== undefined) { eng.api.tap(a.tap); steps.push({ tap: a.tap }); }
      if (a.edit) { a.edit(); eng.api.buildCache(); steps.push({ edit: a.edit }); }
    }
    const until = now + 0.18;
    eng.api.call(now, until);
    const g = eng.api.get();
    check(name + ':monotonic', g.schedUntil >= prevSched - 1e-9, 'schedUntil went backwards');
    check(name + ':caughtUp', Math.abs(g.schedUntil - until) < 1e-9, `schedUntil ${g.schedUntil} != until ${until}`);
    prevSched = g.schedUntil;
    steps.push({ now, until });
  }
  { // restore initial state in place (objects shared with the engine sandbox)
    const s0 = JSON.parse(snap);
    cfg.stacks.forEach((s, i) => { for (const k of Object.keys(s)) delete s[k]; Object.assign(s, s0.stacks[i]); });
    cfg.winsBy.forEach((arr, i) => { arr.length = 0; (s0.winsBy[i] || []).forEach(w => arr.push(w)); });
    for (const k of Object.keys(cfg.orch)) delete cfg.orch[k]; Object.assign(cfg.orch, s0.orch);
  }
  const oc = oracle(cfg, steps);
  matchHits(name, eng.played, oc.hits);
  matchEvents(name, [...launchEv, ...eng.events].slice(1), oc.events.slice(1));
  // structural: every boundary sits on the pulse grid (1e-6: non-dyadic pulses
  // round). Breath deliberately warps boundaries off the wall grid, so this
  // check runs only when breath is off; V12/V13 assert the breath timing laws.
  if (!(cfg0.breath && cfg0.breath.on)) for (const e of eng.events) {
    const pf = (e.t - cfg.t0) / cfg.pulse;
    check(name + ':grid', Math.abs(pf - Math.round(pf)) < 1e-6, `boundary off pulse grid at ${e.t}`);
  }
  return { eng, cfg };
}

// ---------- fixtures: one workspace, tabs of different lengths ----------
function ws() {
  return {
    stacks: [
      { ...stack([1,2,3], [16]),                     // A: ruler + lanes + a LOOP one-off
        orns: [{ li: 0, bar: 0, u: 1, act: 'add', sym: 6 }],   // baked-in crash @ pulse 1
        lanes: [ { ...stack([4,0], [10]), offs: [3], steps: [2] },  // stepping: 5-bar cycle
                 stack([5,0,0,-2], [24]) ] },        //   24-pulse lane: cut at 16 (ghost incl)
      { ...stack([2,1], [9], {0:{S:3,m:[1,0,4,7],p:1,pre:1}}), phase: 2 },  // B: pre + SPILL child
      { ...stack([3,0,-2,1,2,3,1,0], [4, 8]), offs: [5, 0] },  // C: 4-window sliding over 8 (wraps)
    ],
    winsBy: [
      [{tab:1, a:0.5, b:1.5}, {tab:2, a:2.0, b:3.0}],   // mix a: A ground
      [{tab:0, a:0.25, b:1.0}, {tab:1, a:1.25, b:2.0}], // mix b: B ground (tab-1 window inert)
      [{tab:0, a:0.5, b:1.5}],                          // mix c: C ground revealing A
      [],
    ],
  };
}

console.log('V1 written-sequence fidelity (variable-length letters incl M)');
{
  const w = ws();
  run('V1a', { ...w, orch: { motif: [1,2], chains: [CH('A'),CH('B','A')] }, dur: 90, seed: 7 });
  const w2 = ws();
  run('V1b', { ...w2, orch: { motif: [1,2,3,2], chains: [CH('A','B','A'),CH('A','B'),CH('C')] }, dur: 120, seed: 11 });
  const w3 = ws();
  run('V1c', { ...w3, orch: { motif: [2,2,1], chains: [CH('A'),CH('B','C','B','A')] }, dur: 120, seed: 13 });
  const w4 = ws();                                  // all three mixes as letters in one arrangement
  run('V1d', { ...w4, orch: { motif: [1,2], chains: [CH('B','A','C'),CH('A','B')] }, dur: 120, seed: 19 });
  const w5 = ws();                                  // 5 tabs: E/e in play
  w5.stacks.push(stack([2,3], [6]));                // E: 1.50s
  w5.stacks.push(stack([1,4,2], [12]));             // E is idx 3... push twice -> idx 3,4
  w5.winsBy = [[],[],[],[{tab:0,a:0.25,b:1.0}],[{tab:3,a:0.5,b:2.0}]];
  run('V1e', { ...w5, orch: { motif: [1,2], chains: [CH('E','E','A'),CH('D','E')] }, dur: 100, seed: 29 });
}

console.log('V2 inject-then-resume (q=bar)');
{
  const w = ws();
  const { eng } = run('V2', { ...w, orch: { motif: [1,1,2], chains: [CH('A'),CH('B','C','B')] }, dur: 60, seed: 9 },
    { actions: [{ at: 106.0, tap: 1 }, { at: 125.0, tap: 0 }] });
  check('V2:injected', eng.events.some(e => e.chain === 2), 'injection never played');
}

console.log('V3 pulse-quantized injection (cuts the bar mid-flight)');
{
  const w = ws();
  const { eng, cfg } = run('V3', { ...w, orch: { motif: [1], chains: [CH('A'),CH('B','B')] }, q: 'pulse', dur: 40, seed: 21 },
    { actions: [{ at: 101.3, tap: 1 }] });
  // the injection boundary must land mid-bar (A is 4s; tap at ~1.3s in)
  const cut = eng.events.find(e => e.chain === 2);
  check('V3:cutMidBar', cut && Math.abs((cut.t - cfg.t0) / 4.0 - Math.round((cut.t - cfg.t0) / 4.0)) > 1e-6,
    'pulse cut landed on a bar boundary instead');
}

console.log('V4 pre-emption (tap during an injection)');
{
  const w = ws();
  run('V4', { ...w, orch: { motif: [1], chains: [CH('A'),CH('B','B','B','B'),CH('C','C')] }, dur: 50, seed: 23 },
    { actions: [{ at: 105.0, tap: 1 }, { at: 108.0, tap: 2 }] });
}

console.log('V5 mid-play edits (chains, motif, tab periods)');
{
  const w = ws();
  const orch5 = { motif: [1,2], chains: [CH('A'),CH('B','C')] };
  run('V5', { ...w, orch: orch5, dur: 70, seed: 17 }, {
    actions: [
      { at: 108.0, edit: () => { orch5.chains[1] = CH('C','B','C'); } },
      { at: 122.0, edit: () => { orch5.motif = [2,1,1]; } },
      { at: 137.0, edit: () => { w.stacks[1].periods = [11]; } },
      { at: 151.0, edit: () => { w.stacks[0].phase = 5; } },
    ],
  });
}

console.log('V6 long run, exact grid (dyadic bar lengths, no drift)');
{
  const w = ws();
  run('V6', { ...w, orch: { motif: [1,2,3,2,1], chains: [CH('A','B'),CH('C'),CH('A','B','B')] },
    dur: 1800, t0: 1000000.12, coarse: true, seed: 31 });
}

console.log('V8 real tempo (136bpm pulse) with lanes + ghosts');
{
  const w = ws();
  run('V8', { ...w, orch: { motif: [1,2,3], chains: [CH('A'),CH('B','C'),CH('A')] },
    pulse: 15/136, dur: 90, seed: 37 });
}

console.log('V9 chain one-offs (add/mute/ghost at structural addresses + injection)');
{
  const w = ws();
  w.stacks[1] = { ...stack([2,1], [9]), steps: [1] };   // B: 2-bar cycle
  const orch9 = { motif: [1,2], chains: [
    { seq: ['A','B'], orns: [
      { li: 0, bar: 0, u: 3, act: 'add',   sym: 6 },    // crash at phrase1 pulse 3
      { li: 0, bar: 0, u: 0, act: 'mute',  sym: 1 },    // kill the downbeat kick
      { li: 0, bar: 0, u: 5, act: 'add',   sym: -7 },   // ghost snare hit
      { li: 1, bar: 1, u: 2, act: 'ghost', sym: 1 },    // soften B's bar-2 kick
      { li: 0, bar: 0, u: 7, act: 'add', sym: 3,
        ch: { S: 4, m: [3, 0, -3], p: 0 } },            // one-off sub-motif burst
      { li: 0, bar: 0, u: 9, act: 'add', sym: 3,
        ch: { S: 2, m: [3, 3], p: 0, pre: 1 } },        // burst with a prenote pickup
      { li: 0, bar: 0, u: 12, act: 'add', sym: 5,
        ch: { S: 2, m: [5, 0, -5, 5], p: 0 } },         // burst that SPILLS past its pulse
      { li: 0, bar: 0, u: 7, act: 'mute', sym: 3, S: 4, k: 2 },  // sub-tick mute of the burst
      { li: 0, bar: 9, u: 0, act: 'add', sym: 6 },      // OUT OF RANGE: must be silent
    ]},
    { seq: ['B'], orns: [] },
  ]};
  const { eng } = run('V9', { ...w, orch: orch9, dur: 80, seed: 41 },
    { actions: [{ at: 108, tap: 0 }] });                // inject the ornamented chain too
  const cache = eng.api.buildOrchCache();
  const e0 = cache.chainSeqs[0][0], e1 = cache.chainSeqs[0][1];
  const inPulse = (h, u) => Math.floor(h[0] / 0.25 + 1e-6) === u;
  check('V9:add', e0.hits.some(h => inPulse(h, 3) && h[1] === 49 && h[2] === 96), 'crash missing');
  check('V9:ghostAdd', e0.hits.some(h => inPulse(h, 5) && h[1] === 40 && h[2] === 52), 'ghost snare missing');
  check('V9:mute', !e0.hits.some(h => inPulse(h, 0) && h[1] === 36), 'downbeat kick survived mute');
  const bp1 = 9;                                        // B's bar = 9 pulses; bar1 pulse2 -> global 11
  check('V9:ghostAct', e1.hits.filter(h => inPulse(h, bp1 + 2) && h[1] === 36)
    .every(h => h[2] === 52) && e1.hits.some(h => inPulse(h, bp1 + 2) && h[1] === 36),
    'B bar-2 kick not ghosted');
  const plain = eng.api.letterHits('A');
  check('V9:pristine', plain.some(h => inPulse(h, 0) && h[1] === 36),
    'ornament leaked into the pristine letter');
  check('V9:loopOrn', plain.some(h => inPulse(h, 1) && h[1] === 49),
    'loop one-off missing from the letter');
  check('V9:loopOrnCarried', e0.hits.some(h => inPulse(h, 1) && h[1] === 49),
    'loop one-off did not carry into the chain occurrence');
  // the bar-9 orn is out of range for A (1-bar cycle): exactly the two
  // legitimate crashes (loop-orn @1, chain-orn @3) and nothing more
  check('V9:orphanSilent', e0.hits.filter(h => h[1] === 49).length === 2,
    'out-of-range one-off sounded');
  // sub-motif burst at pulse 7: S=4, m=[3,0,-3] -> j0 42@96, j2 42@52, j3 42@70
  const burst = e0.hits.filter(h => inPulse(h, 7) && h[1] === 42)
    .map(h => [Math.round((h[0] - 7 * 0.25) / 0.0625), h[2]]).sort((a, b) => a[0] - b[0]);
  // the sub-tick mute (S=4, k=2) surgically removes the ghost at tick 2
  check('V9:burst', JSON.stringify(burst) === JSON.stringify([[0, 96], [3, 70]]),
    'sub-motif burst + sub-tick mute wrong: ' + JSON.stringify(burst));
  // prenote burst at pulse 9 (S=2, pre=1): pickup at 8.5 ticks -> t=2.125 @70, anchor 2.25 @96
  const preHits = e0.hits.filter(h => h[1] === 42 && h[0] > 2.05 && h[0] < 2.3)
    .map(h => [Math.round(h[0] * 1000), h[2]]).sort((a, b) => a[0] - b[0]);
  check('V9:prenote', JSON.stringify(preHits) === JSON.stringify([[2125, 70], [2250, 96]]),
    'prenote burst wrong: ' + JSON.stringify(preHits));
  // spill burst at pulse 12 (S=2, m len 4): ticks at 3.0(96), 3.25 ghost(52), 3.375(70)
  const spill = e0.hits.filter(h => h[1] === 75 && h[0] > 2.9 && h[0] < 3.5)
    .map(h => [Math.round(h[0] * 1000), h[2]]).sort((a, b) => a[0] - b[0]);
  // (pulse 12 also holds a BASE rim @102 - union semantics: both sound)
  check('V9:spill', JSON.stringify(spill) === JSON.stringify([[3000, 102], [3000, 96], [3250, 52], [3375, 70]]),
    'spill burst wrong: ' + JSON.stringify(spill));
}

console.log('V10 mute layer (isolating windows + several one-offs at one address)');
{
  // isoWin: the smallest (S,k) window catching only the tapped sub-position
  const eng = makeEngine();
  const iw = eng.api.isoWin;
  check('V10:isoLone', JSON.stringify(iw(0, [0])) === '{"S":1,"k":0}', JSON.stringify(iw(0, [0])));
  check('V10:isoHalf', JSON.stringify(iw(0.5, [0, 0.5])) === '{"S":2,"k":1}', JSON.stringify(iw(0.5, [0, 0.5])));
  check('V10:isoTriplet', JSON.stringify(iw(1/3, [0, 1/3, 2/3])) === '{"S":3,"k":1}',
    JSON.stringify(iw(1/3, [0, 1/3, 2/3])));
  // two notes at the SAME sub-position share fate: whole-pulse window
  check('V10:isoTwin', JSON.stringify(iw(0.25, [0.25, 0.25])) === '{"S":1,"k":0}',
    JSON.stringify(iw(0.25, [0.25, 0.25])));
  // several one-offs at ONE address: two sub-tick mutes carve ticks 1 and 3
  // out of an S4 hat cell; at another address an add and a mute coexist
  const A = { ...stack([1, 3], [16], { 1: { S: 4, m: [3, 3, 3, 3] } }), orns: [
    { li: 0, bar: 0, u: 1, act: 'mute', sym: 3, S: 4, k: 1 },
    { li: 0, bar: 0, u: 1, act: 'mute', sym: 3, S: 4, k: 3 },
    { li: 0, bar: 0, u: 0, act: 'add',  sym: 6 },
    { li: 0, bar: 0, u: 0, act: 'mute', sym: 1 },
  ]};
  eng.api.init({ stacks: [A], winsBy: [[]], orch: { motif: [1], chains: [CH('A')] }, q: 'bar', t0: 0 });
  const hs = eng.api.letterHits('A');
  const hats = hs.filter(h => h[1] === 42 && h[0] < 0.5 - 1e-9)
    .map(h => Math.round(h[0] * 1000)).sort((a, b) => a - b);
  check('V10:twoMutes', JSON.stringify(hats) === '[250,375]', JSON.stringify(hats));
  check('V10:coexist', hs.some(h => h[0] < 1e-9 && h[1] === 49)
    && !hs.some(h => h[0] < 0.25 - 1e-9 && h[1] === 36),
    'add + mute at one address failed');
}

console.log('V11 fractional time (flex): spot + subspot timing nudge');
{
  const eng = makeEngine();
  // top=2: index0 has a child, index1 is a plain spot flexed +10% of a pulse;
  // the child's 2nd sub-cell is flexed -20% of a sub-slot
  const A = { ...stack([1, 2], [2], { 0: { S: 2, m: [3, 4], flexm: { 1: -20 } } }), flex: { 1: 10 } };
  eng.api.init({ stacks: [A], winsBy: [[]], orch: { motif: [1], chains: [CH('A')] }, q: 'bar', t0: 0 });
  const hs = eng.api.letterHits('A');
  const find = p => hs.filter(h => h[1] === p).map(h => Math.round(h[0] * 1000)).sort((a, b) => a - b);
  check('V11:spot', JSON.stringify(find(38)) === '[275]', 'spot flex +10% wrong: ' + JSON.stringify(find(38)));
  check('V11:subAnchor', JSON.stringify(find(42)) === '[0]', 'sub anchor moved: ' + JSON.stringify(find(42)));
  check('V11:subFlex', JSON.stringify(find(46)) === '[100]', 'subspot flex -20% wrong: ' + JSON.stringify(find(46)));
  // law: flex 0 = identity (the same stack without flex lands on the grid)
  const B = stack([1, 2], [2], { 0: { S: 2, m: [3, 4] } });
  eng.api.init({ stacks: [B], winsBy: [[]], orch: { motif: [1], chains: [CH('A')] }, q: 'bar', t0: 0 });
  const hs2 = eng.api.letterHits('A');
  const g = p => hs2.filter(h => h[1] === p).map(h => Math.round(h[0] * 1000));
  check('V11:identity', JSON.stringify(g(38)) === '[250]' && JSON.stringify(g(46)) === '[125]',
    'zero-flex not on grid: ' + JSON.stringify(g(38)) + ' ' + JSON.stringify(g(46)));
}

console.log('V12 breathing (global orch-level tempo swell)');
{
  const A = stack([1,2,3,4],[4]);                 // top 4, letterLen 1.0s at pulse .25
  const orchB = { motif:[1], chains:[CH('A','A')] };  // cycle = 2 letters = 2.0s
  const breath = { on:true, depth:0.05, n:1, phase:0 };
  const { eng } = run('V12', { stacks:[A], winsBy:[[]], orch:orchB, breath, t0:0, dur:9, seed:5 });
  // run() already dual-verified engine==oracle (matchHits/matchEvents).
  const cyc = 2.0, TWO_PI = 2*Math.PI;
  const delta = u => (0.05*cyc/TWO_PI)*(1 - Math.cos(TWO_PI*(u/cyc)));
  // analytic: the H (42) at score 0.5 in letter 1 plays at 0.5 + delta(0.5)
  const want = 0.5 + delta(0.5);
  check('V12:warp', eng.played.some(h => h[1]===42 && Math.abs(h[0]-want) < 1e-6),
    `H@0.5 not warped to ${want.toFixed(6)}: ${eng.played.filter(h=>h[1]===42).map(h=>h[0].toFixed(4))}`);
  // drift-free: every cycle boundary lands EXACTLY on k*cycLen
  let driftOk = true;
  for (let k=1;k<=4;k++) if(!eng.events.some(e=>Math.abs(e.t - k*cyc) < 1e-6)) driftOk=false;
  check('V12:driftFree', driftOk, 'cycle boundary off k*cycLen: '+eng.events.map(e=>e.t.toFixed(4)).join(','));
  // warp is actually active: some hit sits off the flat pulse grid
  check('V12:active', eng.played.some(h => { const pf=h[0]/0.25; return Math.abs(pf-Math.round(pf))>1e-4; }),
    'no off-grid (breathed) hit found');
  // content identity: same count + pitch multiset as the breath-off run
  const flat = run('V12flat', { stacks:[A], winsBy:[[]], orch:orchB, t0:0, dur:9, seed:5 });
  const pm = arr => arr.map(h=>h[1]).sort((a,b)=>a-b).join(',');
  check('V12:content', eng.played.length===flat.eng.played.length && pm(eng.played)===pm(flat.eng.played),
    'breath added/dropped notes');
}

console.log('V13 breathing + live injection (phase held; engine==oracle)');
{
  const A = stack([1,2,3,4],[4]), B = stack([5,0,6,0],[4]);
  const orchB = { motif:[1], chains:[CH('A','A'), CH('B')] };
  const breath = { on:true, depth:0.06, n:1, phase:0.1 };
  const { eng } = run('V13', { stacks:[A,B], winsBy:[[],[]], orch:orchB, breath, t0:0, dur:10, seed:8 },
    { actions:[{ at: 2.5, tap: 1 }] });   // tap chain 2 mid-play (dual-verified vs oracle)
  check('V13:injected', eng.events.some(e=>e.chain===2), 'injected chain never played');
}

console.log('V14 composite tab (live: cells assembled from source tabs)');
{
  const eng = makeEngine();
  const A = stack([1,2,3,4],[4]);            // 4 cells
  const B = stack([5,6,7],[3]);              // 3 cells
  const C = { compose:[0,1], periods:[10], children:{}, motif:[0], orns:[] };  // A++B, period 10
  eng.api.init({ stacks:[A,B,C], winsBy:[[],[],[]], orch:{motif:[1],chains:[CH('C')]}, q:'bar', t0:0 });
  // 1) assembled motif = A's cells then B's cells
  check('V14:motif', JSON.stringify(C.motif) === JSON.stringify([1,2,3,4,5,6,7]),
    'compose motif wrong: ' + JSON.stringify(C.motif));
  // 2) Jon's example: period 10 over 7 cells -> pulses 0..9 = cells [1,2,3,4,5,6,7,1,2,3]
  const SND = [36,38,42,46,75,49,40];
  const want = [0,1,2,3,4,5,6,0,1,2].map(c => SND[c]);
  const hs = eng.api.letterHits('C');
  const got = Array.from({length:10}, (_,u) => { const h = hs.find(h => Math.abs(h[0]-u*0.25) < 1e-9); return h?h[1]:null; });
  check('V14:fold', JSON.stringify(got) === JSON.stringify(want), 'fold wrong: ' + JSON.stringify(got));
  // 3) a child on a source lands at the composite offset (B[0] -> composite index 4)
  B.children = { 0: { S:2, m:[3,3] } };
  eng.api.materialize();
  check('V14:childMerge', !!C.children[4] && !C.children[0] && C.children[4].S===2,
    'child not merged at offset: ' + JSON.stringify(Object.keys(C.children)));
  // 4) LIVE: edit a source, re-materialize, composite tracks it
  A.motif[0] = 7;
  eng.api.materialize();
  check('V14:live', C.motif[0] === 7, 'composite did not track source edit');
}

console.log('V15 composite multi-lane (compose every lane, rest-pad the missing)');
{
  const eng = makeEngine();
  const A = { ...stack([1,2,3,4],[4]), lanes:[ stack([7,7],[2]) ] };  // A has a 2nd lane
  const B = stack([5,6,7],[3]);                                        // B is single-lane
  const C = { compose:[0,1], periods:[10], children:{}, motif:[0], orns:[] };
  eng.api.init({ stacks:[A,B,C], winsBy:[[],[],[]], orch:{motif:[1],chains:[CH('C')]}, q:'bar', t0:0 });
  check('V15:ruler', JSON.stringify(C.motif) === JSON.stringify([1,2,3,4,5,6,7]), JSON.stringify(C.motif));
  // lane 2 = A.lane2 ++ B rest-pad (B has no lane2 -> 3 rests = B's ruler length)
  check('V15:lane', C.lanes && C.lanes.length === 1
    && JSON.stringify(C.lanes[0].motif) === JSON.stringify([7,7,0,0,0]),
    'composed lane wrong: ' + JSON.stringify(C.lanes && C.lanes[0] && C.lanes[0].motif));
  // authored lane period survives a re-materialize (only cells refresh)
  C.lanes[0].periods = [8]; eng.api.materialize();
  check('V15:keepPeriod', C.lanes[0].periods[0] === 8
    && JSON.stringify(C.lanes[0].motif) === JSON.stringify([7,7,0,0,0]),
    'lane period not preserved: ' + JSON.stringify(C.lanes[0].periods));
  // sources go single-lane -> composite drops the derived lane
  delete A.lanes; eng.api.materialize();
  check('V15:shrink', !C.lanes, 'composite lane not dropped when all sources single-lane');
}

console.log('V7 migration (v7 lowercase->upper, v6 wrap+trim, v4/v3/v2, v8 clamp)');
{
  const eng = makeEngine();
  const s1 = stack([1,2], [12]), s2 = stack([3], [8]);
  const v7good = { v: 7, stacks: [s1, s2], cur: 0, view: 'orch', mixBase: 1, pulse: 0.2,
    winsBy: [[],[{tab:0,a:1,b:2}]],
    orch: { motif: [1,2], chains: [
      { seq: ['b','A','a'], orns: [{ li: 1, bar: 0, u: 2, act: 'add', sym: 3 }] },
      { seq: ['B'], orns: [] }] }, q: 'pulse' };
  const m7g = eng.api.migrate(null, JSON.parse(JSON.stringify(v7good)), null, null, null, null, null, null);
  check('V7:v7', m7g.v === 11 && m7g.pulse === 0.2
    && m7g.orch.chains[0].seq.join('') === 'BAA'        // lowercase = its own uppercase now
    && m7g.orch.chains[0].orns.length === 1,
    JSON.stringify(m7g.orch));
  const v6good = { v: 6, stacks: [s1, s2], cur: 0, view: 'orch', mixBase: 1, pulse: 0.2,
    winsBy: [[],[{tab:0,a:1,b:2}]],
    orch: { motif: [1,2], chains: [['b','A','B','a','A'],['B']] }, q: 'pulse' };
  const m6 = eng.api.migrate(null, null, JSON.parse(JSON.stringify(v6good)), null, null, null, null, null);
  check('V7:v6', m6.v === 11 && m6.pulse === 0.2
    && m6.orch.chains[0].seq.join('') === 'BABA'        // trimmed to 4 + uppercased
    && m6.orch.chains[0].orns.length === 0 && m6.winsBy[1].length === 1,
    JSON.stringify(m6.orch));
  const v4 = { v: 4, stacks: [s1, s2], cur: 0, view: 'mix', mixBase: 1,
    wins: [{tab:0,a:1,b:2}], orch: { motif: [1,2], chains: [['M','A'],['B']] }, q: 'pulse' };
  const m4 = eng.api.migrate(null, null, null, null, v4, null, null, null);
  check('V7:v4', m4.v === 11 && m4.pulse === 0.25 && m4.winsBy.length === 2
    && m4.orch.chains[0].seq.join('') === 'BA' && m4.orch.chains[1].seq.join('') === 'B'
    && m4.q === 'pulse' && m4.mixBase === 1, JSON.stringify(m4.orch));
  const v3 = { v: 3,
    setups: [
      { stacks: [s1, s2], cur: 0, view: 'stack', wins: [{tab:1,a:1,b:2}], deck: 'A' },
      { stacks: [s1], cur: 0, view: 'stack', wins: [], deck: 'B' },
      { stacks: [s1, s2], cur: 1, view: 'mix', wins: [], deck: 'MIX' },
    ],
    curSetup: 0, oview: 'orch', orch: { periods: [4], motif: [1, 3, 2] }, opulse: 8, q: 'tick' };
  const m3 = eng.api.migrate(null, null, null, null, null, v3, null, null);
  check('V7:v3', m3.v === 11 && m3.orch.chains.length === 3
    && m3.orch.chains[0].seq.join('') === 'A' && m3.orch.chains[2].seq.join('') === 'A'
    && m3.orch.motif.join() === '1,3,2' && m3.q === 'bar', JSON.stringify(m3.orch));
  const v2 = { stacks: [s1], cur: 0, view: 'stack', wins: [] };
  const m2 = eng.api.migrate(null, null, null, null, null, null, v2, null);
  check('V7:v2', m2.v === 11 && m2.orch.chains.length === 1
    && m2.orch.chains[0].seq.join('') === 'A' && m2.winsBy.length === 1);
  const v8bad = { v: 8, stacks: [{...s1, lanes:[null, stack([2],[4]), {bogus:1}]}, s2],
    cur: 9, view: 'orch', mixBase: 7, pulse: 9.9,
    winsBy: [[{tab:1,a:0,b:1}]],
    orch: { motif: [1, 9, 2], chains: [
      { seq: ['A','Z','b'], orns: [
        { li: 0, bar: 0, u: 2, act: 'add', sym: 3 },     // valid
        { li: 9, bar: 0, u: 2, act: 'add', sym: 3 },     // bad li
        { li: 0, bar: 0, u: 2, act: 'zap', sym: 3 },     // bad act
        { li: 0, bar: 0, u: 2, act: 'add', sym: 99 },    // bad sym
        null,
      ]},
      { seq: ['B'] },
    ] }, q: 'weird' };
  const m8 = eng.api.migrate(v8bad, null, null, null, null, null, null, null);
  check('V7:v8clamp', m8.cur === 1 && m8.mixBase === 1 && m8.winsBy.length === 2
    && m8.pulse === 0.25 && m8.stacks[0].lanes.length === 1
    && m8.orch.chains[0].seq.join('') === 'AAB'          // Z->A, b->B
    && m8.orch.chains[0].orns.length === 1
    && m8.orch.chains[1].orns.length === 0
    && m8.orch.motif.join() === '1,2,2' && m8.q === 'bar' && m8.view === 'orch',
    JSON.stringify(m8.orch));
}

console.log(failures === 0 ? '\nALL GREEN' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
