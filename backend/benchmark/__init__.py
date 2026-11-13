"""
Benchmark runner module for programmatic use.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import random
import statistics
from typing import List, Dict
from cube.state import SOLVED_STATE
from cube.moves import apply_moves, MOVE_NAMES, _same_face
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


def generate_scramble(depth: int, seed_val: int) -> List[str]:
    rng = random.Random(seed_val)
    moves = []
    last = None
    for _ in range(depth):
        choices = [m for m in MOVE_NAMES if last is None or not _same_face(m, last)]
        m = rng.choice(choices)
        moves.append(m)
        last = m
    return moves


def run_full_benchmark(
    depths: List[int] = [2, 4, 6, 8, 10],
    algorithms: List[str] = ["v1", "v2", "v3", "v4", "v5"],
    n_cases: int = 5,
    seed: int = 42,
    timeout_s: float = 30.0,
) -> Dict:
    """Run the full benchmark and return aggregated statistics."""
    results = {}

    for depth in depths:
        depth_data = {algo: [] for algo in algorithms}

        for case_i in range(n_cases):
            seed_val = seed * 1000 + depth * 100 + case_i
            scramble = generate_scramble(depth, seed_val)
            start_state = apply_moves(SOLVED_STATE, scramble)

            for algo_name in algorithms:
                if algo_name not in ALGO_MAP:
                    continue
                fn = ALGO_MAP[algo_name]
                # V1 runs with safety timeout (unpruned sticker DFS has no depth limit)
                kwargs = {"timeout_s": min(timeout_s, 2.0) if algo_name == "v1" else timeout_s}
                try:
                    r = fn(start_state, **kwargs)
                    depth_data[algo_name].append(r.to_dict())
                except Exception as e:
                    depth_data[algo_name].append({"error": str(e), "found": False})

        # Aggregate statistics
        depth_summary = {}
        for algo_name in algorithms:
            records = depth_data[algo_name]
            valid = [r for r in records if r.get("found")]
            depth_summary[algo_name] = {
                "n_cases": len(records),
                "n_solved": len(valid),
                "avg_elapsed_ms":    statistics.mean(r["elapsed_ms"] for r in valid) if valid else None,
                "median_elapsed_ms": statistics.median(r["elapsed_ms"] for r in valid) if valid else None,
                "avg_expanded":      statistics.mean(r["expanded_states"] for r in valid) if valid else None,
                "avg_solution_len":  statistics.mean(r["solution_length"] for r in valid) if valid else None,
                "avg_memory_kb":     statistics.mean(r["peak_memory_kb"] for r in valid) if valid else None,
                "raw": records,
            }
        results[depth] = depth_summary

    return results
