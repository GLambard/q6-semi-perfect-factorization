#!/usr/bin/env python3
"""Independent verifier for claimed 3-semi-perfect 1-factorizations of Q_6.

Input JSON: {"matchings": [[[u,v], ...], ...]}; there are six labelled
matchings, each with 32 Q_6 edges. Vertices are integers 0..63.  Matchings
0,1,2 form the first block and 3,4,5 the second.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

N = 64
EVEN = tuple(v for v in range(N) if v.bit_count() % 2 == 0)
ALL_EDGES = {tuple(sorted((v, v ^ (1 << d)))) for v in range(N) for d in range(6)
             if v < (v ^ (1 << d))}


def fail(message: str) -> None:
    raise ValueError(message)


def parse_matching(raw: object, color: int) -> dict[int, int]:
    if not isinstance(raw, list) or len(raw) != 32:
        fail(f"matching {color}: expected exactly 32 edges")
    mate: dict[int, int] = {}
    for number, edge in enumerate(raw):
        if not isinstance(edge, list) or len(edge) != 2 or not all(type(x) is int for x in edge):
            fail(f"matching {color}, edge {number}: expected [integer, integer]")
        u, v = edge
        if not (0 <= u < N and 0 <= v < N):
            fail(f"matching {color}, edge {number}: endpoint outside 0..63")
        if (u ^ v) not in (1, 2, 4, 8, 16, 32):
            fail(f"matching {color}, edge {number}: ({u}, {v}) is not an edge of Q_6")
        if u in mate or v in mate:
            fail(f"matching {color}, edge {number}: matching repeats a vertex")
        mate[u] = v
        mate[v] = u
    if len(mate) != N:
        fail(f"matching {color}: does not cover every vertex")
    return mate


def cycle_lengths(mate_a: dict[int, int], mate_b: dict[int, int]) -> list[int]:
    unseen = set(range(N))
    lengths: list[int] = []
    while unseen:
        start = next(iter(unseen))
        previous = None
        current = start
        length = 0
        while True:
            unseen.remove(current)
            candidates = (mate_a[current], mate_b[current])
            following = candidates[0] if candidates[0] != previous else candidates[1]
            previous, current = current, following
            length += 1
            if current == start:
                break
        lengths.append(length)
    return sorted(lengths)


def permutation_sign_on_even(mate_a: dict[int, int], mate_b: dict[int, int]) -> int:
    """Sign of m_b^-1 o m_a on the 32 even vertices."""
    perm = {u: mate_b[mate_a[u]] for u in EVEN}
    unseen = set(EVEN)
    sign = 1
    while unseen:
        start = next(iter(unseen))
        current = start
        length = 0
        while current in unseen:
            unseen.remove(current)
            current = perm[current]
            length += 1
        if length % 2 == 0:
            sign *= -1
    return sign


def verify(data: object) -> dict[str, object]:
    if not isinstance(data, dict) or set(data) != {"matchings"}:
        fail('top level must be exactly {"matchings": [...]}')
    raw_matchings = data["matchings"]
    if not isinstance(raw_matchings, list) or len(raw_matchings) != 6:
        fail("expected exactly six labelled matchings")
    matchings = [parse_matching(raw, i) for i, raw in enumerate(raw_matchings)]
    used = [tuple(sorted((u, v))) for mate in matchings for u, v in mate.items() if u < v]
    if len(set(used)) != 192:
        fail("the six matchings are not edge-disjoint")
    if set(used) != ALL_EDGES:
        fail("the six matchings do not partition E(Q_6)")
    pairs = {f"{a}-{b}": cycle_lengths(matchings[a], matchings[b])
             for a in range(6) for b in range(a + 1, 6)}
    cross = {key: pairs[key] for key in pairs if int(key[0]) < 3 <= int(key[2])}
    bad = {key: lengths for key, lengths in cross.items() if lengths != [64]}
    if bad:
        fail("not 3-semi-perfect; cross-pair cycle lengths: " + json.dumps(bad, sort_keys=True))
    signs = {key: permutation_sign_on_even(matchings[int(key[0])], matchings[int(key[2])])
             for key in pairs}
    total_sign = 1
    for value in signs.values():
        total_sign *= value
    return {"result": "valid 3-semi-perfect 1-factorization of Q_6",
            "cross_pair_cycle_lengths": cross,
            "all_pair_cycle_lengths": pairs,
            "relative_permutation_signs": signs,
            "factorization_sign": total_sign}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} candidate.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            result = verify(json.load(handle))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
