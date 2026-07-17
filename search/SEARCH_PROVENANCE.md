# Discovery and proof boundary

## Frozen target

The target is a proper six-edge-colouring of the 192 edges of `Q6` whose six
colour classes are perfect matchings and for which every union of one colour
from `{0,1,2}` and one from `{3,4,5}` is a single 64-cycle.

## Stage 1: lazy Boolean constraint search

`solve_lazy_sat.js` introduces a Boolean variable `x[e,c]` for every cube edge
`e` and colour `c`.  Exactly-one constraints impose one colour per edge and one
incident edge of each colour at every vertex.  Thus every model of the base
formula is a labelled 1-factorization.

The six edges `{0,2^c}` are fixed to colour `c`.  This is a sound orbit
normalization obtained from a cube translation, a coordinate permutation, and
factor relabelling within the prescribed two blocks.  For even dimension, the
program also imposes the necessary factorization-sign parity; for `(d,k)=(6,3)`
the target sign is negative.

For each required colour pair, a current model decomposes into alternating
cycles.  If a component has vertex set `S`, any connected target must contain
an edge of one of those two colours across the cut `delta(S)`.  The program adds
this necessary clause and resolves.  Hence these lazy cuts do not remove a
valid Hamiltonian solution.  They are a discovery mechanism: termination at a
round limit is not a proof of nonexistence, and an UNSAT claim would require a
proof-producing encoding and independently checked proof trace.

The historical frozen output `near_witness.json` is a valid 1-factorization
with eight of the nine required cross-pairs Hamiltonian.  Its remaining
cross-pair has cycle lengths 8, 12, and 44.  Its SHA-256 digest is
`9540153c3f9c67236ed3249948845bbd77d9d62d7a3ec68fc7a8b1feaa86f89f`.

On 17 July 2026, a complete replay with Node.js 24.14.0 and
`logic-solver` 2.0.1 reached the same semantic checkpoint at round 5,067 after
adding 89,540 distinct connectivity cuts.  The run took 1,388.831 seconds and
exited with the predeclared near-witness status 31.  Its remaining cross-pair
has cycle lengths 10, 22, and 32.  The regenerated near-witness has digest
`9465cb0dcf00fc13533c0ef49cfcd11daba044370db5bbeab744f68eaeb6d6d4`.
Thus stage 1 is semantically reproduced, not byte-for-byte replayed.

## Stage 2: Kempe-component repair

For colours `a` and `b`, the subgraph formed by their two perfect matchings is a
disjoint union of alternating even cycles.  Interchanging `a` and `b` on any
selected union component preserves a proper six-edge-colouring and therefore
preserves the 1-factorization.

`kempe_search.py` considers all 15 unordered colour pairs.  A global exchange
within either prescribed three-colour block is quotiented as a relabelling.
Cross-block exchanges are retained because they change which pairs are subject
to the nine Hamiltonicity requirements.  Candidate states are ranked by:

1. total component excess over the nine required pairs;
2. number of non-Hamiltonian required pairs;
3. the nine component counts;
4. seeded pseudo-random tie breaking.

For large component-mask families, at most 128 nonempty masks per colour pair
are sampled using seed 1.  The best 2,000 previously unseen states form the next
beam.  Starting from `near_witness.json`, the frozen CPython 3.12.13 replay found
the published certificate at depth 8 after 599,257 distinct states and 134.967
seconds.  The generated file is byte-identical to the reference certificate.

The earlier uncaptured report of 902,324 visited states is not reproduced by
the frozen program and parameters and must not be cited.  This correction has
no mathematical effect because the regenerated certificate is identical.

## End-to-end reproduction from a fresh SAT output

The same Kempe program and parameters were also applied directly to
`near_witness_reproduced.json`, without substituting the historical starting
file.  This run found `certificate_end_to_end.json` at depth 12 after visiting
1,286,206 distinct states in 297.504 seconds.  Its SHA-256 digest is
`98c1d1eef4182bde1679edd3e8f6aa6ec7522f1ae123e8baa68f467034e40222`.
It is not byte-identical to the published certificate, but both independent
verifiers accept it and all nine required cross-pair unions are 64-cycles.

The release therefore supports two different reproducibility claims:

1. **Exact path replay:** the frozen historical near-witness regenerates the
   published certificate byte-for-byte at Kempe depth 8.
2. **End-to-end semantic reproduction:** a new lazy-SAT near-witness is repaired
   to a different, independently accepted certificate at Kempe depth 12.

## Proof boundary

Neither search stage is a logical dependency of the theorem.  The search
programs explain discovery and permit computational replay.  The proof uses
only the explicit certificate, the direct argument in the manuscript, and the
elementary checks performed independently by `verifier.py` and
`verifier_cleanroom.py`.
