# Frozen verification record

Verified on 16 July 2026 with Python 3.12.13 on Linux.

Commands:

```bash
python3 verifier.py candidate.json
python3 verifier_cleanroom.py candidate.json
python3 -O verifier_cleanroom.py candidate.json
sha256sum -c SHA256SUMS
```

Expected conclusions:

- the primary verifier reports a valid 3-semi-perfect 1-factorization of `Q6`;
- every one of the nine cross-pair cycle decompositions is `[64]`;
- the clean-room verifier prints `VALID: Q6 has a 3-semi-perfect 1-factorization`;
- the clean-room result is unchanged under Python optimization because it does not
  use `assert` for certificate conditions; and
- all frozen hashes are accepted.
