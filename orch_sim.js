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
`;
const EPILOGUE = `
__api.buildCache = () => {
  const by={};
  for(const L of UPS+LOS) by[L]={hits:letterHits(L), len:letterLen(L)};
  orchCache={by, seq:flatLetters(), chains:orch.chains.map(c=>c.slice())};
  if(wi>=orchCache.seq.length) wi=0;
  curHits=orchCache.by[curLetter].hits; curLen=orchCache.by[curLetter].len;
};
__api.init = (o) => { stacks=o.stacks; winsBy=o.winsBy||[[],[],[],[]]; orch=o.orch; q=o.q; t0=o.t0;
  mixBase=o.mixBase||0; wins=winsBy[mixBase]||[];
  schedUntil=t0; wi=0; inj=null; oQueue=null;
  const by={};
  for(const L of UPS+LOS) by[L]={hits:letterHits(L), len:letterLen(L)};
  orchCache={by, seq:flatLetters(), chains:orch.chains.map(c=>c.slice())};
  advance(t0); };
__api.tap = (i) => { oQueue=i; };
__api.get = () => ({t0, schedUntil, segStart, wi, inj: inj?{idx:inj.idx,n:inj.list.length,chain:inj.chain}:null,
  oQueue, curLetter, curLen, activeChain, q});
