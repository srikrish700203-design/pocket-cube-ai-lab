"""
Test runner API routes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import random
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from cube.state import SOLVED_STATE, is_solved, is_valid_state
from cube.moves import apply_moves, MOVE_NAMES, _same_face
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star
from database import save_verification_test

router = APIRouter()

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


class TestRequest(BaseModel):
    depths: List[int] = [1, 2, 3, 4, 5, 6]
    n_per_depth: int = 10
    algorithms: List[str] = ["v2", "v3", "v4", "v5"]
    seed: int = 42
    timeout_s: float = 15.0


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
def run_tests(req: TestRequest):
    """Run automated tests on all specified algorithms."""
    all_tests = []
    summary = {
        algo: {"passed": 0, "failed": 0, "invalid": 0, "total": 0}
        for algo in req.algorithms
    }

    # Use v2 BFS as oracle for optimality
    oracle = v2_bfs_unidirectional

    for depth in req.depths:
        for case_i in range(req.n_per_depth):
            seed_val = req.seed * 10000 + depth * 100 + case_i
            scramble = random_scramble(depth, seed_val)
            start_state = apply_moves(SOLVED_STATE, scramble)

            # Oracle solution length
            try:
                oracle_r = oracle(start_state, timeout_s=req.timeout_s)
                optimal_len = oracle_r.solution_length if oracle_r.found else None
            except Exception:
                optimal_len = None

            test_case = {
                "depth": depth,
                "case": case_i,
                "scramble": scramble,
                "optimal_length": optimal_len,
                "results": {}
            }

            for algo_name in req.algorithms:
                if algo_name not in ALGO_MAP:
                    continue
                fn = ALGO_MAP[algo_name]
                kwargs = {"timeout_s": min(req.timeout_s or 5.0, 2.0) if algo_name == "v1" else req.timeout_s}

                try:
                    r = fn(start_state, **kwargs)
                    # Verify: apply solution to scrambled state
                    if r.found:
                        final = apply_moves(start_state, r.solution)
                        solution_valid = is_solved(final)
                        moves_legal = all(m in MOVE_NAMES for m in r.solution)
                    else:
                        solution_valid = False
                        moves_legal = False

                    # Optimality check (compare to oracle)
                    is_optimal = None
                    if r.found and optimal_len is not None:
                        is_optimal = r.solution_length <= optimal_len

                    status = "passed" if (r.found and solution_valid) else "failed"
                    summary[algo_name]["total"] += 1
                    summary[algo_name][status] += 1
                    if r.found and not solution_valid:
                        summary[algo_name]["invalid"] += 1

                    test_case["results"][algo_name] = {
                        "found": r.found,
                        "solution": r.solution,
                        "solution_length": r.solution_length,
                        "solution_valid": solution_valid,
                        "moves_legal": moves_legal,
                        "is_optimal": is_optimal,
                        "elapsed_ms": r.elapsed_ms,
                        "expanded_states": r.expanded_states,
                        "status": status,
                    }
                except Exception as e:
                    summary[algo_name]["failed"] += 1
                    summary[algo_name]["total"] += 1
                    test_case["results"][algo_name] = {
                        "error": str(e), "status": "error"
                    }

            all_tests.append(test_case)

            # Persist to SQLite if standard 4 solvers ran
            res_map = test_case["results"]
            if all(k in res_map for k in ["v2", "v3", "v4", "v5"]):
                try:
                    all_ok = all(
                        res_map[k].get("status") == "passed" and res_map[k].get("is_optimal", True)
                        for k in ["v2", "v3", "v4", "v5"]
                    )
                    save_verification_test(
                        case_number=len(all_tests),
                        scramble_depth=depth,
                        scramble=scramble,
                        optimal_length=optimal_len or 0,
                        all_passed=all_ok,
                        v2_info={"len": res_map["v2"].get("solution_length", 0), "ms": res_map["v2"].get("elapsed_ms", 0.0), "exp": res_map["v2"].get("expanded_states", 0)},
                        v3_info={"len": res_map["v3"].get("solution_length", 0), "ms": res_map["v3"].get("elapsed_ms", 0.0), "exp": res_map["v3"].get("expanded_states", 0)},
                        v4_info={"len": res_map["v4"].get("solution_length", 0), "ms": res_map["v4"].get("elapsed_ms", 0.0), "exp": res_map["v4"].get("expanded_states", 0)},
                        v5_info={"len": res_map["v5"].get("solution_length", 0), "ms": res_map["v5"].get("elapsed_ms", 0.0), "exp": res_map["v5"].get("expanded_states", 0)},
                    )
                except Exception:
                    pass

    return {
        "summary": summary,
        "tests": all_tests,
        "total_cases": len(all_tests),
    }
