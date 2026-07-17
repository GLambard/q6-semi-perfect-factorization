#!/usr/bin/env node
/* Lazy connectivity-cut SAT search for k-semi-perfect factorizations of Q_d.
 *
 * The SAT core enforces a proper d-edge-colouring of Q_d.  For every current
 * disconnected bichromatic 2-factor, a valid Hamiltonian solution must select
 * an edge of one of the two colours across each component cut.  Those clauses
 * are added incrementally until a witness is found or the formula is UNSAT.
 */
'use strict';

const fs = require('fs');
const path = require('path');
// logic-solver bundles an old Emscripten MiniSat image with a fixed 64 MiB
// heap.  Load that image with a larger heap in memory; no dependency file is
// modified, and the SAT algorithm itself is unchanged.
const NodeModule = require('module');
const originalJsLoader = NodeModule._extensions['.js'];
NodeModule._extensions['.js'] = function loadWithLargerMiniSatHeap(module, filename) {
  if (filename.endsWith(`${path.sep}logic-solver${path.sep}minisat.js`)) {
    let source = fs.readFileSync(filename, 'utf8');
    const marker = 'var Module;if(!Module)';
    if (!source.includes(marker)) throw new Error('unexpected logic-solver minisat.js format');
    source = source.replace(marker, 'var Module={TOTAL_MEMORY:536870912};if(!Module)');
    module._compile(source, filename);
    return;
  }
  originalJsLoader(module, filename);
};
const Logic = require('logic-solver');
NodeModule._extensions['.js'] = originalJsLoader;

function usage() {
  console.error('usage: node solve_lazy_sat.js [dimension=6] [left_size=3] [output=candidate.json] [max_rounds=0]');
  process.exit(2);
}

function edgeKey(u, v) {
  return u < v ? `${u}-${v}` : `${v}-${u}`;
}

function variable(edgeId, colour) {
  return `x_${edgeId}_${colour}`;
}