__api.call = (now, until) => scheduleOrch(now, until);
__api.letterHits = (L) => letterHits(L);
__api.letterLen = (L) => letterLen(L);
__api.flatLetters = () => flatLetters();
__api.migrate = (a, b, c, d, e) => migrateFrom(a, b, c, d, e);
`;

function makeEngine() {
  const played = [], events = [];
  const sandbox = {
    PULSE: 0.25, SOUNDS: [[36,'K'],[38,'S'],[42,'H'],[46,'O'],[75,'V']],
    TABN: ['A','B','C','D','E','F','G','H'], UPS: 'ABCDEFGH', LOS: 'abcdefgh',
    CHAINMAX: 6, Math, JSON,
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
  function build() {
    const by = {};
    for (const L of 'ABCDEFGH' + 'abcdefgh') by[L] = { hits: cfg.letterHits(L), len: cfg.letterLen(L) };
    return { by, seq: cfg.flatLetters(), chains: cfg.orch.chains.map(c => c.slice()) };
  }
  function adv(B) {
    if (injO && injO.idx >= injO.list.length) injO = null;
    if (quO != null) {
      const c = cache.chains[quO];
      injO = { list: (c && c.length) ? c : ['A'], idx: 0, chain: quO + 1 };
      quO = null;
    }
    if (injO) { letter = injO.list[injO.idx++]; chainNo = injO.chain; }
    else { const e = cache.seq[wiO]; letter = e[0]; chainNo = e[1]; wiO = (wiO + 1) % cache.seq.length; }
    len = cache.by[letter].len; hs = cache.by[letter].hits; seg = B;
    events.push({ t: B, letter, chain: chainNo, segStart: seg });
  }
  adv(t0);
  for (const step of steps) {
    if (step.tap !== undefined) { quO = step.tap; continue; }
    if (step.edit) { step.edit(); cache = build(); if (wiO >= cache.seq.length) wiO = 0;
      len = cache.by[letter].len; hs = cache.by[letter].hits; continue; }
    const { now, until } = step;
    for (;;) {
      let b = seg + len;
      if (quO != null && q === 'pulse') {
        const p = t0 + Math.ceil((Math.max(su, now) - t0) / 0.25 - 1e-9) * 0.25;
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
function run(name, cfg0, opts) {
  const eng = makeEngine();
  const cfg = {
    stacks: cfg0.stacks, winsBy: cfg0.winsBy || [[],[],[],[]], orch: cfg0.orch,
    q: cfg0.q || 'bar', t0: cfg0.t0 ?? 100.12,
    letterHits: eng.api.letterHits, letterLen: eng.api.letterLen, flatLetters: eng.api.flatLetters,
  };
  eng.api.init({ stacks: cfg.stacks, winsBy: cfg.winsBy, orch: cfg.orch, q: cfg.q, t0: cfg.t0,
    mixBase: cfg0.mixBase || 0 });
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
  // structural: every boundary sits exactly on the pulse grid (bar lens are 0.25-multiples)
  for (const e of eng.events) {
    const pf = (e.t - cfg.t0) / 0.25;
    check(name + ':grid', Math.abs(pf - Math.round(pf)) < 1e-9, `boundary off pulse grid at ${e.t}`);
  }
  return { eng, cfg };
}

// ---------- fixtures: one workspace, tabs of different lengths ----------
function ws() {
  return {
    stacks: [
      stack([1,2,3], [16]),                          // A: 4.00s
      { ...stack([2,1], [9], {0:{S:3,m:[1,0,4],p:1}}), phase: 2 },  // B: 2.25s, phased + child phase
      stack([3,1,2,1], [10, 7]),                      // C: 2.50s
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
  run('V1a', { ...w, orch: { motif: [1,2], chains: [['A'],['B','A']] }, dur: 90, seed: 7 });
  const w2 = ws();
  run('V1b', { ...w2, orch: { motif: [1,2,3,2], chains: [['A','B','A'],['a','B'],['C']] }, dur: 120, seed: 11 });
  const w3 = ws();
  run('V1c', { ...w3, orch: { motif: [2,2,1], chains: [['a'],['B','C','B','A']] }, dur: 120, seed: 13 });
  const w4 = ws();                                  // all three mixes as letters in one arrangement
  run('V1d', { ...w4, orch: { motif: [1,2], chains: [['b','A','c'],['a','b']] }, dur: 120, seed: 19 });
  const w5 = ws();                                  // 5 tabs: E/e in play
  w5.stacks.push(stack([2,3], [6]));                // E: 1.50s
  w5.stacks.push(stack([1,4,2], [12]));             // E is idx 3... push twice -> idx 3,4
  w5.winsBy = [[],[],[],[{tab:0,a:0.25,b:1.0}],[{tab:3,a:0.5,b:2.0}]];
  run('V1e', { ...w5, orch: { motif: [1,2], chains: [['E','e','A'],['d','E']] }, dur: 100, seed: 29 });
}

console.log('V2 inject-then-resume (q=bar)');
{
  const w = ws();
  const { eng } = run('V2', { ...w, orch: { motif: [1,1,2], chains: [['A'],['B','C','B']] }, dur: 60, seed: 9 },
    { actions: [{ at: 106.0, tap: 1 }, { at: 125.0, tap: 0 }] });
  check('V2:injected', eng.events.some(e => e.chain === 2), 'injection never played');
}

console.log('V3 pulse-quantized injection (cuts the bar mid-flight)');
{
  const w = ws();
  const { eng, cfg } = run('V3', { ...w, orch: { motif: [1], chains: [['A'],['B','B']] }, q: 'pulse', dur: 40, seed: 21 },
    { actions: [{ at: 101.3, tap: 1 }] });
  // the injection boundary must land mid-bar (A is 4s; tap at ~1.3s in)
  const cut = eng.events.find(e => e.chain === 2);
  check('V3:cutMidBar', cut && Math.abs((cut.t - cfg.t0) / 4.0 - Math.round((cut.t - cfg.t0) / 4.0)) > 1e-6,
    'pulse cut landed on a bar boundary instead');
}

console.log('V4 pre-emption (tap during an injection)');
{
  const w = ws();
  run('V4', { ...w, orch: { motif: [1], chains: [['A'],['B','B','B','B'],['C','C']] }, dur: 50, seed: 23 },
    { actions: [{ at: 105.0, tap: 1 }, { at: 108.0, tap: 2 }] });
}

console.log('V5 mid-play edits (chains, motif, tab periods)');
{
  const w = ws();
  const orch5 = { motif: [1,2], chains: [['A'],['B','C']] };
  run('V5', { ...w, orch: orch5, dur: 70, seed: 17 }, {
    actions: [
      { at: 108.0, edit: () => { orch5.chains[1] = ['C','B','C']; } },
      { at: 122.0, edit: () => { orch5.motif = [2,1,1]; } },
      { at: 137.0, edit: () => { w.stacks[1].periods = [11]; } },
      { at: 151.0, edit: () => { w.stacks[0].phase = 5; } },
    ],
  });
}

console.log('V6 long run, exact grid (dyadic bar lengths, no drift)');
{
  const w = ws();
  run('V6', { ...w, orch: { motif: [1,2,3,2,1], chains: [['A','B'],['c'],['a','B','b']] },
    dur: 1800, t0: 1000000.12, coarse: true, seed: 31 });
}

console.log('V7 migration (v4 wins+M->winsBy+lowercase, v3 chain, v5 clamp)');
{
  const eng = makeEngine();
  const s1 = stack([1,2], [12]), s2 = stack([3], [8]);
  const v4 = { v: 4, stacks: [s1, s2], cur: 0, view: 'mix', mixBase: 1,
    wins: [{tab:0,a:1,b:2}], orch: { motif: [1,2], chains: [['M','A'],['B']] }, q: 'pulse' };
  const m4 = eng.api.migrate(null, v4, null, null, null);
  check('V7:v4', m4.v === 5 && m4.winsBy.length === 2
    && m4.winsBy[1].length === 1 && m4.winsBy[0].length === 0
    && m4.orch.chains[0].join('') === 'bA' && m4.orch.chains[1].join('') === 'B'
    && m4.q === 'pulse' && m4.mixBase === 1, JSON.stringify(m4.orch) + JSON.stringify(m4.winsBy));
  const v3 = { v: 3,
    setups: [
      { stacks: [s1, s2], cur: 0, view: 'stack', wins: [{tab:1,a:1,b:2}], deck: 'A' },
      { stacks: [s1], cur: 0, view: 'stack', wins: [], deck: 'B' },
      { stacks: [s1, s2], cur: 1, view: 'mix', wins: [], deck: 'MIX' },
    ],
    curSetup: 0, oview: 'orch', orch: { periods: [4], motif: [1, 3, 2] }, opulse: 8, q: 'tick' };
  const m3 = eng.api.migrate(null, null, v3, null, null);
  check('V7:v3', m3.v === 5 && m3.orch.chains.length === 3
    && m3.orch.chains[0].join('') === 'A' && m3.orch.chains[1].join('') === 'B'
    && m3.orch.chains[2].join('') === 'a'          // M -> mix of base 0
    && m3.orch.motif.join() === '1,3,2' && m3.q === 'bar' && m3.stacks.length === 2,
    JSON.stringify(m3.orch));
  const v2 = { stacks: [s1], cur: 0, view: 'stack', wins: [] };
  const m2 = eng.api.migrate(null, null, null, v2, null);
  check('V7:v2', m2.v === 5 && m2.orch.chains.length === 1 && m2.orch.motif.join() === '1'
    && m2.winsBy.length === 1);
  const v5bad = { v: 5, stacks: [s1, s2], cur: 9, view: 'orch', mixBase: 7,
    winsBy: [[{tab:1,a:0,b:1}]],
    orch: { motif: [1, 9, 2], chains: [['A','Z','b'],['B']] }, q: 'weird' };
  const m5 = eng.api.migrate(v5bad, null, null, null, null);
  check('V7:v5clamp', m5.cur === 1 && m5.mixBase === 1 && m5.winsBy.length === 2
    && m5.orch.chains[0].join('') === 'AAb'
    && m5.orch.motif.join() === '1,2,2' && m5.q === 'bar' && m5.view === 'orch');
}

console.log(failures === 0 ? '\nALL GREEN' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
