// Dual-verify conformance.json against the JS reference (sliced live out of
// stack.html), then append mix vectors computed by that same sliced code.
// Only vectors both references agree on ship.
'use strict';
const fs = require('fs'), vm = require('vm'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, 'stack.html'), 'utf8');
function slice(a, b) {
  const i = html.indexOf(a), j = html.indexOf(b);
  if (i < 0 || j < 0) throw new Error('marker missing: ' + a);
  return html.slice(i + a.length, j);
}
const sandbox = {
  PULSE: 1, SOUNDS: [[36,'K'],[38,'S'],[42,'H'],[46,'O'],[75,'V'],[49,'C'],[40,'N']],
  TABN: ['A','B','C','D','E','F','G','H'], UPS: 'ABCDEFGH', LOS: 'abcdefgh',
  Math, JSON, __x: {},
};
vm.createContext(sandbox);
vm.runInContext(`
let stacks=[], wins=[], winsBy=[], mixBase=0, dirty=true, hits=[], looplen=0;
` + slice('// --- realization ---', '// --- tabs ---') + `
__x.tab = (lanes) => { const s = {...lanes[0], lanes: lanes.slice(1)}; return realizeTabHits(s); };
__x.mix = (ss, ws, base) => { stacks = ss; winsBy = []; return realizeMixHits(ss, ws, base); };
`, sandbox);

const SCALE = 84000;   // 840*100: unflexed times divide 840, flex adds denom 100*S
const x84k = (t, name) => {
  const x = t * SCALE;
  if (Math.abs(x - Math.round(x)) > 1e-6) throw new Error(`${name}: off-grid time ${t}`);
  return Math.round(x);
};
const key = h => h.join('|');

const doc = JSON.parse(fs.readFileSync('conformance.json', 'utf8'));
let bad = 0;
for (const v of doc.vectors.filter(v => v.kind === 'tab')) {
  const lanes = v.lanes.map(l => ({ periods: l.periods, offs: l.offs, steps: l.steps,
    motif: l.motif, children: l.children, phase: l.phase, flex: l.flex }));
  const got = sandbox.__x.tab(lanes).map(([t, p, w]) => [x84k(t, v.name), p, w])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]).map(key).sort();
  const want = v.hits.map(key).sort();
  const ok = got.length === want.length && got.every((g, i) => g === want[i]);
  if (!ok) { bad++; console.log(`DISAGREE ${v.name}: js ${got.length} vs py ${want.length}`); }
  else console.log(`ok ${v.name} (${want.length} events, dual-verified)`);
}
if (bad) { console.log(`${bad} disagreements - NOT shipping`); process.exit(1); }

// ---- mix vectors (JS reference is the authority; windows are page-native) ----
const st = (motif, periods, extra) => ({ motif, periods, children: {}, ...extra });
const MIXES = [
  { name: 'mix-two-windows', ground: 0,
    stacks: [ st([1,2,3],[16]), st([2,1],[9],{phase:2}), st([3,0,-2,1],[10]) ],
    wins: [ {tab:1,a:2,b:6}, {tab:2,a:10,b:13} ] },
  { name: 'mix-inert-and-order', ground: 1,
    stacks: [ st([1,0,7,0],[8]), st([2,1],[9]), st([3,4],[6]) ],
    wins: [ {tab:1,a:1,b:4}, {tab:0,a:2,b:5}, {tab:2,a:5,b:8} ] },  // first inert (=ground), overlap order matters
];
doc.vectors = doc.vectors.filter(v => v.kind !== 'mix');
for (const m of MIXES) {
  const hits = sandbox.__x.mix(m.stacks, m.wins, m.ground)
    .map(([t, p, w]) => [x84k(t, m.name), p, w])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  doc.vectors.push({ name: m.name, kind: 'mix', pulse: 1, ground: m.ground,
    stacks: m.stacks, wins: m.wins, hits });
  console.log(`ok ${m.name} (${hits.length} events, mix)`);
}
fs.writeFileSync('conformance.json', JSON.stringify(doc, null, 1));
console.log(`conformance.json final: ${doc.vectors.length} vectors`);
