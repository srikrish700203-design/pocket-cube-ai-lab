"""
V3 — Move-Pruned BFS
====================
BFS with sound Quarter-Turn Metric (QTM) move-sequence pruning.

Quarter-Turn Metric (QTM) Pruning Rules:
----------------------------------------
In the Quarter-Turn Metric, the move set is strictly {U, U', R, R', F, F'}.
There are no half-turn single moves (like U2, R2, F2).
The cyclic group of quarter-turns on any face X has order 4: <X> = {I, X, X^2, X^3}.

Under QTM:
  1. Immediate Inverse Pruning:
     M followed by M' (or M' followed by M) = I.
     Applying an immediate inverse lengthens the path by 2 moves with zero net progress.
     Rule: Any move whose face matches the previous move and whose direction is
     opposite (e.g. U then U', or U' then U) is strictly suboptimal and PRUNED.

  2. Two Consecutive Same-Direction Quarter-Turns (Permitted Half-Turn):
     M followed by M = M^2 (a 180° half-turn).
     Because half-turns cannot be executed in 1 move in QTM, exactly 2 quarter-turns
     are necessary and optimal for 180° rotations.
     Rule: A second consecutive quarter-turn in the same direction (run_length=2)
     is ALLOWED.

  3. Three-Turn Suboptimality Pruning:
     M followed by M followed by M = M^3 = M' (e.g. R R R = R').
     Three consecutive turns in the same direction can always be replaced by 1 turn
     in the opposite direction, shortening the path by 2 moves.
     Rule: Any turn on face X when run_length >= 2 is PRUNED.

Search Context & Visited-State Correctness:
------------------------------------------
Because permitted successor moves depend on the previous move and run length,
reaching the same cube state with different move histories can produce different
permitted continuation sets. Therefore, the search state is defined by the
composite key:

    search_key = (state, context)
    where context = (last_move, run_length)   or None for the start state.

This prevents duplicate-state detection from prematurely discarding an alternate
path that preserves a continuation necessary to reach the goal.

Characteristics:
- Complete: Yes
- Optimal:  Yes (preserves all shortest paths under QTM)
- Time:     Reduced vs V2 (prunes redundant inverse pairs and 3-turn cycles)
- Space:    O(b_eff^d) where b_eff < 6
"""
from __future__ import annotations
import time
import tracemalloc
from collections import deque
from typing import Optional, Callable
from cube.state import State, SOLVED_STATE
from cube.moves import MOVE_NAMES, apply_move, is_move_pruned
from .base import SearchResult


