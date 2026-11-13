"""
V2 — Unidirectional BFS
========================
BFS with a FIFO queue and a single parent/visited dictionary.
Guarantees the shortest solution path (optimal for unit-cost moves).

Characteristics:
- Complete:  Yes
- Optimal:   Yes (unit-cost moves, FIFO = nondecreasing depth)
- Time:      O(b^d)   where b=6, d=solution depth
- Space:     O(b^d)

Data structures:
  parent : dict   {state → (move_name, parent_state) | None}
           Serves as BOTH the visited set AND the parent map.
           A state is "discovered" iff it is a key in parent.
           The start state maps to None (no parent).

Move-attempt model:
  For every expanded state, V2 attempts ALL 6 moves in MOVE_NAMES order.
  Each attempt emits an 'attempt' event.
  If the resulting child is already in parent  → 'duplicate' event.
  If the child is new                          → 'discover' + 'enqueue' events.
  V2 performs DUPLICATE-STATE DETECTION only.
  It does NOT prune moves based on the previous move (that is V3's job).

Event stream (in order):
  start      — search begins, initial state enqueued
  expand     — state dequeued from FIFO queue
  attempt    — a move is applied to the expanded state
  discover   — resulting child is new; recorded in parent
  duplicate  — resulting child was already discovered
  enqueue    — newly discovered child added to FIFO queue
  goal       — goal state discovered during expansion
  complete   — search terminates (found or exhausted or timed out)
"""
from __future__ import annotations
import time
import tracemalloc
from collections import deque
from typing import Optional, Callable
from cube.state import State, SOLVED_STATE
from cube.moves import MOVE_NAMES, apply_move
from .base import SearchResult


