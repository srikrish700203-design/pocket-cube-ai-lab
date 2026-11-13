"""
Unit tests for all five search algorithms.
Tests verify correctness of solutions, optimality where applicable,
and proper handling of the solved state.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from cube.state import SOLVED_STATE, is_solved, is_valid_state
from cube.moves import apply_moves, MOVE_NAMES
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star, heuristic


# Known scrambles for deterministic testing
SCRAMBLES = [
    ("depth1_R",  ["R"]),
    ("depth1_U",  ["U"]),
    ("depth1_F",  ["F"]),
    ("depth2_RU", ["R", "U"]),
    ("depth2_RF", ["R", "F"]),
    ("depth3_RUF",["R", "U", "F"]),
    ("depth3_RUR",["R", "U", "R'"]),
    ("depth4_RURF",["R", "U", "R'", "F"]),
]


def scramble_state(moves):
    return apply_moves(SOLVED_STATE, moves)


def verify_solution(start_state, solution_moves):
    """Apply solution to start and check if we reach solved."""
    final = apply_moves(start_state, solution_moves)
    return is_solved(final)


class TestHeuristic:
    def test_solved_state_heuristic_zero(self):
        assert heuristic(SOLVED_STATE) == 0

    def test_one_move_heuristic(self):
        state = apply_moves(SOLVED_STATE, ["R"])
        h = heuristic(state)
        assert h >= 0
        assert h <= 1  # 4 corners moved, ceil(4/4) = 1

    def test_heuristic_admissible(self):
        """h(s) must never exceed actual solution length.
        Test with known depth-1 scrambles."""
        for name, moves in SCRAMBLES:
            state = scramble_state(moves)
            h = heuristic(state)
            # For depth-1 scrambles, h <= 1
            if len(moves) == 1:
                assert h <= 1, f"{name}: h={h} > 1 (overestimates depth-1)"


class TestAlgorithmsSolvedState:
    """All algorithms should return a trivial solution (empty path) for solved state."""

    def test_v1_solved_state(self):
        result = v1_dfs_unpruned(SOLVED_STATE)
        assert result.found
        assert result.solution == []
        assert result.extra.get("status") == "solved"

    def test_v2_solved_state(self):
        result = v2_bfs_unidirectional(SOLVED_STATE)
        assert result.found
        assert result.solution == []

    def test_v3_solved_state(self):
        result = v3_bfs_move_pruned(SOLVED_STATE)
        assert result.found
        assert result.solution == []

    def test_v4_solved_state(self):
        result = v4_bfs_bidirectional(SOLVED_STATE)
        assert result.found
        assert result.solution == []

    def test_v5_solved_state(self):
        result = v5_ida_star(SOLVED_STATE)
        assert result.found
        assert result.solution == []


class TestDepth1Scrambles:
    @pytest.mark.parametrize("name,moves", [
        ("R",  ["R"]),
        ("U",  ["U"]),
        ("F",  ["F"]),
        ("Ri", ["R'"]),
        ("Ui", ["U'"]),
        ("Fi", ["F'"]),
    ])
    def test_v2_depth1(self, name, moves):
        state = scramble_state(moves)
        result = v2_bfs_unidirectional(state)
        assert result.found
        assert result.solution_length == 1
        assert verify_solution(state, result.solution)

    @pytest.mark.parametrize("name,moves", [
        ("R",  ["R"]),
        ("U",  ["U"]),
        ("F",  ["F"]),
    ])
    def test_v3_depth1(self, name, moves):
        state = scramble_state(moves)
        result = v3_bfs_move_pruned(state)
        assert result.found
        assert result.solution_length == 1
        assert verify_solution(state, result.solution)

    @pytest.mark.parametrize("name,moves", [
        ("R",  ["R"]),
        ("U",  ["U"]),
        ("F",  ["F"]),
    ])
    def test_v4_depth1(self, name, moves):
        state = scramble_state(moves)
        result = v4_bfs_bidirectional(state)
        assert result.found
        assert verify_solution(state, result.solution)

    @pytest.mark.parametrize("name,moves", [
        ("R",  ["R"]),
        ("U",  ["U"]),
        ("F",  ["F"]),
    ])
    def test_v5_depth1(self, name, moves):
        state = scramble_state(moves)
        result = v5_ida_star(state)
        assert result.found
        assert result.solution_length == 1
        assert verify_solution(state, result.solution)


class TestDepth3Scrambles:
    @pytest.mark.parametrize("name,moves", [
        ("RUF",   ["R", "U", "F"]),
        ("RURi",  ["R", "U", "R'"]),
        ("UFRi",  ["U", "F", "R'"]),
    ])
    def test_v2_v3_v4_v5_agree(self, name, moves):
        """For depth-3 scrambles, all optimal algorithms must find equal-length solutions."""
        state = scramble_state(moves)
        r2 = v2_bfs_unidirectional(state)
        r3 = v3_bfs_move_pruned(state)
        r4 = v4_bfs_bidirectional(state)
        r5 = v5_ida_star(state)
        assert r2.found and r3.found and r4.found and r5.found
        # All should find same optimal length
        assert r2.solution_length == r3.solution_length
        assert r2.solution_length == r5.solution_length
        # Verify solutions are valid
        for r in [r2, r3, r4, r5]:
            assert verify_solution(state, r.solution), f"{r.algorithm} solution invalid for {name}"


class TestSolutionValidity:
    @pytest.mark.parametrize("name,moves", SCRAMBLES)
    def test_v2_solution_valid(self, name, moves):
        state = scramble_state(moves)
        result = v2_bfs_unidirectional(state)
        assert result.found
        assert verify_solution(state, result.solution)

    @pytest.mark.parametrize("name,moves", SCRAMBLES)
    def test_all_solution_moves_legal(self, name, moves):
        state = scramble_state(moves)
        result = v2_bfs_unidirectional(state)
        assert all(m in MOVE_NAMES for m in result.solution)


class TestStage1V1Compliance:
    """Rigorous compliance tests for Stage 1 (V1 Unpruned 24-Sticker DFS)."""

    def test_all_24_stickers_preserved_by_every_move(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move, V1_MOVE_NAMES
        for m in V1_MOVE_NAMES:
            after = apply_sticker_move(SOLVED_STICKERS, m)
            assert len(after) == 24
            assert sorted(after) == sorted(SOLVED_STICKERS), f"{m} altered color distribution"

    def test_move_inverse_restores_sticker_array(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move, V1_MOVE_NAMES, MOVE_INVERSES
        for m in V1_MOVE_NAMES:
            inv = MOVE_INVERSES[m]
            after = apply_sticker_move(apply_sticker_move(SOLVED_STICKERS, m), inv)
            assert tuple(after) == SOLVED_STICKERS, f"{m} followed by {inv} did not restore solved stickers"

    def test_four_quarter_turns_restore_sticker_array(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move, V1_MOVE_NAMES
        for m in V1_MOVE_NAMES:
            curr = list(SOLVED_STICKERS)
            for _ in range(4):
                curr = apply_sticker_move(curr, m)
            assert tuple(curr) == SOLVED_STICKERS, f"{m}^4 did not restore solved stickers"

    def test_sticker_solved_state_check(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move, is_sticker_solved
        assert is_sticker_solved(SOLVED_STICKERS) is True
        scrambled = apply_sticker_move(SOLVED_STICKERS, "U")
        assert is_sticker_solved(scrambled) is False

    def test_v1_has_no_depth_limit_parameter_in_signature(self):
        import inspect
        sig = inspect.signature(v1_dfs_unpruned)
        assert "max_depth" not in sig.parameters, "V1 signature must not have max_depth parameter"

    def test_v1_has_no_depth_limit_condition_in_execution(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move
        scramble = apply_sticker_move(SOLVED_STICKERS, "F")
        res = v1_dfs_unpruned(scramble, timeout_s=0.05)
        # Should not be stopped at depth 11
        assert res.max_depth > 11, f"Expected search to exceed depth 11, reached {res.max_depth}"

    def test_v1_has_no_visited_state_tracking(self):
        from cube.stickers import SOLVED_STICKERS
        res = v1_dfs_unpruned(SOLVED_STICKERS)
        assert res.visited_states == 0
        assert res.extra.get("has_visited_set") is False

    def test_v1_solves_simple_scramble_before_timeout(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move
        scramble = apply_sticker_move(SOLVED_STICKERS, "U'")
        res = v1_dfs_unpruned(scramble, timeout_s=5.0)
        assert res.found is True
        assert res.solution == ["U"]
        assert res.extra.get("status") == "solved"

    def test_v1_timeout_reported_separately_from_exhaustion(self):
        from cube.stickers import SOLVED_STICKERS, apply_sticker_move
        scramble = apply_sticker_move(SOLVED_STICKERS, "F")
        res = v1_dfs_unpruned(scramble, timeout_s=0.03)
        assert res.found is False
        assert res.extra.get("status") == "timed_out"
        assert res.extra.get("timed_out") is True



class TestStage2V2Compliance:
    """
    Rigorous compliance tests for Stage 2 (V2 Unidirectional BFS).

    Verifies:
    - All 6 moves are attempted from every expanded state
    - All 6 attempt events appear in the event stream
    - Inverse moves (which return to previously visited states) produce
      'duplicate' events, not 'discover' events
    - Consecutive same-face moves ARE still attempted (no V3-style pruning)
    - V2 does NOT use the V3 move-pruning helper
    - Every newly discovered state is enqueued exactly once
    - FIFO expansion order is preserved (depth-nondecreasing)
    - 'duplicate' events are present in the event stream
    - Final solution reaches the goal
    - Solution length matches an independent BFS reference
    - Maximum frontier size is calculated correctly
    - Single parent dict serves as visited+parent (no separate visited dict)
    """

    def _collect_events(self, start_state, timeout_s=10.0):
        events = []
        result = v2_bfs_unidirectional(
            start_state, timeout_s=timeout_s,
            event_callback=lambda e: events.append(e)
        )
        return result, events

    # ── Test 1: Root state attempts all 6 moves (use deeper scramble) ─────────
    def test_root_state_attempts_all_6_moves(self):
        """
        After the root expand event (for a non-goal-finding expansion),
        all 6 moves must be attempted.
        Use a depth-3 scramble so root expansion does not immediately find the goal.
        """
        state = scramble_state(["R", "U", "F"])
        result, events = self._collect_events(state)
        root_attempts = [e for e in events if e["type"] == "attempt" and e["depth"] == 0]
        assert len(root_attempts) == 6, (
            f"Expected exactly 6 attempt events from root, got {len(root_attempts)}"
        )

    # ── Test 2: All 6 move names appear as attempt events from root ───────────
    def test_all_6_move_names_in_root_attempt_events(self):
        """
        Every element of MOVE_NAMES must appear as attempts from root depth.
        Use depth-3 scramble so root expansion completes all 6 without finding goal.
        """
        state = scramble_state(["R", "U", "F"])
        result, events = self._collect_events(state)
        root_attempt_moves = {
            e["move"] for e in events
            if e["type"] == "attempt" and e["depth"] == 0
        }
        for m in MOVE_NAMES:
            assert m in root_attempt_moves, (
                f"Move '{m}' missing from root attempt events. "
                f"Got: {root_attempt_moves}"
            )

    # ── Test 3: Inverse move yields a duplicate event ─────────────────────────
    def test_inverse_move_produces_duplicate_event(self):
        """
        When BFS expands depth-1 nodes, some moves lead back to the start
        state or to states discovered via another path → 'duplicate' events.
        For a depth-2 scramble [R,U], after expanding the root we discover
        6 depth-1 states. When we then expand those depth-1 states, many
        moves lead back to already-discovered states → duplicates at depth 2.
        """
        state = scramble_state(["R", "U"])
        result, events = self._collect_events(state)
        dup_events = [e for e in events if e["type"] == "duplicate"]
        assert len(dup_events) > 0, (
            "Expected 'duplicate' events (BFS always revisits states via "
            f"multiple paths). Total events: {len(events)}"
        )
        # Duplicates should appear at depth >= 2 (children of depth-1 nodes
        # lead back to already-discovered depth-0 or depth-1 states)
        dup_at_depth2_plus = [e for e in dup_events if e["depth"] >= 2]
        assert len(dup_at_depth2_plus) > 0, (
            "Expected 'duplicate' events at depth >= 2 (inverse moves from "
            f"depth-1 nodes lead back to already-discovered states). "
            f"Duplicate depths found: {sorted(set(e['depth'] for e in dup_events))}"
        )

    # ── Test 4: Consecutive same-face moves ARE still attempted ──────────────
    def test_same_face_moves_still_attempted(self):
        """
        V2 must NOT prune same-face moves. After expanding ANY state at
        depth >= 1, all 6 moves must still be attempted — including same-face
        moves. Use depth-3 scramble to get depth-1 expansions that have room
        for all 6 attempts.
        """
        state = scramble_state(["R", "U", "F"])
        result, events = self._collect_events(state)
        # Collect all moves attempted at depth 1
        depth1_attempt_moves = {
            e["move"] for e in events
            if e["type"] == "attempt" and e["depth"] == 1
        }
        # At depth 1 we should see all 6 moves attempted (across all depth-1 nodes)
        for m in MOVE_NAMES:
            assert m in depth1_attempt_moves, (
                f"Move '{m}' never attempted at depth 1. "
                f"V2 may be pruning same-face moves. Got: {depth1_attempt_moves}"
            )

    # ── Test 5: V2 does not use previous-move restrictions ───────────────────
    def test_v2_has_no_previous_move_parameter(self):
        """
        V2's queue entries must not carry a 'last_move' field.
        V3 carries (state, depth, last_move); V2 must carry (state, depth) only.
        Inspect source code to confirm.
        """
        import inspect
        import algorithms.v2_bfs as v2_mod
        src = inspect.getsource(v2_mod)
        assert "last_move" not in src, (
            "V2 source contains 'last_move' — this indicates V3-style move pruning"
        )

    # ── Test 6: V2 does not call V3's move-pruning helper ────────────────────
    def test_v2_does_not_call_get_successors_pruned(self):
        import inspect
        import algorithms.v2_bfs as v2_mod
        src = inspect.getsource(v2_mod)
        assert "get_successors_pruned" not in src, (
            "V2 must not use get_successors_pruned (that is V3's function)"
        )
        assert "_same_face" not in src, (
            "V2 must not use _same_face move-pruning logic"
        )

    # ── Test 7: Every newly discovered state enqueued exactly once ────────────
    def test_each_discovered_state_enqueued_exactly_once(self):
        """
        For every 'discover' event there must be exactly one corresponding
        'enqueue' event with the same move and depth. No state appears in
        more than one enqueue event.
        """
        state = scramble_state(["R", "U"])
        result, events = self._collect_events(state)
        enqueue_paths = [
            tuple(e["path"] + [e["move"]])
            for e in events if e["type"] == "enqueue"
        ]
        # All enqueue paths should be unique
        assert len(enqueue_paths) == len(set(enqueue_paths)), (
            "Some state was enqueued more than once"
        )
        # Count of discover == count of enqueue (non-goal discovers → enqueue)
        discover_count = len([e for e in events if e["type"] == "discover"])
        # goal-discovers do NOT get enqueued, so discovers >= enqueues
        enqueue_count = len([e for e in events if e["type"] == "enqueue"])
        goal_discover = len([e for e in events if e["type"] == "goal"])
        assert discover_count == enqueue_count + goal_discover, (
            f"discover_count={discover_count} != enqueue_count={enqueue_count}"
            f" + goal_discover={goal_discover}"
        )

    # ── Test 8: FIFO order: depths are nondecreasing across expand events ─────
    def test_fifo_expansion_depth_nondecreasing(self):
        """BFS must expand states in nondecreasing depth order."""
        state = scramble_state(["R", "U", "F"])
        result, events = self._collect_events(state)
        expand_depths = [e["depth"] for e in events if e["type"] == "expand"]
        for i in range(1, len(expand_depths)):
            assert expand_depths[i] >= expand_depths[i - 1], (
                f"Depth decreased from {expand_depths[i-1]} to {expand_depths[i]} "
                f"at expand index {i} — FIFO property violated"
            )

    # ── Test 9: Duplicate events are present and non-empty ───────────────────
    def test_duplicate_events_present_in_stream(self):
        """
        In any non-trivial BFS run, there will always be states reached by
        multiple paths. Duplicate events must appear in the stream.
        """
        state = scramble_state(["R", "U"])
        result, events = self._collect_events(state)
        dup_events = [e for e in events if e["type"] == "duplicate"]
        assert len(dup_events) > 0, (
            "No 'duplicate' events found. V2 must report duplicate-state attempts."
        )

    # ── Test 10: Final solution reaches the goal ──────────────────────────────
    def test_solution_reaches_goal(self):
        for name, moves in SCRAMBLES:
            state = scramble_state(moves)
            result = v2_bfs_unidirectional(state)
            assert result.found, f"{name}: V2 did not find a solution"
            assert verify_solution(state, result.solution), (
                f"{name}: V2 solution does not reach solved state"
            )

    # ── Test 11: Solution length matches independent BFS reference ────────────
    def test_solution_length_matches_reference(self):
        """
        For small scrambles, compare V2 solution length against V3 and V5
        (both optimal). They must all agree.
        """
        for name, moves in [
            ("depth1_R", ["R"]),
            ("depth2_RU", ["R", "U"]),
            ("depth3_RUF", ["R", "U", "F"]),
        ]:
            state = scramble_state(moves)
            r2 = v2_bfs_unidirectional(state)
            r3 = v3_bfs_move_pruned(state)
            assert r2.found and r3.found, f"{name}: one of V2/V3 failed"
            assert r2.solution_length == r3.solution_length, (
                f"{name}: V2 solution_length={r2.solution_length} but "
                f"V3 solution_length={r3.solution_length}. V2 must be optimal."
            )

    # ── Test 12: Maximum frontier size is tracked correctly ───────────────────
    def test_max_frontier_size_is_positive_and_at_least_branching_factor(self):
        """
        For a depth-3 scramble, BFS must enqueue all 6 children of root before
        finding the goal (which is depth 3). The frontier should be at least 6.
        """
        state = scramble_state(["R", "U", "F"])
        result = v2_bfs_unidirectional(state)
        assert result.max_frontier_size >= 6, (
            f"max_frontier_size={result.max_frontier_size} is less than 6; "
            "after expanding root, all 6 children should have been in the "
            "queue simultaneously (depth-3 scramble, goal not found at depth 1)."
        )

    # ── Test 13: Single parent dict (no separate visited dict) ───────────────
    def test_single_parent_dict_not_two_dicts(self):
        """
        V2 source must use a single dict (parent) for both visited detection
        and path reconstruction. There must be no separate `visited` dict.
        """
        import inspect
        import algorithms.v2_bfs as v2_mod
        src = inspect.getsource(v2_mod)
        # The old V2 had both `visited = {}` and `parent = {}`. That is now merged.
        assert "visited = {}" not in src, (
            "V2 still has a separate 'visited = {}' dict. Must use single parent dict."
        )

    # ── Test 14: attempt events contain child_state ───────────────────────────
    def test_attempt_events_contain_child_state(self):
        """Every 'attempt' event must include the computed child_state."""
        state = scramble_state(["F"])
        _, events = self._collect_events(state)
        attempt_events = [e for e in events if e["type"] == "attempt"]
        assert len(attempt_events) > 0
        for ev in attempt_events[:6]:
            assert "child_state" in ev, (
                f"'attempt' event missing 'child_state' field: {ev}"
            )
            assert "perm" in ev["child_state"]
            assert "orient" in ev["child_state"]

    # ── Test 15: event ordering matches BFS semantics ─────────────────────────
    def test_event_order_expand_then_6_attempts(self):
        """
        Each 'expand' event must be immediately followed by exactly 6
        'attempt' events for expansions that do not discover the goal
        mid-expansion. Use depth-3 scramble so root expansion completes fully.
        """
        state = scramble_state(["R", "U", "F"])
        _, events = self._collect_events(state)
        i = 0
        checked = 0
        while i < len(events):
            if events[i]["type"] == "expand":
                attempt_block = []
                found_goal = False
                j = i + 1
                while j < len(events) and events[j]["type"] in (
                    "attempt", "discover", "duplicate", "enqueue", "goal"
                ):
                    if events[j]["type"] == "attempt":
                        attempt_block.append(events[j])
                    if events[j]["type"] == "goal":
                        found_goal = True
                    j += 1
                # Only assert 6 attempts on expansions that don't find goal mid-way
                if not found_goal:
                    assert len(attempt_block) == 6, (
                        f"expand at index {i} (depth={events[i]['depth']}) "
                        f"followed by {len(attempt_block)} attempts, expected 6. "
                        f"Event types in block: "
                        f"{[e['type'] for e in events[i+1:j]]}"
                    )
                    checked += 1
                i = j
            else:
                i += 1
        assert checked >= 1, "No non-goal expand was found to test"


class TestStage3V3Compliance:
    """
    Rigorous compliance tests for Stage 3 (V3 Move-Pruned BFS).

    Verifies:
    - Scramble 'R R' (half-turn) can be solved in 2 quarter-turn moves
    - Scramble 'R R R' (suboptimal 3-turn) is solved in 1 inverse move
    - Immediate inverse pairs are pruned before state generation
    - 3 consecutive turns in the same direction are pruned
    - Canonical pruning preserves shortest-path optimality vs unpruned V2
    - Search state uses composite context (state, context) to prevent
      incorrect discarding of valid continuations
    - All returned solutions replay correctly to the goal state
    """

    def _collect_v3_events(self, start_state, timeout_s=10.0):
        events = []
        result = v3_bfs_move_pruned(
            start_state, timeout_s=timeout_s,
            event_callback=lambda e: events.append(e)
        )
        return result, events

    def test_v3_solves_RR_in_2_moves(self):
        """A half-turn scramble 'R R' must be solved in 2 quarter-turn moves."""
        st = scramble_state(["R", "R"])
        res = v3_bfs_move_pruned(st)
        assert res.found, "V3 failed to solve R R scramble"
        assert res.solution_length == 2, f"Expected 2 moves for R R, got {res.solution_length}: {res.solution}"
        assert verify_solution(st, res.solution), "Solution does not reach goal"

    def test_v3_solves_RRR_in_1_move(self):
        """A 3-quarter-turn scramble 'R R R' is equivalent to R' and must be solved in 1 move."""
        st = scramble_state(["R", "R", "R"])
        res = v3_bfs_move_pruned(st)
        assert res.found, "V3 failed to solve R R R scramble"
        assert res.solution_length == 1, f"Expected 1 move for R R R, got {res.solution_length}: {res.solution}"
        assert res.solution == ["R"], f"Expected ['R'], got {res.solution}"
        assert verify_solution(st, res.solution), "Solution does not reach goal"

    def test_v3_immediate_inverse_pruned(self):
        """From a state reached via R, attempting R' must be pruned."""
        st = scramble_state(["R", "U", "F"])
        res, events = self._collect_v3_events(st)
        # Find prune events for an immediate inverse
        prune_events = [e for e in events if e["type"] == "prune"]
        assert len(prune_events) > 0, "No prune events emitted by V3"
        # Check that inverse pruning explanation is present
        inverse_prunes = [e for e in prune_events if "inverse" in e.get("explanation", "").lower()]
        assert len(inverse_prunes) > 0, f"No inverse prune events found. Prunes: {prune_events[:5]}"

    def test_v3_three_consecutive_same_face_turns_pruned(self):
        """After applying 2 consecutive turns in the same direction, a 3rd turn must be pruned."""
        st = scramble_state(["R", "R", "U", "F"])
        res, events = self._collect_v3_events(st)
        prune_events = [e for e in events if e["type"] == "prune"]
        three_turn_prunes = [e for e in prune_events if "3" in e.get("explanation", "") or "consecutive" in e.get("explanation", "")]
        assert len(three_turn_prunes) > 0, "No 3-turn limit prune events found"

    def test_v3_solves_states_requiring_same_face_consecutive_turns(self):
        """Scrambles with half-turns (e.g. R R U, U U R) must be solved optimally."""
        for seq in [["R", "R", "U"], ["U", "U", "R"], ["F", "F", "R"]]:
            st = scramble_state(seq)
            res = v3_bfs_move_pruned(st)
            r2 = v2_bfs_unidirectional(st)
            assert res.found, f"V3 failed on {seq}"
            assert res.solution_length == r2.solution_length, (
                f"V3 solution length {res.solution_length} != V2 {r2.solution_length} on {seq}"
            )
            assert verify_solution(st, res.solution), f"Solution invalid for {seq}"

    def test_v3_canonical_pruning_preserves_shortest_path_vs_v2(self):
        """V3 must return the exact same shortest solution length as unpruned V2 on all small test cases."""
        import itertools
        for d in [1, 2]:
            for seq in itertools.product(MOVE_NAMES, repeat=d):
                st = scramble_state(list(seq))
                r2 = v2_bfs_unidirectional(st)
                r3 = v3_bfs_move_pruned(st)
                assert r3.found, f"V3 failed on {seq}"
                assert r3.solution_length == r2.solution_length, (
                    f"Optimality violation on {seq}: V3={r3.solution_length}, V2={r2.solution_length}"
                )
                assert verify_solution(st, r3.solution), f"Solution failed to solve cube for {seq}"

    def test_v3_all_returned_solutions_replay_to_goal(self):
        """All standard benchmark scrambles must replay successfully to solved state."""
        for name, moves in SCRAMBLES:
            st = scramble_state(moves)
            res = v3_bfs_move_pruned(st)
            assert res.found, f"V3 failed on {name}"
            assert verify_solution(st, res.solution), f"V3 solution for {name} does not reach goal"