def v3_bfs_move_pruned(
    start: State,
    goal: State = SOLVED_STATE,
    timeout_s: float = 30.0,
    event_callback: Optional[Callable] = None,
) -> SearchResult:
    """
    Move-pruned BFS using mathematically sound QTM move-sequence pruning
    and context-aware duplicate-state tracking.
    """
    expanded_count = 0
    generated_count = 0
    pruned_count = 0
    pruned_inverses = 0
    pruned_run3 = 0
    skipped_count = 0
    max_frontier = 0
    max_depth = 0

    start_time = time.perf_counter()
    tracemalloc.start()

    def elapsed_ms():
        return (time.perf_counter() - start_time) * 1000

    # Composite start key: (state, context)
    start_key = (start, None)

    # Single parent map serving both as visited set and path reconstruction
    parent: dict = {start_key: None}

    def _path_to(key) -> list[str]:
        path = []
        cur = key
        while cur in parent and parent[cur] is not None:
            m, prev_k = parent[cur]
            path.append(m)
            cur = prev_k
        path.reverse()
        return path

    def emit(event_type: str, state: State, depth: int = 0,
             move: str = "", explanation: str = "", path=None, **kwargs):
        if not event_callback:
            return
        event_callback({
            "type":          event_type,
            "state":         {"perm": list(state[0]), "orient": list(state[1])},
            "depth":         depth,
            "move":          move,
            "path":          path if path is not None else [],
            "expanded":      expanded_count,
            "generated":     generated_count,
            "pruned":        pruned_count,
            "skipped":       skipped_count,
            "frontier_size": len(queue),
            "max_frontier":  max_frontier,
            "elapsed_ms":    elapsed_ms(),
            "explanation":   explanation,
            **kwargs,
        })

    # Trivial case: already solved
    if start == goal:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        emit("start", start, 0, path=[], explanation="Start state is already solved.")
        emit("goal", start, 0, path=[], explanation="Goal found at depth 0.")
        emit("complete", start, 0, path=[], explanation="Search complete. Solution depth: 0.")
        return SearchResult(
            algorithm="V3 Move-Pruned BFS", found=True, solution=[],
            solution_length=0, expanded_states=0, generated_states=0,
            visited_states=1, max_frontier_size=1,
            peak_memory_kb=peak / 1024, elapsed_ms=elapsed_ms(), max_depth=0
        )

    # Queue entries: (state, depth, context)
    # context is (last_move, run_length) or None
    queue: deque = deque([(start, 0, None)])
    max_frontier = max(max_frontier, len(queue))

    emit("start", start, 0, path=[],
         explanation=(
             "V3 Pruned BFS initialised. QTM canonical rules active: "
             "1) Immediate inverses pruned, 2) Half-turns (run=2) allowed, "
             "3) 3-turn cycles (run>=3) pruned."
         ))

    timed_out = False
    solution: list[str] = []
    found = False

    try:
        while queue:
            if time.perf_counter() - start_time > timeout_s:
                timed_out = True
                break

            state, depth, context = queue.popleft()
            expanded_count += 1
            max_depth = max(max_depth, depth)
            curr_key = (state, context)
            cur_path = _path_to(curr_key)

            emit("expand", state, depth, path=cur_path,
                 explanation=f"Dequeued state at depth {depth}. Context: {context}.")

            last_move = context[0] if context is not None else None
            run_length = context[1] if context is not None else 0

            for move_name in MOVE_NAMES:
                # ── Move-Sequence Pruning (BEFORE state generation) ───────────
                if is_move_pruned(move_name, last_move, run_length):
                    pruned_count += 1
                    if last_move is not None and move_name[0] == last_move[0]:
                        if ("'" in move_name) != ("'" in last_move):
                            pruned_inverses += 1
                            reason = f"Pruned {move_name}: immediate inverse of {last_move} (cancels to identity)."
                        else:
                            pruned_run3 += 1
                            reason = f"Pruned {move_name}: 3rd consecutive turn on face {move_name[0]} (suboptimal; X^3 = X')."
                    else:
                        reason = f"Pruned {move_name} by move constraints."

                    emit("prune", state, depth, move=move_name, path=cur_path,
                         explanation=reason)
                    continue

                # ── Generate State ────────────────────────────────────────────
                child = apply_move(state, move_name)
                generated_count += 1
                child_path = cur_path + [move_name]

                # Update context for child
                if last_move is not None and move_name == last_move:
                    new_run = run_length + 1
                else:
                    new_run = 1
                child_context = (move_name, new_run)
                child_key = (child, child_context)

                # ── Context-Aware Visited Check ───────────────────────────────
                if child_key in parent:
                    skipped_count += 1
                    emit("skip", child, depth + 1, move=move_name, path=child_path,
                         explanation=f"State via {move_name} already visited in context {child_context}.")
                    continue

                parent[child_key] = (move_name, curr_key)

                # ── Goal Check ────────────────────────────────────────────────
                if child == goal:
                    path = []
                    cur = child_key
                    while parent[cur] is not None:
                        m, prev_k = parent[cur]
                        path.append(m)
                        cur = prev_k
                    path.reverse()
                    solution = path
                    found = True

                    emit("goal", child, depth + 1, move=move_name, path=child_path,
                         explanation=f"GOAL FOUND at depth {depth+1}! Solution: {solution}. Pruned: {pruned_count} moves.")
                    break

                # ── Enqueue ───────────────────────────────────────────────────
                queue.append((child, depth + 1, child_context))
                max_frontier = max(max_frontier, len(queue))
                emit("visit", child, depth + 1, move=move_name, path=child_path,
                     explanation=f"New state via {move_name} enqueued at depth {depth+1} with context {child_context}.")

            if found:
                break

    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    emit("complete", start, 0, path=[],
         explanation=(
             f"Search complete. Found: {found}, Timed out: {timed_out}. "
             f"Expanded: {expanded_count}, Generated: {generated_count}, "
             f"Pruned: {pruned_count}, Visited: {len(parent)}."
         ))

    return SearchResult(
        algorithm        = "V3 Move-Pruned BFS",
        found            = found,
        solution         = solution,
        solution_length  = len(solution),
        expanded_states  = expanded_count,
        generated_states = generated_count,
        visited_states   = len(parent),
        max_frontier_size= max_frontier,
        peak_memory_kb   = peak / 1024,
        elapsed_ms       = elapsed_ms(),
        max_depth        = max_depth,
        extra            = {
            "pruned_moves":           pruned_count,
            "pruned_inverses":        pruned_inverses,
            "pruned_run3":            pruned_run3,
            "skipped_states":         skipped_count,
            "timed_out":              timed_out,
            "unique_states_visited":  len(set(k[0] for k in parent)),
        }
    )
