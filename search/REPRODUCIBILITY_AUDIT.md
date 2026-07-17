# Reproducibility audit

Date: 17 July 2026

## Outcome

**Passed at two levels.**

1. The frozen historical near-witness regenerates the published certificate
   byte-for-byte.  The run ends at Kempe depth 8 after 599,257 visited states.
2. A new lazy-SAT run generates a different 8-of-9 near-witness, which the same
   Kempe program repairs to a different valid certificate at depth 12.  Both
   independent verifiers accept that certificate.

## Audit layers

| Layer | Status | Evidence |
|---|---|---|
| Inventory | Pass | Programs, inputs, outputs, manifests, complete logs, exit statuses, environment, and hashes are present. |
| Environment | Pass with boundary | Python 3.12.13, Node.js 24.14.0, and `logic-solver` 2.0.1 are recorded; no container image is supplied. |
| Dependency replay | Pass | `npm ci --ignore-scripts` succeeded from the frozen `package-lock.json`; a `logic-solver` satisfiability smoke test passed. |
| Exact Kempe replay | Pass | Published certificate hash `3d3a...f8db` reproduced byte-for-byte. |
| SAT replay | Semantic pass | A one-defect near-witness was regenerated, but its bytes and cycle decomposition differ from the historical input. |
| End-to-end replay | Pass | Fresh SAT near-witness repaired to accepted certificate hash `98c1...022`. |
| Independent validation | Pass | Primary, clean-room, and optimized clean-room verifier executions all accept both final certificates. |
| Hash integrity | Pass | `sha256sum -c SHA256SUMS` accepts every frozen release file. |
| Claim linkage | Pass | The theorem depends on the certificate checks; search logs support discovery provenance only. |

## Corrections made during the audit

- The previously reported value of 902,324 visited Kempe states was not
  reproduced.  The exact replay visits 599,257 states and produces the same
  certificate.  The manuscript must use 599,257.
- The lazy-SAT replay is not byte-identical to the historical near-witness.
  Accordingly, the release distinguishes exact replay from semantic
  reproduction.

## Remaining limitations

- Exact pseudo-random traces are claimed only for the recorded CPython 3.12.13
  environment.  Other runtimes may generate different valid witnesses.
- The unavailable SAW experiment runner was replaced by explicit JSON
  manifests and the standard-library logging wrapper `run_logged.py`.
- The search directory does not prove UNSAT for any instance or residual
  neighborhood.
