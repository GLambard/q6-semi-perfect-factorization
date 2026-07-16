# Certificate and independent verifiers

`candidate.json` contains six labelled perfect matchings of `Q6`. Matchings
1–3 form one part and matchings 4–6 the other. Both verifiers check that the
six matchings partition all 192 cube edges and that every one of the nine
cross-pair unions is a Hamilton cycle.

Run:

```bash
python3 verifier.py candidate.json
python3 verifier_cleanroom.py candidate.json
sha256sum -c SHA256SUMS
```

Both verifiers require only Python 3 and its standard library. Exit status zero
certifies acceptance. The verifier implementations are intentionally separate;
`verifier_cleanroom.py` neither imports nor calls `verifier.py`.
