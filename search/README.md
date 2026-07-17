# Search provenance for the exceptional Q6 certificate

This directory records how the explicit certificate was discovered.  It is
separate from the proof: the theorem is established by the certificate and the
independent verifiers, not by trusting either search program.

The reproducible certificate-producing command is:

```bash
python3 run_logged.py \
  --log kempe_replay.log \
  --status kempe_replay.status \
  python3 kempe_search.py near_witness.json certificate_replay.json \
  --beam 2000 --depth 20 --mask-cap 128 --seed 1
```

On Python 3.12.13 this reaches a solution at trade depth 8 after visiting
599,257 distinct states.  `certificate_replay.json` must have SHA-256 digest
`3d3a476aa481ac0e5a0fd51e3f4a677d8dadf5ec3c000ed0f972dee1982bf8db`.
The frozen output in `certificate_reproduced.json` is byte-identical to the
published certificate.

Verify it with:

```bash
python3 verifier.py certificate_reproduced.json
python3 verifier_cleanroom.py certificate_reproduced.json
python3 -O verifier_cleanroom.py certificate_reproduced.json
sha256sum -c SHA256SUMS
```

For the preceding lazy-SAT discovery stage, install the pinned JavaScript
dependency and run:

```bash
npm ci
Q6_STOP_AT_BAD_PAIRS=1 node solve_lazy_sat.js 6 3 candidate_sat.json 100000
```

The recorded replay stopped at round 5,067 after adding 89,540 connectivity
cuts and produced `near_witness_reproduced.json`.  This is a mathematically
equivalent 8-of-9 near-witness, but it is not byte-identical to
`near_witness.json`.  Repairing this fresh output end-to-end gives:

```bash
python3 kempe_search.py near_witness_reproduced.json \
  certificate_end_to_end_replay.json \
  --beam 2000 --depth 20 --mask-cap 128 --seed 1
```

The archived run found a second valid certificate at depth 12 after visiting
1,286,206 states.  It is stored as `certificate_end_to_end.json` and accepted
by both verifiers.

The lazy-SAT stage is a discovery heuristic with necessary connectivity cuts.
An unfinished run, a round limit, or failure to rediscover a near-witness is
not an UNSAT result.  See `SEARCH_PROVENANCE.md` for the exact contracts and
audit boundary.
