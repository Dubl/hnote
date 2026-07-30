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
`;
const EPILOGUE = `
__api.buildCache = () => {
  orchCache=buildOrchCache();
  if(wi>=orchCache.seq.length) wi=0;
  const e=orchCache.seq[(wi-1+orchCache.seq.length)%orchCache.seq.length];
  if(e&&e.L===curLetter){ curHits=e.hits; curLen=e.len; }
};
__api.init = (o) => { stacks=o.stacks; winsBy=o.winsBy||[[],[],[],[]]; orch=o.orch; q=o.q; t0=o.t0;
  PULSE=o.pulse||0.25;
  mixBase=o.mixBase||0; wins=winsBy[mixBase]||[];
  schedUntil=t0; wi=0; inj=null; oQueue=null;
  orchCache=buildOrchCache();
  advance(t0); };
__api.tap = (i) => { oQueue=i; };
__api.get = () => ({t0, schedUntil, segStart, wi, inj: inj?{idx:inj.idx,n:inj.list.length}:null,
  oQueue, curLetter, curLen, activeChain, q});
__api.call = (now, until) => scheduleOrch(now, until);
__api.letterHits = (L) => letterHits(L);
__api.letterLen = (L) => letterLen(L);
__api.buildOrchCache = () => buildOrchCache();
__api.migrate = (a, b, c, d, e, f, g) => migrateFrom(a, b, c, d, e, f, g);
`;

function makeEngine() {
  const played = [], events = [];
  const sandbox = {
    PULSE: 0.25, SOUNDS: [[36,'K'],[38,'S'],[42,'H'],[46,'O'],[75,'V'],[49,'C'],[40,'N']],
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
  function adv(B) {
    if (injO && injO.idx >= injO.list.length) injO = null;
    if (quO != null) {
      const list = cache.chainSeqs[quO];
      injO = { list: (list && list.length) ? list : [cache.seq[0]], idx: 0 };
      quO = null;
    }
    let e;
    if (injO) { e = injO.list[injO.idx++]; }
    else { e = cache.seq[wiO]; wiO = (wiO + 1) % cache.seq.length; }
    letter = e.L; chainNo = e.chain; len = e.len; hs = e.hits; seg = B;
    events.push({ t: B, letter, chain: chainNo, segStart: seg });
  }
  adv(t0);
  for (const step of steps) {
    if (step.tap !== undefined) { quO = step.tap; continue; }
    if (step.edit) { step.edit(); cache = build(); if (wiO >= cache.seq.length) wiO = 0;
      const e2 = cache.seq[(wiO - 1 + cache.seq.length) % cache.seq.length];
      if (e2 && e2.L === letter) { len = e2.len; hs = e2.hits; } continue; }
    const { now, until } = step;
    for (;;) {
      let b = seg + len;
      if (quO != null && q === 'pulse') {
        const pu = cfg.pulse;
        const p = t0 + Math.ceil((Math.max(su, now) - t0) / pu - 1e-9) * pu;
        if (p < b - 1e-6) b = p;
      }
      const to = Math.min(until, b);
      if (to > su + 1e-9) {
        for (const [t, p, v] of hs) {
          const at = seg + t;
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
    q: cfg0.q || 'bar', t0: cfg0.t0 ?? 100.12, pulse: cfg0.pulse || 0.25,
    letterHits: eng.api.letterHits, letterLen: eng.api.letterLen,
    buildOrchCache: eng.api.buildOrchCache,
  };
  eng.api.init({ stacks: cfg.stacks, winsBy: cfg.winsBy, orch: cfg.orch, q: cfg.q, t0: cfg.t0,
    mixBase: cfg0.mixBase || 0, pulse: cfg.pulse });
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
  // structural: every boundary sits on the pulse grid (1e-6: non-dyadic pulses round)
  for (const e of eng.events) {
    const pf = (e.t - cfg.t0) / cfg.pulse;
    check(name + ':grid', Math.abs(pf - Math.round(pf)) < 1e-6, `boundary off pulse grid at ${e.t}`);
  }
  return { eng, cfg };
}

// ---------- fixtures: one workspace, tabs of different lengths ----------
function ws() {
  return {
    stacks: [
      { ...stack([1,2,3], [16]),                     // A: 16-pulse ruler + 2 lanes
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
  run('V1b', { ...w2, orch: { motif: [1,2,3,2], chains: [CH('A','B','A'),CH('a','B'),CH('C')] }, dur: 120, seed: 11 });
  const w3 = ws();
  run('V1c', { ...w3, orch: { motif: [2,2,1], chains: [CH('a'),CH('B','C','B','A')] }, dur: 120, seed: 13 });
  const w4 = ws();                                  // all three mixes as letters in one arrangement
  run('V1d', { ...w4, orch: { motif: [1,2], chains: [CH('b','A','c'),CH('a','b')] }, dur: 120, seed: 19 });
  const w5 = ws();                                  // 5 tabs: E/e in play
  w5.stacks.push(stack([2,3], [6]));                // E: 1.50s
  w5.stacks.push(stack([1,4,2], [12]));             // E is idx 3... push twice -> idx 3,4
  w5.winsBy = [[],[],[],[{tab:0,a:0.25,b:1.0}],[{tab:3,a:0.5,b:2.0}]];
  run('V1e', { ...w5, orch: { motif: [1,2], chains: [CH('E','e','A'),CH('d','E')] }, dur: 100, seed: 29 });
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
  run('V6', { ...w, orch: { motif: [1,2,3,2,1], chains: [CH('A','B'),CH('c'),CH('a','B','b')] },
    dur: 1800, t0: 1000000.12, coarse: true, seed: 31 });
}

console.log('V8 real tempo (136bpm pulse) with lanes + ghosts');
{
  const w = ws();
  run('V8', { ...w, orch: { motif: [1,2,3], chains: [CH('A'),CH('b','C'),CH('a')] },
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
  // sub-motif burst at pulse 7: S=4, m=[3,0,-3] -> j0 42@96, j2 42@52, j3 42@70
  const burst = e0.hits.filter(h => inPulse(h, 7) && h[1] === 42)
    .map(h => [Math.round((h[0] - 7 * 0.25) / 0.0625), h[2]]).sort((a, b) => a[0] - b[0]);
  check('V9:burst', JSON.stringify(burst) === JSON.stringify([[0, 96], [2, 52], [3, 70]]),
    'sub-motif burst wrong: ' + JSON.stringify(burst));
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

console.log('V7 migration (v6 wrap+trim, v4/v3/v2 chain, v7 clamp)');
{
  const eng = makeEngine();
  const s1 = stack([1,2], [12]), s2 = stack([3], [8]);
  const v6good = { v: 6, stacks: [s1, s2], cur: 0, view: 'orch', mixBase: 1, pulse: 0.2,
    winsBy: [[],[{tab:0,a:1,b:2}]],
    orch: { motif: [1,2], chains: [['b','A','B','a','A'],['B']] }, q: 'pulse' };
  const m6 = eng.api.migrate(null, JSON.parse(JSON.stringify(v6good)), null, null, null, null, null);
  check('V7:v6', m6.v === 7 && m6.pulse === 0.2
    && m6.orch.chains[0].seq.join('') === 'bABa'        // trimmed to the 4-phrase convention
    && m6.orch.chains[0].orns.length === 0 && m6.winsBy[1].length === 1,
    JSON.stringify(m6.orch));
  const v4 = { v: 4, stacks: [s1, s2], cur: 0, view: 'mix', mixBase: 1,
    wins: [{tab:0,a:1,b:2}], orch: { motif: [1,2], chains: [['M','A'],['B']] }, q: 'pulse' };
  const m4 = eng.api.migrate(null, null, null, v4, null, null, null);
  check('V7:v4', m4.v === 7 && m4.pulse === 0.25 && m4.winsBy.length === 2
    && m4.orch.chains[0].seq.join('') === 'bA' && m4.orch.chains[1].seq.join('') === 'B'
    && m4.q === 'pulse' && m4.mixBase === 1, JSON.stringify(m4.orch));
  const v3 = { v: 3,
    setups: [
      { stacks: [s1, s2], cur: 0, view: 'stack', wins: [{tab:1,a:1,b:2}], deck: 'A' },
      { stacks: [s1], cur: 0, view: 'stack', wins: [], deck: 'B' },
      { stacks: [s1, s2], cur: 1, view: 'mix', wins: [], deck: 'MIX' },
    ],
    curSetup: 0, oview: 'orch', orch: { periods: [4], motif: [1, 3, 2] }, opulse: 8, q: 'tick' };
  const m3 = eng.api.migrate(null, null, null, null, v3, null, null);
  check('V7:v3', m3.v === 7 && m3.orch.chains.length === 3
    && m3.orch.chains[0].seq.join('') === 'A' && m3.orch.chains[2].seq.join('') === 'a'
    && m3.orch.motif.join() === '1,3,2' && m3.q === 'bar', JSON.stringify(m3.orch));
  const v2 = { stacks: [s1], cur: 0, view: 'stack', wins: [] };
  const m2 = eng.api.migrate(null, null, null, null, null, v2, null);
  check('V7:v2', m2.v === 7 && m2.orch.chains.length === 1
    && m2.orch.chains[0].seq.join('') === 'A' && m2.winsBy.length === 1);
  const v7bad = { v: 7, stacks: [{...s1, lanes:[null, stack([2],[4]), {bogus:1}]}, s2],
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
  const m7 = eng.api.migrate(v7bad, null, null, null, null, null, null);
  check('V7:v7clamp', m7.cur === 1 && m7.mixBase === 1 && m7.winsBy.length === 2
    && m7.pulse === 0.25 && m7.stacks[0].lanes.length === 1
    && m7.orch.chains[0].seq.join('') === 'AAb'
    && m7.orch.chains[0].orns.length === 1
    && m7.orch.chains[1].orns.length === 0
    && m7.orch.motif.join() === '1,2,2' && m7.q === 'bar' && m7.view === 'orch',
    JSON.stringify(m7.orch));
}

console.log(failures === 0 ? '\nALL GREEN' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
