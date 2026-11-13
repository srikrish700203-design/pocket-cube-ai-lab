"""
V1 — Naive 24-Sticker Array + Unpruned Depth-First Search (DFS)
================================================================
Stage 1 in the Progressive Algorithmic Evolution Ladder.

Key Characteristics (Handout Specification):
- State Representation: Naive 24-element color array (mutable/indexed).
- Search Strategy: Recursive Depth-First Search (DFS).
- Visited Set: NONE. States are not recorded in any set or hash table.
- Depth Cap: NONE. No max_depth limit; explores unpruned branches until
  the goal is found, a safety timeout expires, or Python's recursion limit is reached.
- Move Set: Quarter-turns {U, U', R, R', F, F'} directly operating on the 24 stickers.
- Optimality: NO guarantee (can return long suboptimal paths or get trapped in cycles).
- Re-visitations: States may be revisited repeatedly (e.g., R -> R' -> R -> R'...).

Termination Classification:
- "solved": Goal state reached.
- "timed_out": Wall-clock safety timeout exceeded.
- "recursion_limit_reached": Python recursion stack limit hit while exploring deep branches.
- "exhausted": Search space exhausted without finding goal.
"""
from __future__ import annotations
import time
import tracemalloc
from typing import List, Optional, Callable, Sequence, Union, Any

from cube.stickers import (
    apply_sticker_move,
    is_sticker_solved,
    state_to_sticker_array,
    SOLVED_STICKER_LIST,
    V1_MOVE_NAMES,
)
from .base import SearchResult