def v2_bfs_unidirectional(
    start: State,
    goal: State = SOLVED_STATE,
    timeout_s: float = 30.0,
    event_callback: Optional[Callable] = None,
) -> SearchResult:
    """
    Unidirectional BFS.  Returns the shortest solution path.

    Uses a single dict `parent` for both visited-state detection and
    path reconstruction.  Every move is attempted from every expanded
    state; duplicates are reported but not enqueued.
    """
    # ── Counters ─────────────────────────────────────────────────────────────
    expanded_count   = 0   # states removed from queue and processed
    attempts_count   = 0   # total move-applications made
    discovered_count = 0   # newly discovered (unique) states
    duplicate_count  = 0   # attempts that hit an already-visited state
    enqueued_count   = 0   # states added to the FIFO queue
    max_frontier     = 0   # peak queue length (after enqueue, before dequeue)
    max_depth        = 0   # deepest depth reached

    start_time = time.perf_counter()
    tracemalloc.start()

    def elapsed_ms():
        return (time.perf_counter() - start_time) * 1000

    # ── Single parent dict: state → (move, parent_state) | None ─────────────
    parent: dict = {start: None}

    def _path_to(s: State) -> list[str]:
        """Reconstruct move list from start to s via parent dict."""
        path = []
        cur = s
        while parent[cur] is not None:
            m, prev = parent[cur]
            path.append(m)
            cur = prev
        path.reverse()
        return path

    # ── Event emitter ─────────────────────────────────────────────────────────
    def emit(event_type: str, state: State, depth: int = 0,
             move: str = "", explanation: str = "", path=None,
             child_state: State | None = None,
             is_duplicate: bool = False, was_enqueued: bool = False,
             **kwargs):
        if not event_callback:
            return
        ev = {
            "type":           event_type,
            "state":          {"perm": list(state[0]), "orient": list(state[1])},
            "depth":          depth,
            "move":           move,
            "path":           path if path is not None else _path_to(state),
            "expanded":       expanded_count,
            "attempts":       attempts_count,
            "discovered":     discovered_count,
            "duplicates":     duplicate_count,
            "enqueued":       enqueued_count,
            "frontier_size":  len(queue),
            "max_frontier":   max_frontier,
            "elapsed_ms":     elapsed_ms(),
            "explanation":    explanation,
            "is_duplicate":   is_duplicate,
            "was_enqueued":   was_enqueued,
        }
        if child_state is not None:
            ev["child_state"] = {"perm": list(child_state[0]),
                                  "orient": list(child_state[1])}
        ev.update(kwargs)
        event_callback(ev)

    # ── Trivial case ──────────────────────────────────────────────────────────
    if start == goal:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        emit("start", start, 0, path=[],
             explanation="Initial state is already the goal. Solved immediately.")
        emit("goal", start, 0, path=[],
             explanation="Goal found at depth 0 (already solved).")
        emit("complete", start, 0, path=[],
             explanation="Search complete. Solution depth: 0.")
        return SearchResult(
            algorithm="V2 Unidirectional BFS", found=True, solution=[],
            solution_length=0, expanded_states=0, generated_states=0,
            visited_states=1, max_frontier_size=1,
            peak_memory_kb=peak / 1024, elapsed_ms=elapsed_ms(), max_depth=0
        )

    # ── FIFO queue: entries are (state, depth) ────────────────────────────────
    queue: deque = deque()
    queue.append((start, 0))
    enqueued_count += 1
    max_frontier = max(max_frontier, len(queue))

    emit("start", start, 0, path=[],
         explanation=(
             f"BFS initialised. Start state enqueued at depth 0. "
             f"Move set: {MOVE_NAMES}. Branching factor b=6."
         ))

    timed_out = False
    solution: list[str] = []
    found = False

    try:
        while queue:
            # ── Timeout check ─────────────────────────────────────────────────
            if time.perf_counter() - start_time > timeout_s:
                timed_out = True
                break

            # ── Dequeue next state (FIFO = nondecreasing depth) ───────────────
            state, depth = queue.popleft()
            expanded_count += 1
            max_depth = max(max_depth, depth)

            cur_path = _path_to(state)
            emit("expand", state, depth, path=cur_path,
                 explanation=(
                     f"Dequeued state at depth {depth}. "
                     f"Attempting all {len(MOVE_NAMES)} moves: {MOVE_NAMES}."
                 ))

            # ── Attempt every move in MOVE_NAMES order ────────────────────────
            for move_name in MOVE_NAMES:
                child = apply_move(state, move_name)
                attempts_count += 1
                child_path = cur_path + [move_name]

                # Emit attempt — always, regardless of duplicate/new
                emit("attempt", state, depth, move=move_name, path=cur_path,
                     child_state=child,
                     is_duplicate=(child in parent), was_enqueued=False,
                     explanation=(
                         f"Attempting move {move_name} from depth-{depth} state. "
                         f"Child path would be: {child_path}."
                     ))

                if child in parent:
                    # ── Duplicate: already discovered, skip ───────────────────
                    duplicate_count += 1
                    emit("duplicate", child, depth + 1, move=move_name,
                         path=child_path, child_state=child,
                         is_duplicate=True, was_enqueued=False,
                         explanation=(
                             f"Move {move_name} leads to a state already "
                             f"discovered at depth {len(_path_to(child))}. "
                             f"Duplicate-state detection: not enqueued."
                         ))
                    continue

                # ── Newly discovered ──────────────────────────────────────────
                parent[child] = (move_name, state)
                discovered_count += 1

                emit("discover", child, depth + 1, move=move_name,
                     path=child_path, child_state=child,
                     is_duplicate=False, was_enqueued=False,
                     explanation=(
                         f"New state discovered via {move_name} at depth "
                         f"{depth + 1}. Recorded in parent dictionary."
                     ))

                # ── Goal check ────────────────────────────────────────────────
                if child == goal:
                    solution = _path_to(child)
                    found = True
                    emit("goal", child, depth + 1, move=move_name,
                         path=child_path, child_state=child,
                         is_duplicate=False, was_enqueued=False,
                         explanation=(
                             f"GOAL FOUND at depth {depth + 1}! "
                             f"Solution: {solution}."
                         ))
                    # Break out of inner loop — solution found
                    break

                # ── Enqueue ───────────────────────────────────────────────────
                queue.append((child, depth + 1))
                enqueued_count += 1
                max_frontier = max(max_frontier, len(queue))

                emit("enqueue", child, depth + 1, move=move_name,
                     path=child_path, child_state=child,
                     is_duplicate=False, was_enqueued=True,
                     explanation=(
                         f"State via {move_name} added to FIFO queue. "
                         f"Queue size: {len(queue)}."
                     ))

            if found:
                break

    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    # ── Complete event ────────────────────────────────────────────────────────
    if found:
        status_msg = (
            f"Search complete. Solution found at depth {len(solution)}. "
            f"Expanded: {expanded_count}, Attempts: {attempts_count}, "
            f"Discovered: {discovered_count}, Duplicates: {duplicate_count}."
        )
    elif timed_out:
        status_msg = (
            f"Search timed out after {timeout_s}s. "
            f"Expanded: {expanded_count}, Attempts: {attempts_count}."
        )
    else:
        status_msg = (
            f"Search exhausted. No solution found. "
            f"Expanded: {expanded_count}, Attempts: {attempts_count}."
        )

    emit("complete", start, 0, path=[],
         explanation=status_msg,
         extra_found=found, extra_timed_out=timed_out)

    return SearchResult(
        algorithm        = "V2 Unidirectional BFS",
        found            = found,
        solution         = solution,
        solution_length  = len(solution),
        expanded_states  = expanded_count,
        generated_states = attempts_count,
        visited_states   = discovered_count,
        max_frontier_size= max_frontier,
        peak_memory_kb   = peak / 1024,
        elapsed_ms       = elapsed_ms(),
        max_depth        = max_depth,
        extra            = {
            "attempts":       attempts_count,
            "discovered":     discovered_count,
            "duplicates":     duplicate_count,
            "enqueued":       enqueued_count,
            "timed_out":      timed_out,
        }
    )
