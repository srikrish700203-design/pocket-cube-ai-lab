"""
Benchmark API routes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from cube.state import SOLVED_STATE, make_state, is_valid_state
from cube.moves import apply_moves, MOVE_NAMES, _same_face
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star
from database import save_benchmark_record

router = APIRouter()

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


class BenchmarkRequest(BaseModel):
    depths: List[int] = [2, 4, 6, 8, 10]
    algorithms: List[str] = ["v1", "v2", "v3", "v4", "v5"]
    n_cases: int = 5
    seed: int = 42
    timeout_s: float = 30.0


def random_scramble(depth: int, seed_val: int) -> List[str]:
    rng = random.Random(seed_val)
    moves = []
    last = None
    for _ in range(depth):
        choices = [m for m in MOVE_NAMES if last is None or not _same_face(m, last)]
        m = rng.choice(choices)
        moves.append(m)
        last = m
    return moves


@router.post("/run")
def run_benchmark(req: BenchmarkRequest):
    """Run benchmark across depths and algorithms."""
    results = []

    for depth in req.depths:
        depth_results = []
        for case_i in range(req.n_cases):
            seed_val = req.seed * 1000 + depth * 100 + case_i
            scramble = random_scramble(depth, seed_val)
            start_state = apply_moves(SOLVED_STATE, scramble)

            case_result = {
                "depth": depth,
                "case": case_i,
                "scramble": scramble,
                "algorithms": {}
            }

            for algo_name in req.algorithms:
                if algo_name not in ALGO_MAP:
                    continue
                fn = ALGO_MAP[algo_name]
                kwargs = {"timeout_s": min(req.timeout_s or 5.0, 2.0) if algo_name == "v1" else req.timeout_s}
                try:
                    r = fn(start_state, **kwargs)
                    r_dict = r.to_dict()
                    case_result["algorithms"][algo_name] = r_dict
                    try:
                        save_benchmark_record(
                            depth=depth,
                            algorithm=algo_name,
                            case_index=case_i,
                            scramble=scramble,
                            res=r_dict
                        )
                    except Exception:
                        pass
                except Exception as e:
                    case_result["algorithms"][algo_name] = {
                        "error": str(e), "found": False
                    }

            depth_results.append(case_result)
        results.append({"depth": depth, "cases": depth_results})

    return {"benchmark_results": results}


@router.post("/export/csv")
def export_csv(req: BenchmarkRequest):
    """Run benchmark and return CSV."""
    import io, csv
    # Run benchmark inline
    rows = []
    for depth in req.depths:
        for case_i in range(req.n_cases):
            seed_val = req.seed * 1000 + depth * 100 + case_i
            scramble = random_scramble(depth, seed_val)
            start_state = apply_moves(SOLVED_STATE, scramble)
            for algo_name in req.algorithms:
                if algo_name not in ALGO_MAP:
                    continue
                fn = ALGO_MAP[algo_name]
                kwargs = {"timeout_s": min(req.timeout_s or 5.0, 2.0) if algo_name == "v1" else req.timeout_s}
                try:
                    r = fn(start_state, **kwargs)
                    d = r.to_dict()
                    rows.append({
                        "depth": depth, "case": case_i,
                        "scramble": " ".join(scramble),
                        "algorithm": algo_name,
                        "found": d["found"],
                        "solution_length": d["solution_length"],
                        "expanded_states": d["expanded_states"],
                        "generated_states": d["generated_states"],
                        "visited_states": d["visited_states"],
                        "max_frontier_size": d["max_frontier_size"],
                        "peak_memory_kb": d["peak_memory_kb"],
                        "elapsed_ms": d["elapsed_ms"],
                    })
                except Exception as e:
                    rows.append({"depth": depth, "case": case_i,
                                 "algorithm": algo_name, "error": str(e)})

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=benchmark_results.csv"}
    )