def v1_dfs_unpruned(
    start: Any,
    goal: Any = None,
    timeout_s: float = 30.0,
    event_callback: Optional[Callable] = None,
    **kwargs,  # Accept and ignore legacy max_depth parameter without applying depth cap
) -> SearchResult:
    """
    Stage 1: Naive 24-sticker unpruned DFS without visited set or depth limit.

    Parameters
    ----------
    start          : Initial cube state (either 24-sticker sequence or compact State tuple)
    goal           : Target sticker configuration (default: SOLVED_STICKER_LIST)
    timeout_s      : Safety wall-clock timeout in seconds (not an algorithmic depth cap)
    event_callback : Optional callback(event_dict) for visualization
    """
    # 1. Prepare initial 24-sticker representation at entrance boundary
    if isinstance(start, (list, tuple)) and len(start) == 24 and isinstance(start[0], int):
        start_stickers: List[int] = list(start)
    elif isinstance(start, tuple) and len(start) == 2 and isinstance(start[0], tuple):
        # Convert compact cubie tuple (perm, orient) to 24-sticker list at entrance
        start_stickers = state_to_sticker_array(start)
    else:
        # Fallback / copy
        start_stickers = list(start)

    # 2. Prepare target goal stickers
    if goal is None:
        goal_stickers: List[int] = list(SOLVED_STICKER_LIST)
    elif isinstance(goal, (list, tuple)) and len(goal) == 24 and isinstance(goal[0], int):
        goal_stickers = list(goal)
    elif isinstance(goal, tuple) and len(goal) == 2 and isinstance(goal[0], tuple):
        goal_stickers = state_to_sticker_array(goal)
    else:
        goal_stickers = list(goal)

    # Search tracking variables
    expanded = 0
    generated = 0
    max_depth_reached = 0
    max_stack_depth = 0
    start_time = time.perf_counter()

    timed_out = False
    recursion_limit_hit = False

    tracemalloc.start()

    def emit(event_type: str, stickers: List[int], depth: int, move: str = "",
             explanation: str = "", active_path: Optional[List[str]] = None, **extra_fields):
        if event_callback:
            from cube.stickers import sticker_array_to_state
            try:
                st = sticker_array_to_state(stickers)
                st_dict = {"perm": list(st[0]), "orient": list(st[1])}
            except Exception:
                st_dict = None
            cur_p = list(active_path) if active_path is not None else (list(path) if 'path' in locals() or 'path' in globals() else [])
            event_callback({
                "type": event_type,
                "stickers": list(stickers),
                "state": st_dict,
                "depth": depth,
                "move": move,
                "path": cur_p,
                "expanded": expanded,
                "generated": generated,
                "elapsed_ms": (time.perf_counter() - start_time) * 1000,
                "explanation": explanation,
                **extra_fields,
            })

    def dfs(stickers: List[int], path: List[str], depth: int) -> bool:
        """
        Pure recursive DFS operating entirely on the 24-sticker list.
        NO visited set, NO depth cap, NO move pruning.
        """
        nonlocal expanded, generated, max_depth_reached, max_stack_depth
        nonlocal timed_out, recursion_limit_hit

        # Safety wall-clock timeout check
        if time.perf_counter() - start_time > timeout_s:
            timed_out = True
            return False

        max_depth_reached = max(max_depth_reached, depth)
        max_stack_depth = max(max_stack_depth, depth)

        expanded += 1
        emit(
            "expand", stickers, depth,
            active_path=path,
            explanation=f"Expanding node at depth {depth} (24-sticker array). Stack depth = {depth}."
        )

        # Check goal state directly on the 24-sticker array
        if stickers == goal_stickers or is_sticker_solved(stickers):
            emit("goal", stickers, depth, active_path=path, explanation="Goal reached on 24-sticker array!")
            return True

        # Unpruned branching across all 6 quarter-turns
        for move_name in V1_MOVE_NAMES:
            if timed_out:
                return False

            generated += 1
            # Apply move directly to 24-sticker array without converting to cubie tuples
            child_stickers = apply_sticker_move(stickers, move_name)
            path.append(move_name)

            emit(
                "generate", child_stickers, depth + 1, move=move_name,
                active_path=path,
                explanation=f"Applied {move_name} directly to 24 stickers. Generated child at depth {depth + 1}."
            )

            try:
                if dfs(child_stickers, path, depth + 1):
                    return True
            except RecursionError:
                # Python call stack limit hit while exploring this deep unpruned branch
                recursion_limit_hit = True
                emit(
                    "recursion_limit", child_stickers, depth + 1, move=move_name,
                    active_path=path,
                    explanation=f"Python recursion limit reached at depth {depth + 1}. Backtracking."
                )

            emit(
                "backtrack", stickers, depth, move=move_name,
                active_path=path,
                explanation=f"Backtracking from {move_name} at depth {depth}."
            )
            path.pop()

        return False

    path: List[str] = []
    found = dfs(start_stickers, path, 0)

    solution_path = list(path) if found else []

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Determine termination status
    if found:
        status = "solved"
        termination_reason = "Solution found within time limit."
    elif timed_out:
        status = "timed_out"
        termination_reason = f"Search timed out after {timeout_s:.2f}s safety threshold."
    elif recursion_limit_hit:
        status = "recursion_limit_reached"
        termination_reason = "Python recursion limit reached during unpruned search."
    else:
        status = "exhausted"
        termination_reason = "Search space exhausted without finding goal."

    return SearchResult(
        algorithm="V1 Unpruned DFS",
        found=found,
        solution=solution_path,
        solution_length=len(solution_path),
        expanded_states=expanded,
        generated_states=generated,
        visited_states=0,  # Explicitly 0: V1 maintains NO visited set
        max_frontier_size=max_stack_depth,  # Recursion stack depth
        peak_memory_kb=peak / 1024,
        elapsed_ms=elapsed_ms,
        max_depth=max_depth_reached,
        extra={
            "status": status,
            "termination_reason": termination_reason,
            "timed_out": timed_out,
            "recursion_limit_reached": recursion_limit_hit,
            "max_recursion_depth": max_depth_reached,
            "representation": "24-sticker colour array",
            "has_visited_set": False,
            "has_depth_cap": False,
            "note": "Naive 24-sticker representation; unpruned DFS without visited set or depth limit.",
        }
    )
