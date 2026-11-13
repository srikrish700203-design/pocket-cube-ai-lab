"""
V4 — Bidirectional BFS
=======================
Searches simultaneously from start (forward) and goal (backward),
expanding complete levels before checking for intersection.

Mathematical Guarantees & Level Expansion:
------------------------------------------
1. Two FIFO queues:
   - `fwd_queue`: states discovered in forward direction from `start`.
   - `bwd_queue`: states discovered in backward direction from `goal`.
2. Complete-level expansion:
   A level at depth d is fully expanded before any intersection check is performed.
   This guarantees that when an intersection is detected, all candidate intersections
   at that level boundary are known.
3. Optimal Meeting-Point Selection:
   Among all states in the intersection `set(fwd_parent.keys()) & set(bwd_parent.keys())`,
   the algorithm selects the meeting state m* minimizing:
       total_depth = fwd_depth[m*] + bwd_depth[m*]
   This guarantees shortest-path optimality under the unit-cost Quarter-Turn Metric (QTM).
4. Backward Move Inversion:
   Backward transitions apply move m to state s to discover predecessor p:
       p = apply_move(s, m)
   In the forward direction, p reaches s via INVERSE_MOVE[m].
   When reconstructing the final solution:
       forward_path (start → meeting) + meeting_to_goal_path (meeting → goal)
   where meeting_to_goal_path is obtained by inverting each move along the backward parent chain.
5. All 6 Moves Attempted:
   Every expanded state in both directions attempts all 6 moves in MOVE_NAMES.
   Duplicates are recorded as events and not enqueued.
"""
from __future__ import annotations
import time
import tracemalloc
from collections import deque
from typing import Optional, Callable
from cube.state import State, SOLVED_STATE
from cube.moves import MOVE_NAMES, apply_move, INVERSE_MOVE
from .base import SearchResult


