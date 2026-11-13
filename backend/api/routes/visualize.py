"""
Visualization API — Server-Sent Events for live algorithm visualization.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from cube.state import make_state, SOLVED_STATE, is_valid_state
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star

router = APIRouter()

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


class VisualizeRequest(BaseModel):
    perm: List[int]
    orient: List[int]
    algorithm: str = "v2"
    max_depth: Optional[int] = 11
    timeout_s: Optional[float] = 30.0
    max_events: Optional[int] = 2000  # cap events for large searches


@router.post("/run")
def visualize_algorithm(req: VisualizeRequest):
    """
    Run an algorithm with event collection and return all events.
    Events are capped at max_events for performance.
    """
    if req.algorithm not in ALGO_MAP:
        return {"error": f"Unknown algorithm '{req.algorithm}'"}

    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        return {"error": "Invalid cube state"}

    events = []
    max_events = req.max_events or 2000
    event_capped = False

    def on_event(evt):
        nonlocal event_capped
        if len(events) < max_events:
            events.append(evt)
        else:
            event_capped = True

    algo_fn = ALGO_MAP[req.algorithm]
    timeout = min(req.timeout_s or 5.0, 5.0) if req.algorithm == "v1" else req.timeout_s
    kwargs = {
        "timeout_s": timeout,
        "event_callback": on_event
    }

    result = algo_fn(state, **kwargs)

    return {
        "result": result.to_dict(),
        "events": events,
        "event_count": len(events),
        "event_capped": event_capped,
        "total_events_would_be": result.expanded_states + result.generated_states,
    }