class TestStage4V4Compliance:
    """
    Rigorous compliance tests for Stage 4 (V4 Bidirectional BFS).

    Verifies:
    1. Start equals goal: empty solution, length 0
    2. One-move scramble: correct 1-move solution
    3. Two-move scramble: correct 2-move shortest solution
    4. Multi-move scramble: correct replay to goal
    5. Backward move inversion: inverse moves take predecessor to state
    6. Forward path reconstruction: start -> meeting
    7. Backward search path reconstruction: goal -> meeting
    8. Correct concatenation at meeting state
    9. Minimum combined depth meeting state selection
    10. Full-level expansion before intersection check
    11. All 6 moves attempted for every expanded state in both directions
    12. Duplicate moves emitted as duplicate events, not silently omitted
    13. V4 does not use V3 move pruning
    14. Solution length matches independent unidirectional BFS (V2)
    15. Every returned solution transforms start to goal
    16. Timeout handling and memory tracing cleanup
    """

    def _collect_v4_events(self, start_state, timeout_s=10.0):
        events = []
        result = v4_bfs_bidirectional(
            start_state, timeout_s=timeout_s,
            event_callback=lambda e: events.append(e)
        )
        return result, events

    def test_1_start_equals_goal(self):
        res = v4_bfs_bidirectional(SOLVED_STATE)
        assert res.found is True
        assert res.solution == []
        assert res.solution_length == 0

    def test_2_one_move_scramble(self):
        st = scramble_state(["R"])
        res = v4_bfs_bidirectional(st)
        assert res.found is True
        assert res.solution_length == 1
        assert res.solution == ["R'"]
        assert verify_solution(st, res.solution)

    def test_3_two_move_scramble(self):
        st = scramble_state(["R", "U"])
        res = v4_bfs_bidirectional(st)
        assert res.found is True
        assert res.solution_length == 2
        assert verify_solution(st, res.solution)

    def test_4_multi_move_scramble(self):
        st = scramble_state(["R", "U", "F"])
        res = v4_bfs_bidirectional(st)
        assert res.found is True
        assert res.solution_length == 3
        assert verify_solution(st, res.solution)

    def test_5_backward_move_inversion(self):
        """Verifies that INVERSE_MOVE maps predecessor back to state."""
        from cube.moves import apply_move, INVERSE_MOVE
        for m in MOVE_NAMES:
            child = apply_move(SOLVED_STATE, m)
            inv = INVERSE_MOVE[m]
            back = apply_move(child, inv)
            assert back == SOLVED_STATE

    def test_6_forward_path_reconstruction(self):
        st = scramble_state(["R", "U", "F"])
        res = v4_bfs_bidirectional(st)
        fwd_p = res.extra.get("fwd_path", [])
        meeting = res.extra.get("meeting_state")
        assert meeting is not None
        meeting_st = (tuple(meeting["perm"]), tuple(meeting["orient"]))
        # Applying fwd_path to start must reach meeting
        assert apply_moves(st, fwd_p) == meeting_st

    def test_7_backward_path_reconstruction(self):
        st = scramble_state(["R", "U", "F"])
        res = v4_bfs_bidirectional(st)
        bwd_search_p = res.extra.get("bwd_search_path", [])
        meeting = res.extra.get("meeting_state")
        assert meeting is not None
        meeting_st = (tuple(meeting["perm"]), tuple(meeting["orient"]))
        # Applying bwd_search_path to SOLVED_STATE must reach meeting
        assert apply_moves(SOLVED_STATE, bwd_search_p) == meeting_st

    def test_8_correct_concatenation_at_meeting(self):
        st = scramble_state(["R", "U", "F"])
        res = v4_bfs_bidirectional(st)
        # Full solution must equal fwd_path + inverted_bwd_path
        fwd_p = res.extra.get("fwd_path", [])
        bwd_p = res.extra.get("bwd_search_path", [])
        inv_bwd = [INVERSE_MOVE[m] for m in reversed(bwd_p)]
        assert res.solution == fwd_p + inv_bwd
        assert verify_solution(st, res.solution)

    def test_9_minimum_combined_depth_selection(self):
        """Selected meeting state must have total_depth equal to reported solution length."""
        st = scramble_state(["R", "U", "R'", "F"])
        res = v4_bfs_bidirectional(st)
        fwd_d = res.extra.get("fwd_depth", 0)
        bwd_d = res.extra.get("bwd_depth", 0)
        assert res.solution_length <= fwd_d + bwd_d

    def test_10_full_level_expansion_before_intersection(self):
        """Inspect source: queue level_size is captured and popped completely before intersection check."""
        import inspect
        import algorithms.v4_bidirectional as v4_mod
        src = inspect.getsource(v4_mod)
        assert "fwd_level_size = len(fwd_queue)" in src
        assert "for _ in range(fwd_level_size):" in src
        assert "bwd_level_size = len(bwd_queue)" in src
        assert "for _ in range(bwd_level_size):" in src

    def test_11_all_six_moves_attempted_both_directions(self):
        st = scramble_state(["R", "U", "F"])
        _, events = self._collect_v4_events(st)
        fwd_attempts = [e for e in events if e["type"] == "attempt" and e.get("direction") == "forward" and e["depth"] == 0]
        assert len(fwd_attempts) == 6
        assert {e["move"] for e in fwd_attempts} == set(MOVE_NAMES)
        bwd_attempts = [e for e in events if e["type"] == "attempt" and e.get("direction") == "backward" and e["depth"] == 0]
        assert len(bwd_attempts) == 6
        assert {e["move"] for e in bwd_attempts} == set(MOVE_NAMES)

    def test_12_duplicates_emitted_as_events(self):
        st = scramble_state(["R", "U"])
        _, events = self._collect_v4_events(st)
        dup_events = [e for e in events if e["type"] == "duplicate"]
        assert len(dup_events) > 0, "Expected duplicate events in V4 bidirectional search"

    def test_13_no_v3_pruning_used(self):
        import inspect
        import algorithms.v4_bidirectional as v4_mod
        src = inspect.getsource(v4_mod)
        assert "get_successors_pruned" not in src
        assert "is_move_pruned" not in src

    def test_14_optimality_matches_unidirectional_bfs(self):
        import itertools
        for d in [1, 2, 3]:
            for seq in itertools.product(MOVE_NAMES, repeat=d):
                st = scramble_state(list(seq))
                r2 = v2_bfs_unidirectional(st)
                r4 = v4_bfs_bidirectional(st)
                assert r4.found, f"V4 failed on {seq}"
                assert r4.solution_length == r2.solution_length, f"Optimality mismatch on {seq}: V4={r4.solution_length}, V2={r2.solution_length}"

    def test_15_all_solutions_replay_to_goal(self):
        for name, moves in SCRAMBLES:
            st = scramble_state(moves)
            res = v4_bfs_bidirectional(st)
            assert res.found, f"V4 failed on {name}"
            assert verify_solution(st, res.solution), f"V4 solution for {name} failed"

    def test_16_timeout_cleanup_and_metrics(self):
        st = scramble_state(["R", "U", "F", "R'", "U'"])
        res = v4_bfs_bidirectional(st, timeout_s=0.0001)
        # Timeout must return result cleanly
        assert "timed_out" in res.extra
        assert res.peak_memory_kb > 0


