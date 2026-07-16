#!/usr/bin/env python3
"""Second, deliberately independent checker for the Q6 construction."""
import json
import sys


def require(condition: bool) -> None:
    if not condition:
        raise ValueError("certificate condition failed")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verifier_cleanroom.py candidate.json", file=sys.stderr)
        return 2
    try:
        obj = json.load(open(sys.argv[1], encoding="utf-8"))
        factors = obj["matchings"]
        require(set(obj) == {"matchings"})
        require(len(factors) == 6)
        expected = {
            tuple(sorted((u, u ^ (1 << direction))))
            for u in range(64) for direction in range(6)
        }
        seen_edges = []
        partners = []
        for factor in factors:
            require(len(factor) == 32)
            partner = {}
            for item in factor:
                require(isinstance(item, list) and len(item) == 2)
                u, v = item
                require(type(u) is int and type(v) is int)
                require(0 <= u < 64 and 0 <= v < 64)
                require((u ^ v) in {1, 2, 4, 8, 16, 32})
                require(u not in partner and v not in partner)
                partner[u], partner[v] = v, u
                seen_edges.append(tuple(sorted((u, v))))
            require(len(partner) == 64)
            partners.append(partner)
        require(len(seen_edges) == 192)
        require(len(set(seen_edges)) == 192)
        require(set(seen_edges) == expected)

        for left in range(3):
            for right in range(3, 6):
                previous, current = -1, 0
                visited = {0}
                for length in range(1, 65):
                    candidates = (partners[left][current], partners[right][current])
                    following = candidates[0] if candidates[0] != previous else candidates[1]
                    previous, current = current, following
                    if current == 0:
                        require(length == 64)
                        break
                    require(current not in visited)
                    visited.add(current)
                require(len(visited) == 64)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID: Q6 has a 3-semi-perfect 1-factorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
