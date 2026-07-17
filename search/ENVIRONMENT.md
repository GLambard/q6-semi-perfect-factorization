# Recorded environment

- Replay date: 17 July 2026 (UTC)
- Operating system: Linux x86_64, kernel 6.12.47
- Processor: Intel Xeon Platinum 8370C
- Python: 3.12.13
- Node.js: 24.14.0
- `logic-solver`: 2.0.1, including its bundled MiniSat image
- Kempe search dependencies: Python standard library only

The Kempe replay is seeded, but Python's pseudo-random stream and iteration
details should not be assumed identical across all Python implementations and
versions.  Exact replay is therefore claimed for the recorded CPython 3.12.13
environment.  On other environments, any output accepted by both verifiers is
a mathematically equivalent reproduction even when its bytes or search trace
differ.