function seededShuffle(values, seedBox) {
  const result = values.slice();
  for (let i = result.length - 1; i > 0; i--) {
    seedBox.value = (1664525 * seedBox.value + 1013904223) >>> 0;
    const j = seedBox.value % (i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

function components(mateA, mateB, vertexCount) {
  const unseen = new Set(Array.from({ length: vertexCount }, (_, i) => i));
  const result = [];
  while (unseen.size) {
    const start = unseen.values().next().value;
    const stack = [start];
    const component = [];
    unseen.delete(start);
    while (stack.length) {
      const u = stack.pop();
      component.push(u);
      for (const v of [mateA[u], mateB[u]]) {
        if (unseen.delete(v)) stack.push(v);
      }
    }
    result.push(component.sort((a, b) => a - b));
  }
  return result.sort((a, b) => a.length - b.length || a[0] - b[0]);
}

function canonicalSide(component, vertexCount) {
  if (component.length < vertexCount / 2) return component;
  const inside = new Set(component);
  const complement = Array.from({ length: vertexCount }, (_, i) => i).filter((v) => !inside.has(v));
  if (component.length > vertexCount / 2) return complement;
  const a = component.join(',');
  const b = complement.join(',');
  return a <= b ? component : complement;
}

function main() {
  const d = Number(process.argv[2] || 6);
  const k = Number(process.argv[3] || 3);
  const output = process.argv[4] || path.join(__dirname, 'candidate.json');
  const maxRounds = Number(process.argv[5] || 0);
  if (!Number.isInteger(d) || d < 2 || d > 8 || !Number.isInteger(k) || k < 1 || k >= d ||
      !Number.isInteger(maxRounds) || maxRounds < 0) usage();

  const vertexCount = 1 << d;
  const searchSeed = Number(process.env.Q6_SEED || 1) >>> 0;
  const seedBox = { value: searchSeed };
  const edges = [];
  const edgeId = new Map();
  const incident = Array.from({ length: vertexCount }, () => []);
  for (let u = 0; u < vertexCount; u++) {
    for (let direction = 0; direction < d; direction++) {
      const v = u ^ (1 << direction);
      if (u < v) {
        const id = edges.length;
        edges.push([u, v]);
        edgeId.set(edgeKey(u, v), id);
        incident[u].push(id);
        incident[v].push(id);
      }
    }
  }

  const solver = new Logic.Solver();
  for (const id of seededShuffle(Array.from({ length: edges.length }, (_, i) => i), seedBox)) {
    solver.require(Logic.exactlyOne(Array.from({ length: d }, (_, c) => variable(id, c))));
  }
  for (const v of seededShuffle(Array.from({ length: vertexCount }, (_, i) => i), seedBox)) {
    for (let c = 0; c < d; c++) {
      solver.require(Logic.exactlyOne(seededShuffle(incident[v], seedBox).map((id) => variable(id, c))));
    }
  }
  for (let c = 0; c < d; c++) {
    solver.require(variable(edgeId.get(edgeKey(0, 1 << c)), c));
  }

  const referencePath = process.env.Q6_REFERENCE;
  const maxChangesText = process.env.Q6_MAX_CHANGES;
  if (referencePath || maxChangesText !== undefined) {
    if (!referencePath || maxChangesText === undefined) {
      throw new Error('Q6_REFERENCE and Q6_MAX_CHANGES must be supplied together');
    }
    const maxChanges = Number(maxChangesText);
    if (!Number.isInteger(maxChanges) || maxChanges < 0 || maxChanges > edges.length) {
      throw new Error('invalid Q6_MAX_CHANGES');
    }
    const reference = JSON.parse(fs.readFileSync(referencePath, 'utf8'));
    const originalColour = Array(edges.length).fill(-1);
    for (let c = 0; c < d; c++) for (const [u0, v0] of reference.matchings[c]) {
      const id = edgeId.get(edgeKey(u0, v0));
      if (id === undefined || originalColour[id] !== -1) throw new Error('invalid reference');
      originalColour[id] = c;
    }
    if (originalColour.some(c => c < 0)) throw new Error('reference omits cube edges');
    const changed = originalColour.map((c, id) => Logic.not(variable(id, c)));
    solver.require(Logic.lessThanOrEqual(Logic.sum(changed), Logic.constantBits(maxChanges)));
    console.error(JSON.stringify({ reference: referencePath, max_changed_edges: maxChanges }));
  }

  // For even d, the factorization sign is the product of the signs of the
  // d matching permutations E_even -> E_odd.  A target K_{k,d-k} has sign
  // (-1)^(k(d-k)).  Encoding this necessary invariant prevents the search
  // from spending time in the directional (+1) sign class when d=6,k=3.
  if ((d & 1) === 0 && process.env.Q6_SKIP_SIGN !== '1') {
    const even = [];
    const odd = [];
    for (let v = 0; v < vertexCount; v++) {
      let parity = 0;
      for (let x = v; x; x >>= 1) parity ^= x & 1;
      (parity === 0 ? even : odd).push(v);
    }
    const oddIndex = new Map(odd.map((v, i) => [v, i]));
    const inversions = [];
    for (let c = 0; c < d; c++) {
      for (let p = 0; p < even.length; p++) {
        const u = even[p];
        for (let q = p + 1; q < even.length; q++) {
          const w = even[q];
          for (let du = 0; du < d; du++) {
            const v = u ^ (1 << du);
            for (let dw = 0; dw < d; dw++) {
              const z = w ^ (1 << dw);
              if (oddIndex.get(v) <= oddIndex.get(z)) continue;
              inversions.push(Logic.and(
                variable(edgeId.get(edgeKey(u, v)), c),
                variable(edgeId.get(edgeKey(w, z)), c)
              ));
            }
          }
        }
      }
    }
    const oddTargetSign = (k * (d - k)) & 1;
    if (oddTargetSign) solver.require(Logic.xor(inversions));
    else solver.forbid(Logic.xor(inversions));
    console.error(JSON.stringify({ factorization_sign_parity: oddTargetSign, inversion_terms: inversions.length }));
  }

  const seenCuts = new Set();
  const lockedPairs = new Set();
  const lockSuccessfulPairs = process.env.Q6_LOCK_PAIRS === '1';
  const stopAtBadPairs = Number(process.env.Q6_STOP_AT_BAD_PAIRS || 0);
  let bestBadPairs = Number.POSITIVE_INFINITY;
  let bestComponentExcess = Number.POSITIVE_INFINITY;

  function lockHamiltonPair(a, b) {
    const evenVertices = [];
    for (let v = 0; v < vertexCount; v++) {
      let parity = 0;
      for (let x = v; x; x >>= 1) parity ^= x & 1;
      if (parity === 0) evenVertices.push(v);
    }
    const half = evenVertices.length;
    const rankName = (u, t) => `r_${a}_${b}_${u}_${t}`;
    for (const u of evenVertices) {
      solver.require(Logic.exactlyOne(Array.from({ length: half }, (_, t) => rankName(u, t))));
    }
    solver.require(rankName(0, 0));
    for (const u of evenVertices) {
      for (let firstDirection = 0; firstDirection < d; firstDirection++) {
        const v = u ^ (1 << firstDirection);
        const firstId = edgeId.get(edgeKey(u, v));
        for (let secondDirection = 0; secondDirection < d; secondDirection++) {
          if (secondDirection === firstDirection) continue;
          const w = v ^ (1 << secondDirection);
          const secondId = edgeId.get(edgeKey(v, w));
          for (let t = 0; t < half; t++) {
            solver.require(Logic.implies(
              Logic.and(variable(firstId, a), variable(secondId, b), rankName(u, t)),
              rankName(w, (t + 1) % half)
            ));
          }
        }
      }
    }
  }

  const started = Date.now();
  console.error(JSON.stringify({ search_seed: searchSeed, lock_successful_pairs: lockSuccessfulPairs }));
  let round = 0;
  while (maxRounds === 0 || round < maxRounds) {
    round++;
    const solution = solver.solve();
    if (!solution) {
      console.error(JSON.stringify({ result: 'unsat', rounds: round, cuts: seenCuts.size,
                                     elapsed_ms: Date.now() - started }));
      process.exit(20);
    }
    const truth = solution.getMap();
    const matchings = Array.from({ length: d }, () => []);
    const mates = Array.from({ length: d }, () => Array(vertexCount).fill(-1));
    for (let id = 0; id < edges.length; id++) {
      const [u, v] = edges[id];
      let selected = -1;
      for (let c = 0; c < d; c++) {
        if (truth[variable(id, c)]) {
          if (selected !== -1) throw new Error(`edge ${id} has multiple colours`);
          selected = c;
        }
      }
      if (selected === -1) throw new Error(`edge ${id} has no colour`);
      matchings[selected].push([u, v]);
      mates[selected][u] = v;
      mates[selected][v] = u;
    }

    let badPairs = 0;
    let componentExcess = 0;
    let added = 0;
    let newlyLocked = 0;
    for (let a = 0; a < k; a++) {
      for (let b = k; b < d; b++) {
        const comps = components(mates[a], mates[b], vertexCount);
        if (comps.length === 1) {
          const pairKey = `${a}-${b}`;
          if (lockSuccessfulPairs && !lockedPairs.has(pairKey)) {
            lockHamiltonPair(a, b);
            lockedPairs.add(pairKey);
            newlyLocked++;
          }
          continue;
        }
        badPairs++;
        componentExcess += comps.length - 1;
        for (const component of comps) {
          const side = canonicalSide(component, vertexCount);
          if (side.length === 0) continue;
          const inside = new Set(side);
          const boundaryIds = [];
          for (let id = 0; id < edges.length; id++) {
            const [u, v] = edges[id];
            if (inside.has(u) !== inside.has(v)) boundaryIds.push(id);
          }
          const key = `${a}-${b}:${boundaryIds.join(',')}`;
          if (seenCuts.has(key)) continue;
          seenCuts.add(key);
          const literals = [];
          for (const id of boundaryIds) literals.push(variable(id, a), variable(id, b));
          // Under the base 2-regularity constraints every cut has even size,
          // so this nonempty-boundary clause is equivalent to at least two.
          solver.require(Logic.or(literals));
          added++;
        }
      }
    }

    if (badPairs < bestBadPairs || (badPairs === bestBadPairs && componentExcess < bestComponentExcess)) {
      bestBadPairs = badPairs;
      bestComponentExcess = componentExcess;
      fs.writeFileSync(`${output}.best.json`, JSON.stringify({ matchings }, null, 2) + '\n');
      console.error(JSON.stringify({ best_bad_pairs: bestBadPairs,
                                     best_component_excess: bestComponentExcess,
                                     best_output: `${output}.best.json` }));
    }

    if (badPairs === 0) {
      fs.writeFileSync(output, JSON.stringify({ matchings }, null, 2) + '\n');
      console.error(JSON.stringify({ result: 'sat', rounds: round, cuts: seenCuts.size,
                                     elapsed_ms: Date.now() - started, output }));
      return;
    }
    if (stopAtBadPairs > 0 && badPairs <= stopAtBadPairs) {
      console.error(JSON.stringify({ result: 'near_witness', bad_pairs: badPairs,
                                     component_excess: componentExcess,
                                     rounds: round, cuts: seenCuts.size,
                                     elapsed_ms: Date.now() - started,
                                     output: `${output}.best.json` }));
      process.exit(31);
    }
    if (added === 0) throw new Error('disconnected model produced no new connectivity cut');
    if (round <= 10 || round % 100 === 0) {
      console.error(JSON.stringify({ round, bad_pairs: badPairs, component_excess: componentExcess,
                                     added_cuts: added, total_cuts: seenCuts.size,
                                     newly_locked_pairs: newlyLocked, locked_pairs: lockedPairs.size,
                                     elapsed_ms: Date.now() - started }));
    }
  }
  console.error(JSON.stringify({ result: 'round_limit', rounds: round, cuts: seenCuts.size,
                                 elapsed_ms: Date.now() - started }));
  process.exit(30);
}

try {
  main();
} catch (error) {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
}