def v4_bfs_bidirectional(
    start: State,
    goal: State = SOLVED_STATE,
    timeout_s: float = 30.0,
    event_callback: Optional[Callable] = None,
) -> SearchResult:
    """
    Bidirectional BFS with complete-level expansion, optimal meeting-point selection,
    and distinct forward/backward event tracking.
    """
    fwd_expanded = 0
    bwd_expanded = 0
    fwd_generated = 0
    bwd_generated = 0
    fwd_duplicates = 0
    bwd_duplicates = 0

    max_fwd_frontier = 0
    max_bwd_frontier = 0
    max_combined_frontier = 0

    fwd_cur_depth = 0
    bwd_cur_depth = 0

    start_time = time.perf_counter()
    tracemalloc.start()

    def elapsed_ms():
        return (time.perf_counter() - start_time) * 1000

    # ── Visited & Parent Maps ─────────────────────────────────────────────────
    fwd_parent: dict[State, tuple[str, State] | None] = {start: None}
    fwd_depth: dict[State, int] = {start: 0}

    bwd_parent: dict[State, tuple[str, State] | None] = {goal: None}
    bwd_depth: dict[State, int] = {goal: 0}

    def _fwd_path_to(s: State) -> list[str]:
        p = []
        curr = s
        while curr in fwd_parent and fwd_parent[curr] is not None:
            m, prev = fwd_parent[curr]
            p.append(m)
            curr = prev
        p.reverse()
        return p

    def _bwd_path_to(s: State) -> list[str]:
        p = []
        curr = s
        while curr in bwd_parent and bwd_parent[curr] is not None:
            m, prev = bwd_parent[curr]
            p.append(m)
            curr = prev
        p.reverse()
        return p

    # ── Event Emitter ─────────────────────────────────────────────────────────
    def emit(event_type: str, state: State, depth: int = 0,
             direction: str = "forward", move: str = "",
             explanation: str = "", path=None,
             child_state: State | None = None,
             is_duplicate: bool = False, is_intersection: bool = False,
             **kwargs):
        if not event_callback:
            return
        ev = {
            "type":             event_type,
            "direction":        direction,
            "state":            {"perm": list(state[0]), "orient": list(state[1])},
            "depth":            depth,
            "move":             move,
            "path":             path if path is not None else (_fwd_path_to(state) if direction == "forward" else _bwd_path_to(state)),
            "fwd_expanded":     fwd_expanded,
            "bwd_expanded":     bwd_expanded,
            "expanded":         fwd_expanded + bwd_expanded,
            "fwd_generated":    fwd_generated,
            "bwd_generated":    bwd_generated,
            "generated":        fwd_generated + bwd_generated,
            "fwd_visited":      len(fwd_parent),
            "bwd_visited":      len(bwd_parent),
            "unique_visited":   len(set(fwd_parent.keys()) | set(bwd_parent.keys())),
            "fwd_frontier":     len(fwd_queue),
            "bwd_frontier":     len(bwd_queue),
            "frontier_size":    len(fwd_queue) + len(bwd_queue),
            "max_frontier":     max_combined_frontier,
            "elapsed_ms":       elapsed_ms(),
            "explanation":      explanation,
            "is_duplicate":     is_duplicate,
            "is_intersection":  is_intersection,
        }
        if child_state is not None:
            ev["child_state"] = {"perm": list(child_state[0]), "orient": list(child_state[1])}
        ev.update(kwargs)
        event_callback(ev)

    # ── Trivial Case: Start is Goal ───────────────────────────────────────────
    if start == goal:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        emit("start", start, 0, direction="forward", path=[],
             explanation="Initial state is already solved.")
        emit("goal", start, 0, direction="forward", path=[],
             explanation="Goal found immediately at depth 0.")
        emit("complete", start, 0, direction="forward", path=[],
             explanation="Search complete. Solution depth: 0.")
        return SearchResult(
            algorithm="V4 Bidirectional BFS", found=True, solution=[],
            solution_length=0, expanded_states=0, generated_states=0,
            visited_states=1, max_frontier_size=1,
            peak_memory_kb=peak / 1024, elapsed_ms=elapsed_ms(), max_depth=0,
            extra={
                "fwd_expanded": 0, "bwd_expanded": 0,
                "fwd_generated": 0, "bwd_generated": 0,
                "fwd_visited": 1, "bwd_visited": 1,
                "unique_visited": 1, "total_records": 2,
                "meeting_state": {"perm": list(start[0]), "orient": list(start[1])},
                "fwd_depth": 0, "bwd_depth": 0,
            }
        )

    # ── FIFO Queues: entries are (state, depth) ───────────────────────────────
    fwd_queue: deque[tuple[State, int]] = deque([(start, 0)])
    bwd_queue: deque[tuple[State, int]] = deque([(goal, 0)])

    max_fwd_frontier = len(fwd_queue)
    max_bwd_frontier = len(bwd_queue)
    max_combined_frontier = len(fwd_queue) + len(bwd_queue)

    emit("start", start, 0, direction="forward", path=[],
         explanation="Bidirectional BFS initialised. Forward queue starts at scrambled state.")
    emit("start", goal, 0, direction="backward", path=[],
         explanation="Bidirectional BFS initialised. Backward queue starts at solved goal state.")

    def reconstruct_solution(meeting: State) -> tuple[list[str], list[str], list[str]]:
        """
        Reconstructs:
        1. forward_path: start → meeting
        2. bwd_search_path: goal → meeting (actual moves applied in backward search)
        3. meeting_to_goal: meeting → goal (inverting bwd moves)
        Full solution = forward_path + meeting_to_goal
        """
        fwd_p = []
        curr = meeting
        while fwd_parent[curr] is not None:
            m, prev_st = fwd_parent[curr]
            fwd_p.append(m)
            curr = prev_st
        fwd_p.reverse()

        bwd_search_p = []
        meeting_to_goal = []
        curr = meeting
        while bwd_parent[curr] is not None:
            m_applied, prev_st = bwd_parent[curr]
            bwd_search_p.append(m_applied)
            meeting_to_goal.append(INVERSE_MOVE[m_applied])
            curr = prev_st

        # bwd_search_p goes meeting -> goal; reverse to represent goal -> meeting
        bwd_search_p.reverse()

        return fwd_p, bwd_search_p, fwd_p + meeting_to_goal

    timed_out = False
    solution: list[str] = []
    meeting_state: State | None = None
    fwd_path_meeting: list[str] = []
    bwd_path_meeting: list[str] = []
    found = False

    try:
        while fwd_queue or bwd_queue:
            if time.perf_counter() - start_time > timeout_s:
                timed_out = True
                break

            # ─────────────────────────────────────────────────────────────────
            # 1. EXPAND FORWARD LEVEL (Complete Level Expansion)
            # ─────────────────────────────────────────────────────────────────
            if fwd_queue:
                fwd_level_size = len(fwd_queue)
                emit("frontier", start, fwd_cur_depth, direction="forward",
                     explanation=f"[Forward] Expanding complete level {fwd_cur_depth} ({fwd_level_size} states in level).")

                for _ in range(fwd_level_size):
                    st, d = fwd_queue.popleft()
                    fwd_expanded += 1
                    cur_path = _fwd_path_to(st)

                    emit("expand", st, d, direction="forward", path=cur_path,
                         explanation=f"[Forward] Dequeued state at forward depth {d}. Attempting all 6 moves.")

                    for move_name in MOVE_NAMES:
                        child = apply_move(st, move_name)
                        fwd_generated += 1
                        child_path = cur_path + [move_name]
                        is_dup = child in fwd_parent
                        is_inter = child in bwd_parent

                        emit("attempt", st, d, direction="forward", move=move_name,
                             path=cur_path, child_state=child,
                             is_duplicate=is_dup, is_intersection=is_inter,
                             explanation=f"[Forward] Attempting move {move_name} from forward depth {d}.")

                        if is_dup:
                            fwd_duplicates += 1
                            emit("duplicate", child, d + 1, direction="forward", move=move_name,
                                 path=child_path, child_state=child,
                                 is_duplicate=True, is_intersection=is_inter,
                                 explanation=f"[Forward] Move {move_name} leads to state already in forward visited table.")
                            continue

                        fwd_parent[child] = (move_name, st)
                        fwd_depth[child] = d + 1
                        fwd_queue.append((child, d + 1))

                        max_fwd_frontier = max(max_fwd_frontier, len(fwd_queue))
                        max_combined_frontier = max(max_combined_frontier, len(fwd_queue) + len(bwd_queue))

                        emit("discover", child, d + 1, direction="forward", move=move_name,
                             path=child_path, child_state=child,
                             is_duplicate=False, is_intersection=is_inter,
                             explanation=f"[Forward] New state discovered via {move_name} at forward depth {d + 1}.")

                        if is_inter:
                            emit("intersection", child, d + 1, direction="forward", move=move_name,
                                 path=child_path, child_state=child,
                                 is_duplicate=False, is_intersection=True,
                                 explanation=f"[Forward] State via {move_name} intersects backward search frontier!")

                fwd_cur_depth += 1
                emit("frontier_complete", start, fwd_cur_depth, direction="forward",
                     explanation=f"[Forward] Level {fwd_cur_depth - 1} complete. Checking intersections.")

                # ── Check Intersections after Complete Forward Level ─────────
                intersections = set(fwd_parent.keys()) & set(bwd_parent.keys())
                if intersections:
                    # Optimal selection: minimize total combined path length
                    meeting_state = min(intersections, key=lambda s: fwd_depth[s] + bwd_depth[s])
                    fwd_path_meeting, bwd_path_meeting, solution = reconstruct_solution(meeting_state)
                    found = True

                    emit("goal", meeting_state, fwd_depth[meeting_state], direction="forward",
                         path=fwd_path_meeting, child_state=meeting_state,
                         fwd_path=fwd_path_meeting, bwd_search_path=bwd_path_meeting,
                         solution=solution,
                         explanation=(
                             f"INTERSECTION CONFIRMED! Selected optimal meeting state with "
                             f"fwd_depth={fwd_depth[meeting_state]} + bwd_depth={bwd_depth[meeting_state]} = "
                             f"{len(solution)} total moves. Solution: {solution}."
                         ))
                    emit("goal", meeting_state, bwd_depth[meeting_state], direction="backward",
                         path=bwd_path_meeting, child_state=meeting_state,
                         fwd_path=fwd_path_meeting, bwd_search_path=bwd_path_meeting,
                         solution=solution,
                         explanation=(
                             f"INTERSECTION CONFIRMED! Selected optimal meeting state in backward search with "
                             f"fwd_depth={fwd_depth[meeting_state]} + bwd_depth={bwd_depth[meeting_state]} = "
                             f"{len(solution)} total moves. Solution: {solution}."
                         ))
                    break

            # ─────────────────────────────────────────────────────────────────
            # 2. EXPAND BACKWARD LEVEL (Complete Level Expansion)
            # ─────────────────────────────────────────────────────────────────
            if bwd_queue:
                bwd_level_size = len(bwd_queue)
                emit("frontier", goal, bwd_cur_depth, direction="backward",
                     explanation=f"[Backward] Expanding complete level {bwd_cur_depth} ({bwd_level_size} states in level).")

                for _ in range(bwd_level_size):
                    st, d = bwd_queue.popleft()
                    bwd_expanded += 1
                    cur_path = _bwd_path_to(st)

                    emit("expand", st, d, direction="backward", path=cur_path,
                         explanation=f"[Backward] Dequeued state at backward depth {d}. Attempting all 6 moves.")

                    for move_name in MOVE_NAMES:
                        # In backward search, applying move_name to st generates predecessor child
                        child = apply_move(st, move_name)
                        bwd_generated += 1
                        child_path = cur_path + [move_name]
                        is_dup = child in bwd_parent
                        is_inter = child in fwd_parent

                        emit("attempt", st, d, direction="backward", move=move_name,
                             path=cur_path, child_state=child,
                             is_duplicate=is_dup, is_intersection=is_inter,
                             explanation=f"[Backward] Attempting move {move_name} from backward depth {d}.")

                        if is_dup:
                            bwd_duplicates += 1
                            emit("duplicate", child, d + 1, direction="backward", move=move_name,
                                 path=child_path, child_state=child,
                                 is_duplicate=True, is_intersection=is_inter,
                                 explanation=f"[Backward] Move {move_name} leads to state already in backward visited table.")
                            continue

                        bwd_parent[child] = (move_name, st)
                        bwd_depth[child] = d + 1
                        bwd_queue.append((child, d + 1))

                        max_bwd_frontier = max(max_bwd_frontier, len(bwd_queue))
                        max_combined_frontier = max(max_combined_frontier, len(fwd_queue) + len(bwd_queue))

                        emit("discover", child, d + 1, direction="backward", move=move_name,
                             path=child_path, child_state=child,
                             is_duplicate=False, is_intersection=is_inter,
                             explanation=f"[Backward] New state discovered via {move_name} at backward depth {d + 1}.")

                        if is_inter:
                            emit("intersection", child, d + 1, direction="backward", move=move_name,
                                 path=child_path, child_state=child,
                                 is_duplicate=False, is_intersection=True,
                                 explanation=f"[Backward] State via {move_name} intersects forward search frontier!")

                bwd_cur_depth += 1
                emit("frontier_complete", goal, bwd_cur_depth, direction="backward",
                     explanation=f"[Backward] Level {bwd_cur_depth - 1} complete. Checking intersections.")

                # ── Check Intersections after Complete Backward Level ────────
                intersections = set(fwd_parent.keys()) & set(bwd_parent.keys())
                if intersections:
                    meeting_state = min(intersections, key=lambda s: fwd_depth[s] + bwd_depth[s])
                    fwd_path_meeting, bwd_path_meeting, solution = reconstruct_solution(meeting_state)
                    found = True

                    emit("goal", meeting_state, fwd_depth[meeting_state], direction="forward",
                         path=fwd_path_meeting, child_state=meeting_state,
                         fwd_path=fwd_path_meeting, bwd_search_path=bwd_path_meeting,
                         solution=solution,
                         explanation=(
                             f"INTERSECTION CONFIRMED! Selected optimal meeting state with "
                             f"fwd_depth={fwd_depth[meeting_state]} + bwd_depth={bwd_depth[meeting_state]} = "
                             f"{len(solution)} total moves. Solution: {solution}."
                         ))
                    emit("goal", meeting_state, bwd_depth[meeting_state], direction="backward",
                         path=bwd_path_meeting, child_state=meeting_state,
                         fwd_path=fwd_path_meeting, bwd_search_path=bwd_path_meeting,
                         solution=solution,
                         explanation=(
                             f"INTERSECTION CONFIRMED! Selected optimal meeting state in backward search with "
                             f"fwd_depth={fwd_depth[meeting_state]} + bwd_depth={bwd_depth[meeting_state]} = "
                             f"{len(solution)} total moves. Solution: {solution}."
                         ))
                    break

    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    unique_states = len(set(fwd_parent.keys()) | set(bwd_parent.keys()))
    total_records = len(fwd_parent) + len(bwd_parent)

    emit("complete", start, 0, direction="forward", path=[],
         explanation=(
             f"Bidirectional search complete. Found: {found}. Solution length: {len(solution)}. "
             f"Fwd expanded: {fwd_expanded}, Bwd expanded: {bwd_expanded}, "
             f"Fwd visited: {len(fwd_parent)}, Bwd visited: {len(bwd_parent)}, "
             f"Unique states: {unique_states}."
         ))

    return SearchResult(
        algorithm        = "V4 Bidirectional BFS",
        found            = found,
        solution         = solution,
        solution_length  = len(solution),
        expanded_states  = fwd_expanded + bwd_expanded,
        generated_states = fwd_generated + bwd_generated,
        visited_states   = unique_states,
        max_frontier_size= max_combined_frontier,
        peak_memory_kb   = peak / 1024,
        elapsed_ms       = elapsed_ms(),
        max_depth        = max(fwd_cur_depth, bwd_cur_depth),
        extra            = {
            "fwd_expanded":          fwd_expanded,
            "bwd_expanded":          bwd_expanded,
            "fwd_generated":         fwd_generated,
            "bwd_generated":         bwd_generated,
            "fwd_duplicates":        fwd_duplicates,
            "bwd_duplicates":        bwd_duplicates,
            "fwd_visited":           len(fwd_parent),
            "bwd_visited":           len(bwd_parent),
            "unique_visited":        unique_states,
            "total_records":         total_records,
            "max_fwd_frontier":      max_fwd_frontier,
            "max_bwd_frontier":      max_bwd_frontier,
            "max_combined_frontier": max_combined_frontier,
            "fwd_depth":             fwd_cur_depth,
            "bwd_depth":             bwd_cur_depth,
            "meeting_state":         {"perm": list(meeting_state[0]), "orient": list(meeting_state[1])} if meeting_state else None,
            "fwd_path":              fwd_path_meeting,
            "bwd_search_path":       bwd_path_meeting,
            "timed_out":             timed_out,
        }
    )
