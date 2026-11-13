"""
V5 — IDA* (Iterative Deepening A*)
====================================
Memory-efficient heuristic search using iterative deepening on f-cost.

Heuristic:
  h(s) = ceil(misplaced_or_twisted_corners / 4)

  A corner is "misplaced or twisted" if either:
    - The piece in its slot is not the correct piece (wrong permutation), OR
    - The piece is in the correct slot but has wrong orientation (twisted).

Admissibility:
  Each move is a quarter-turn affecting exactly 4 corner pieces.
  Therefore at most 4 misplaced/twisted corners can be fixed per move.
  h(s) = ceil(count/4) ≤ actual moves needed.

Characteristics:
- Complete: Yes
- Optimal: Yes (with admissible heuristic)
- Time:  O(b^d)
- Space: O(d)  — only current path kept
"""
from __future__ import annotations
import time
import math
import tracemalloc
from typing import Optional, Callable
from cube.state import State, SOLVED_STATE, SOLVED_PERM, SOLVED_ORIENT
from cube.moves import MOVE_NAMES, apply_move, _same_face
from .base import SearchResult


INFINITY = float('inf')


def heuristic(state: State) -> int:
    """
    h(s) = ceil(misplaced_or_twisted_corners / 4)

    Count corners that are either:
    - In the wrong slot (perm[i] != i), OR
    - In the right slot but twisted (orient[i] != 0).
    The fixed DBL corner (index 7) is always correct and not counted.
    """
    perm, orient = state
    count = 0
    for i in range(7):
        if perm[i] != i or orient[i] != 0:
            count += 1
    return math.ceil(count / 4)


def v5_ida_star(
    start: State,
    goal: State = SOLVED_STATE,
    timeout_s: float = 30.0,
    event_callback: Optional[Callable] = None,
) -> SearchResult:
    """
    IDA* search using the assignment's admissible heuristic.
    """
    expanded          = 0
    generated         = 0
    max_depth_reached = 0
    iterations        = 0
    start_time        = time.perf_counter()
    thresholds_seen   = []
    timed_out         = False
    tracemalloc.start()

    def elapsed():
        return (time.perf_counter() - start_time) * 1000

    def emit(event_type, state, depth=0, move="", explanation="", path=None, **kwargs):
        if event_callback:
            event_callback({
                "type":          event_type,
                "state":         {"perm": list(state[0]), "orient": list(state[1])},
                "depth":         depth,
                "move":          move,
                "path":          list(path) if path is not None else [],
                "expanded":      expanded,
                "generated":     generated,
                "elapsed_ms":    elapsed(),
                "explanation":   explanation,
                **kwargs,
            })

    solution_path = None

    def search(state, g, threshold, path, path_set, last_move):
        nonlocal expanded, generated, max_depth_reached, timed_out, solution_path

        if time.perf_counter() - start_time > timeout_s:
            timed_out = True
            return INFINITY

        h = heuristic(state)
        f = g + h
        max_depth_reached = max(max_depth_reached, g)

        if f > threshold:
            emit("prune", state, g, move=path[-1] if path else "", path=path,
                 explanation=f"f={f} = g={g}+h={h} > threshold={threshold}. Backtracking.",
                 f=f, g=g, h=h, threshold=threshold)
            return f

        expanded += 1
        emit("expand", state, g, path=path,
             explanation=f"Expanding. f={f}=g={g}+h={h}. Within threshold={threshold}.",
             f=f, g=g, h=h, threshold=threshold)

        if state == goal:
            solution_path = list(path)
            emit("goal", state, g, path=path,
                 explanation=f"GOAL FOUND at depth {g}! f={f}.",
                 f=f, g=g, h=h)
            return -1  # signal: found!

        minimum = INFINITY
        for move_name in MOVE_NAMES:
            # Path cycle prevention: skip same-face as last move
            if last_move is not None and _same_face(move_name, last_move):
                continue

            child = apply_move(state, move_name)
            generated += 1

            # Avoid revisiting states on the CURRENT PATH (cycle prevention)
            child_key = child  # states are tuples, hashable
            if child_key in path_set:
                continue

            path.append(move_name)
            path_set.add(child_key)

            emit("generate", child, g + 1, move=move_name, path=path,
                 explanation=f"Trying {move_name}. New depth={g+1}.",
                 f=g+1+heuristic(child), g=g+1, h=heuristic(child), threshold=threshold)

            result = search(child, g + 1, threshold, path, path_set, move_name)

            if result == -1:  # found!
                return -1

            if timed_out:
                return INFINITY

            minimum = min(minimum, result)
            path.pop()
            path_set.discard(child_key)

        return minimum

    # Initial threshold = h(start)
    threshold = heuristic(start)
    emit("start", start, 0,
         explanation=f"IDA* started. Initial threshold={threshold}. h(start)={threshold}.")

    while threshold != INFINITY and not timed_out:
        iterations += 1
        thresholds_seen.append(threshold)

        emit("iteration", start, 0,
             explanation=f"IDA* iteration {iterations}. Threshold = {threshold}.",
             iteration=iterations, threshold=threshold)

        path_set = {start}
        result = search(start, 0, threshold, [], path_set, None)

        if result == -1 or timed_out:
            break

        if result == INFINITY:
            break  # no solution exists

        threshold = result

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    found = solution_path is not None and not timed_out
    return SearchResult(
        algorithm        = "V5 IDA*",
        found            = found,
        solution         = solution_path or [],
        solution_length  = len(solution_path) if solution_path else 0,
        expanded_states  = expanded,
        generated_states = generated,
        visited_states   = 0,  # IDA* doesn't maintain a global visited set
        max_frontier_size= max_depth_reached,  # max depth = max "stack" depth
        peak_memory_kb   = peak / 1024,
        elapsed_ms       = elapsed(),
        max_depth        = max_depth_reached,
        extra            = {
            "iterations":       iterations,
            "thresholds":       thresholds_seen,
            "timed_out":        timed_out,
            "heuristic":        "h(s)=ceil(misplaced_twisted/4)",
        }
    )
