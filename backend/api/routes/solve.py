"""
Solve API routes — run algorithms and return results.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from cube.state import make_state, SOLVED_STATE, is_valid_state, is_solved
from cube.moves import apply_move
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star
from database import save_solve_record

router = APIRouter()

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


class SolveRequest(BaseModel):
    perm: List[int]
    orient: List[int]
    algorithm: str = "v2"
    max_depth: Optional[int] = 11
    timeout_s: Optional[float] = 30.0


@router.post("")
def solve_cube(req: SolveRequest):
    """Solve a cube state using the specified algorithm."""
    if req.algorithm not in ALGO_MAP:
        raise HTTPException(400, f"Unknown algorithm '{req.algorithm}'. Valid: {list(ALGO_MAP)}")

    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        raise HTTPException(400, "Invalid cube state")

    algo_fn = ALGO_MAP[req.algorithm]
    kwargs = {"timeout_s": min(req.timeout_s or 5.0, 5.0) if req.algorithm == "v1" else req.timeout_s}

    result = algo_fn(state, **kwargs)
    res_dict = result.to_dict()

    # Pre-calculate step-by-step intermediate states along the solution path
    if result.found and result.solution:
        intermediate_states = []
        curr = state
        intermediate_states.append({
            "step": 0,
            "move": None,
            "perm": list(curr[0]),
            "orient": list(curr[1]),
            "is_solved": is_solved(curr),
        })
        for step_idx, m in enumerate(result.solution, 1):
            curr = apply_move(curr, m)
            intermediate_states.append({
                "step": step_idx,
                "move": m,
                "perm": list(curr[0]),
                "orient": list(curr[1]),
                "is_solved": is_solved(curr),
            })
        res_dict["intermediate_states"] = intermediate_states

    # Persist solve to SQLite
    try:
        save_solve_record(
            algorithm=req.algorithm,
            start_perm=tuple(req.perm),
            start_orient=tuple(req.orient),
            result=res_dict
        )
    except Exception as e:
        print(f"Warning: Failed to persist solve record to SQLite: {e}")

    return res_dict


@router.post("/compare")
def compare_algorithms(req: SolveRequest):
    """Run all algorithms on the same state and compare results."""
    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        raise HTTPException(400, "Invalid cube state")

    results = {}
    for name, fn in ALGO_MAP.items():
        timeout = 2.0 if name == "v1" else min(req.timeout_s or 30.0, 10.0)
        kwargs = {"timeout_s": timeout}
        try:
            r = fn(state, **kwargs)
            r_dict = r.to_dict()
            results[name] = r_dict
            try:
                save_solve_record(
                    algorithm=name,
                    start_perm=tuple(req.perm),
                    start_orient=tuple(req.orient),
                    result=r_dict
                )
            except Exception:
                pass
        except Exception as e:
            results[name] = {"error": str(e), "found": False}

    return {"results": results}
