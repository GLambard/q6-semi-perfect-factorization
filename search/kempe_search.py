#!/usr/bin/env python3
"""Deterministic beam search using Kempe component trades.

Every move swaps two colours on a union component. It preserves a
1-factorization and the factorization-sign class. Global swaps within one
prescribed block are quotiented; cross-block swaps are retained because they
change which Hamilton-pair conditions are required.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

N = 64
TRADE_PAIRS = tuple((a, b) for a in range(6) for b in range(a + 1, 6))
CROSS_PAIRS = tuple((a, b) for a in range(3) for b in range(3, 6))
EDGES = tuple((u, u ^ (1 << d)) for u in range(N) for d in range(6) if u < (u ^ (1 << d)))
EDGE_INDEX = {edge: i for i, edge in enumerate(EDGES)}


def load_colours(path: Path) -> tuple[int, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    colours = [-1] * len(EDGES)
    for colour, matching in enumerate(data["matchings"]):
        for u, v in matching:
            colours[EDGE_INDEX[tuple(sorted((u, v)))]] = colour
    if any(c < 0 for c in colours):
        raise ValueError("input does not colour every Q6 edge")
    return tuple(colours)


def mates(colours: tuple[int, ...]) -> list[list[int]]:
    result = [[-1] * N for _ in range(6)]
    for index, (u, v) in enumerate(EDGES):
        colour = colours[index]
        result[colour][u] = v
        result[colour][v] = u
    return result


def components(pair_mates: list[list[int]], a: int, b: int) -> list[list[int]]:
    unseen = set(range(N))
    result: list[list[int]] = []
    while unseen:
        start = next(iter(unseen))
        stack = [start]
        unseen.remove(start)
        component: list[int] = []
        while stack:
            u = stack.pop()
            component.append(u)
            for v in (pair_mates[a][u], pair_mates[b][u]):
                if v in unseen:
                    unseen.remove(v)
                    stack.append(v)
        result.append(component)
    return result


def quality(colours: tuple[int, ...]) -> tuple[int, int, tuple[int, ...]]:
    pair_mates = mates(colours)
    counts = tuple(len(components(pair_mates, a, b)) for a, b in CROSS_PAIRS)
    return sum(count - 1 for count in counts), sum(count > 1 for count in counts), counts


def neighbours(colours: tuple[int, ...], rng: random.Random, mask_cap: int) -> set[tuple[int, ...]]:
    pair_mates = mates(colours)
    result: set[tuple[int, ...]] = set()
    for a, b in TRADE_PAIRS:
        vertex_components = components(pair_mates, a, b)
        same_block = (a < 3 and b < 3) or (a >= 3 and b >= 3)
        # A global swap is redundant only within one prescribed colour block.
        # Across blocks it changes the 3+3 partition and is a genuine move.
        selectable = len(vertex_components) - 1 if same_block else len(vertex_components)
        if selectable <= 0:
            continue
        total_masks = (1 << selectable) - 1
        if total_masks <= mask_cap:
            masks = range(1, total_masks + 1)
        else:
            masks = sorted(rng.sample(range(1, total_masks + 1), mask_cap))
        component_edges: list[list[int]] = []
        for component in vertex_components[:selectable]:
            inside = set(component)
            component_edges.append([
                index for index, (u, _v) in enumerate(EDGES)
                if colours[index] in (a, b) and u in inside
            ])
        for mask in masks:
            changed = list(colours)
            for component_index, edge_indices in enumerate(component_edges):
                if not ((mask >> component_index) & 1):
                    continue
                for edge_index in edge_indices:
                    changed[edge_index] = b if changed[edge_index] == a else a
            result.add(tuple(changed))
    return result


def write_candidate(colours: tuple[int, ...], path: Path) -> None:
    matchings = [[] for _ in range(6)]
    for index, edge in enumerate(EDGES):
        matchings[colours[index]].append(list(edge))
    path.write_text(json.dumps({"matchings": matchings}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--beam", type=int, default=2000)
    parser.add_argument("--depth", type=int, default=20)
    parser.add_argument("--mask-cap", type=int, default=128)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    start = load_colours(args.input)
    frontier = [start]
    visited = {start}
    best = quality(start)
    print(json.dumps({"depth": 0, "quality": best, "frontier": 1, "visited": 1}), flush=True)
    if best[0] == 0:
        write_candidate(start, args.output)
        return 0

    for depth in range(1, args.depth + 1):
        candidates: dict[tuple[int, ...], tuple[int, int, tuple[int, ...]]] = {}
        for state in frontier:
            for candidate in neighbours(state, rng, args.mask_cap):
                if candidate in visited:
                    continue
                visited.add(candidate)
                candidate_quality = quality(candidate)
                if candidate_quality[0] == 0:
                    write_candidate(candidate, args.output)
                    print(json.dumps({"result": "found", "depth": depth,
                                      "quality": candidate_quality, "visited": len(visited),
                                      "output": str(args.output)}), flush=True)
                    return 0
                candidates[candidate] = candidate_quality
                if candidate_quality < best:
                    best = candidate_quality
        ranked = sorted(candidates, key=lambda state: (candidates[state], rng.random()))
        frontier = ranked[:args.beam]
        print(json.dumps({"depth": depth, "best": best, "frontier": len(frontier),
                          "generated": len(candidates), "visited": len(visited)}), flush=True)
        if not frontier:
            break
    print(json.dumps({"result": "not_found", "best": best, "visited": len(visited)}), flush=True)
    return 30


if __name__ == "__main__":
    raise SystemExit(main())
