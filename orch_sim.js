// Verification harness for stack.html's ORCH engine.
// Slices the SHIPPED code (pure realization + ORCH-CORE markers) out of the
// html and runs it in a vm with a mocked, jittered clock; asserts the emitted
// hit set + switch timeline against an independently-expanded oracle.
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
let stacks=[], wins=[], dirty=true, hits=[], looplen=0;
let t0=0, opSec=0, schedUntil=0, segStart=0, active=0, ovr=null, oQueue=null, q='tick';
let orch=null, setups=null, orchCache=null;
`;
const EPILOGUE = `
__api.init = (o) => { setups=o.setups; orch=o.orch; opSec=o.opSec; q=o.q; t0=o.t0;
  schedUntil=t0; segStart=t0; active=seqSetup(0); ovr=null; oQueue=null;
  orchCache={hits:setups.map(deckHits), lens:setups.map(deckLen)}; };
__api.refresh = () => { orchCache={hits:setups.map(deckHits), lens:setups.map(deckLen)}; };
__api.tap = (i) => { oQueue=i; };
__api.get = () => ({t0, opSec, schedUntil, segStart, active, ovr: ovr?{su:ovr.su,baseSym:ovr.baseSym}:null, oQueue, q});
__api.call = (now, until) => scheduleOrch(now, until);
__api.deckHits = (su) => deckHits(su);
__api.deckLen = (su) => deckLen(su);
__api.seqSetup = (k) => seqSetup(k);
__api.migrate = (a, b, c) => migrateFrom(a, b, c);
`;

function makeEngine() {
  const played = [], events = [];
  const sandbox = {
    PULSE: 0.25, SOUNDS: [[36,'K'],[38,'S'],[42,'H'],[46,'O'],[75,'V']],
    TABN: ['A','B','C','D'], SETUPMAX: 6, Math, JSON,
    playHit: (at, p, v) => played.push([at, p, v]),
    onSwitch: () => {},
    __api: {},
  };
  vm.createContext(sandbox);
  vm.runInContext(PREAMBLE + pureState + pure + core + EPILOGUE, sandbox);
  sandbox.onSwitch = (B) => {
    const g = sandbox.__api.get();
    events.push({ t: B, active: g.active, segStart: g.segStart });
  };
  return { api: sandbox.__api, played, events };
}

// deterministic rng (Date/Math.random-free discipline kept here too)
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

// ---------- independent oracle ----------
// Walks the same clock steps, but expands hits analytically per interval
// (seg + n*len + t) rather than via the engine's incremental tiler.
function oracle(cfg, steps) {
  const { orch: o, opSec, t0 } = cfg;
  let q = cfg.q;
  let su = t0, act = null, seg = t0, ov = null, qu = null;
  let cache = snap(cfg.setups, cfg.deckHits, cfg.deckLen);
  const hits = [], events = [];
  act = cfg.seqSetup(0);
  function snap(setups, dh, dl) { return { hs: setups.map(dh), ls: setups.map(dl) }; }
  function expand(from, to) {
    const hs = cache.hs[act], len = cache.ls[act];
    let n = Math.floor((from - seg) / len);
    for (; seg + n * len < to - 1e-9; n++) {
      const base = seg + n * len;
      for (const [t, p, v] of hs) {
        const at = base + t;
        if (at >= from - 1e-9 && at < to - 1e-9) hits.push([at, p, v]);
      }
    }
  }
  function consum(B, k, viaPulse) {
    const s = cfg.seqSetup(k);
    if (!viaPulse && ov && s !== ov.baseSym) ov = null;
    let next = ov ? ov.su : s;
    if (qu != null) {
      if (qu === s) { ov = null; next = s; }
      else { ov = { su: qu, baseSym: s }; next = qu; }
      qu = null;
    }
    if (next !== act) { act = next; seg = B; }
    events.push({ t: B, active: act, segStart: seg });
  }
  for (const step of steps) {
    if (step.tap !== undefined) { qu = step.tap; continue; }
    if (step.edit) { step.edit(); cache = snap(cfg.setups, cfg.deckHits, cfg.deckLen); continue; }
    if (step.setQ) { q = step.setQ; continue; }
    const { now, until } = step;
    for (;;) {
      const k = Math.floor((su - t0) / opSec + 1e-9) + 1;
      let b = t0 + k * opSec, viaPulse = false;
      if (qu != null && q === 'pulse') {
        const p = t0 + Math.ceil((Math.max(su, now) - t0) / 0.25 - 1e-9) * 0.25;
        if (p < b - 1e-6) { b = p; viaPulse = true; }
      }
      const to = Math.min(until, b);
      if (to > su + 1e-9) { expand(su, to); su = to; }
      if (b <= until + 1e-9) { consum(b, viaPulse ? Math.floor((b - t0) / opSec + 1e-9) : k, viaPulse); su = b; }
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
    if (Math.abs(a.t - b.t) > 1e-6 || a.active !== b.active || Math.abs(a.segStart - b.segStart) > 1e-6) {
      check(name + ':ev', false, `ev ${i}: got t=${a.t.toFixed(4)} a=${a.active} s=${a.segStart.toFixed(4)} want t=${b.t.toFixed(4)} a=${b.active} s=${b.segStart.toFixed(4)}`);
      return;
    }
  }
}

// ---------- scenario driver ----------
function stack(motif, periods, children) { return { motif, periods, children: children || {} }; }
function run(name, cfg0, opts) {
  const eng = makeEngine();
  const cfg = {
    setups: cfg0.setups, orch: cfg0.orch, opSec: cfg0.opulse * 0.25,
    q: cfg0.q || 'tick', t0: cfg0.t0 ?? 100.12,
    deckHits: eng.api.deckHits, deckLen: eng.api.deckLen, seqSetup: eng.api.seqSetup,
  };
  eng.api.init({ setups: cfg.setups, orch: cfg.orch, opSec: cfg.opSec, q: cfg.q, t0: cfg.t0 });
  // snapshot so the oracle can replay edits from the initial state
  const snap = JSON.stringify({ setups: cfg.setups, orch: cfg.orch });
  const r = rng(cfg0.seed ?? 42);
  const dur = cfg0.dur ?? 60;
  const steps = [];
  let now = cfg.t0 - 0.12;
  const acts = opts?.actions ?? [];   // [{at, tap|edit|setQ}] applied when now >= at
  let ai = 0;
  let prevSched = cfg.t0, lastUntil = cfg.t0;
  while (now < cfg.t0 - 0.12 + dur) {
    now += (cfg0.coarse ? 0.15 : 0.04 + r() * 0.03) + (r() < 0.06 ? 0.12 + r() * 0.08 : 0);
    while (ai < acts.length && now >= acts[ai].at) {
      const a = acts[ai++];
      if (a.tap !== undefined) { eng.api.tap(a.tap); steps.push({ tap: a.tap }); }
      if (a.edit) { a.edit(); eng.api.refresh(); steps.push({ edit: a.edit }); }
    }
    const until = now + 0.18;
    eng.api.call(now, until);
    const g = eng.api.get();
    check(name + ':monotonic', g.schedUntil >= prevSched - 1e-9, `schedUntil went backwards`);
    check(name + ':caughtUp', Math.abs(g.schedUntil - until) < 1e-9, `schedUntil ${g.schedUntil} != until ${until}`);
    prevSched = g.schedUntil; lastUntil = until;
    steps.push({ now, until });
  }
  { // restore initial state in place (objects are shared with the engine sandbox)
    const s0 = JSON.parse(snap);
    cfg.setups.forEach((su, i) => { for (const k of Object.keys(su)) delete su[k]; Object.assign(su, s0.setups[i]); });
    for (const k of Object.keys(cfg.orch)) delete cfg.orch[k]; Object.assign(cfg.orch, s0.orch);
  }
  const oc = oracle(cfg, steps);
  matchHits(name, eng.played, oc.hits);
  matchEvents(name, eng.events, oc.events);
  // structural: every tick event on the t0+k*opSec lattice; restart discipline
  let lastActive = null, lastSeg = null;
  for (const e of eng.events) {
    const kf = (e.t - cfg.t0) / cfg.opSec, kr = Math.round(kf);
    const onTick = Math.abs(kf - kr) < 1e-9;
    const pf = (e.t - cfg.t0) / 0.25, pr = Math.round(pf);
    check(name + ':lattice', onTick || Math.abs(pf - pr) < 1e-9, `event off both lattices at ${e.t}`);
    if (lastActive !== null && e.active === lastActive)
      check(name + ':noGhostRestart', Math.abs(e.segStart - lastSeg) < 1e-9, `segStart moved without a switch`);
    lastActive = e.active; lastSeg = e.segStart;
  }
  return { eng, cfg };
}

// ---------- setups used across scenarios ----------
const A = { name: '', stacks: [stack([1,2,3], [16, 8])], cur: 0, view: 'stack', wins: [], deck: 'A' };
const B = { name: '', stacks: [stack([2,1], [9], {0:{S:3,m:[1,0,4]}})], cur: 0, view: 'stack', wins: [], deck: 'A' };  // incl. rest (0)
const C = { name: '', stacks: [stack([1,2,3], [8]), stack([4,5], [6])], cur: 0, view: 'mix',
            wins: [{tab:1, a:0.5, b:1.5}], deck: 'MIX' };
const D = { name: '', stacks: [stack([3,1,2,1], [10, 7])], cur: 0, view: 'stack', wins: [], deck: 'A' };

console.log('S1 sequence fidelity (random orchs, mixed decks incl MIX)');
run('S1a', { setups: [A, B], orch: { periods: [5], motif: [1, 2] }, opulse: 4, dur: 120, seed: 7 });
run('S1b', { setups: [A, B, C], orch: { periods: [7, 4], motif: [1, 2, 3] }, opulse: 6, dur: 120, seed: 11 });
run('S1c', { setups: [A, C, D], orch: { periods: [9, 5, 3], motif: [2, 1, 3] }, opulse: 3, dur: 120, seed: 13 });

console.log('S2 run continuation vs restart (motif 1,1,2)');
{
  const { eng, cfg } = run('S2', { setups: [A, B], orch: { periods: [], motif: [1, 1, 2] }, opulse: 4, dur: 60, seed: 3 });
  // setup changes only where the realized symbol changes: k%3: 0,1 -> setup0; 2 -> setup1
  for (const e of eng.events) {
    const k = Math.round((e.t - cfg.t0) / cfg.opSec);
    if (k % 3 === 1) { // tick 1 continues setup0's run - segStart must predate this tick
      check('S2:continuation', e.segStart < e.t - 1e-9, `restart at continuation tick k=${k}`);
    }
  }
}

console.log('S3 opulse=1 (multiple boundaries per horizon, with stalls)');
run('S3', { setups: [A, B], orch: { periods: [5], motif: [1, 2] }, opulse: 1, dur: 45, seed: 5 });

console.log('S4 live override, q=tick');
{
  const { eng, cfg } = run('S4', { setups: [A, B, D], orch: { periods: [], motif: [1] }, opulse: 4, dur: 40, seed: 9 },
    { actions: [{ at: 103.0, tap: 1 }, { at: 112.3, tap: 2 }, { at: 121.9, tap: 0 }] });
  check('S4:switched', eng.events.some(e => e.active === 1) && eng.events.some(e => e.active === 2), 'overrides never landed');
  for (const e of eng.events) {
    const kf = (e.t - cfg.t0) / cfg.opSec;
    check('S4:onTick', Math.abs(kf - Math.round(kf)) < 1e-9, `q=tick landed off-tick at ${e.t}`);
  }
}

console.log('S5 live override, q=pulse (incl. seamless early-jump)');
{
  // motif [1,2] opulse 8: tap setup2 (idx1) mid-tick0; expect pulse landing, then NO restart at tick1
  const { eng, cfg } = run('S5', { setups: [A, B], orch: { periods: [], motif: [1, 2] }, opulse: 8, q: 'pulse', dur: 20, seed: 21 },
    { actions: [{ at: 100.5, tap: 1 }] });
  const sw = eng.events.filter((e, i, a) => i === 0 ? true : e.active !== a[i - 1].active);
  check('S5:earlyLand', sw.length >= 1 && sw[0].active === 1, 'override did not land');
  const pf = (sw[0].t - cfg.t0) / 0.25;
  check('S5:onPulse', Math.abs(pf - Math.round(pf)) < 1e-9, 'pulse landing off-grid');
  check('S5:midTick', sw[0].t < cfg.t0 + cfg.opSec - 1e-9, 'landed at tick, not early pulse');
  // at tick1 the sequence itself reaches setup2: override clears, no second restart
  const tick1 = eng.events.find(e => Math.abs(e.t - (cfg.t0 + cfg.opSec)) < 1e-9);
  check('S5:seamless', tick1 && tick1.active === 1 && Math.abs(tick1.segStart - sw[0].t) < 1e-9,
    'seamless jump restarted at tick1');
}

console.log('S5b cancel gesture (tap the sequence\'s own symbol)');
{
  // override to setup1 during a long setup0 stretch, then tap setup0 -> returns to sequence
  const { eng } = run('S5b', { setups: [A, B], orch: { periods: [], motif: [1] }, opulse: 4, dur: 30, seed: 23 },
    { actions: [{ at: 102.0, tap: 1 }, { at: 108.0, tap: 0 }] });
  const last = eng.events[eng.events.length - 1];
  check('S5b:returned', last.active === 0, 'did not return to sequence');
  const g = eng.api.get();
  check('S5b:ovrCleared', g.ovr === null, 'override survived the cancel');
}

console.log('S7 float robustness (long run, odd opulse, large t0)');
run('S7', { setups: [A, B], orch: { periods: [11, 4], motif: [1, 2] }, opulse: 3, dur: 1800, t0: 1000000.12, coarse: true, seed: 31 });

console.log('S8 mid-play edits (deck contents + orch pattern)');
{
  const su2 = JSON.parse(JSON.stringify(B));
  const orch8 = { periods: [6], motif: [1, 2] };
  run('S8', { setups: [A, su2], orch: orch8, opulse: 4, dur: 60, seed: 17 }, {
    actions: [
      { at: 105.0, edit: () => { su2.stacks[0].motif = [2, 1, 3]; } },
      { at: 118.0, edit: () => { su2.stacks[0].periods = [7]; } },
      { at: 131.0, edit: () => { orch8.motif = [2, 1]; } },
    ],
  });
}

console.log('S9 migration (v2 wrap, v1 wrap, v3 clamp; inputs untouched)');
{
  const eng = makeEngine();
  const v2 = { stacks: [stack([1, 2], [12], {1:{S:2,m:[3,4]}}), stack([5], [4])], cur: 1, view: 'mix',
               wins: [{ tab: 1, a: 1, b: 2 }] };
  const v2snap = JSON.stringify(v2);
  const m2 = eng.api.migrate(null, JSON.parse(v2snap), null);
  check('S9:v2shape', m2.v === 3 && m2.setups.length === 1 && m2.setups[0].deck === 'MIX'
    && m2.setups[0].cur === 1 && m2.orch.motif.length === 1 && m2.oview === 'setup', JSON.stringify(m2).slice(0, 120));
  const v2b = JSON.parse(v2snap);
  eng.api.migrate(null, v2b, null);
  check('S9:v2untouched', JSON.stringify(v2b) === v2snap, 'migration mutated v2 input');
  const m1 = eng.api.migrate(null, null, { motif: [2, 3], periods: [9] });
  check('S9:v1shape', m1.v === 3 && m1.setups[0].stacks[0].motif.join() === '2,3' && m1.setups[0].deck === 'A');
  const m0 = eng.api.migrate(null, null, null);
  check('S9:empty', m0.v === 3 && m0.setups[0].stacks[0].motif.join() === '1,2,3');
  const v3 = { v: 3, setups: [A, B], curSetup: 9, oview: 'orch', orch: { periods: [4], motif: [1, 5, 2] }, opulse: 8, q: 'weird' };
  const m3 = eng.api.migrate(v3, null, null);
  check('S9:v3clamp', m3.curSetup === 1 && m3.orch.motif.join() === '1,2,2' && m3.q === 'tick' && m3.oview === 'orch');
}

console.log(failures === 0 ? '\nALL GREEN' : `\n${failures} FAILURES`);
process.exit(failures === 0 ? 0 : 1);
