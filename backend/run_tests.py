"""
Self-contained test runner for Pocket Cube test suites.
Can be executed with standard Python without any third-party test dependencies.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import time
from cube.state import (
    SOLVED_STATE, SOLVED_PERM, SOLVED_ORIENT,
    make_state, solved_state, is_valid_state, is_solved,
    is_valid_perm, is_valid_orient, is_valid_orient_sum,
    state_hash, states_equal, state_to_sticker_grid
)
from cube.moves import (
    MOVE_NAMES, INVERSE_MOVE, apply_move, apply_moves,
    get_successors, get_successors_pruned, invert_sequence, _same_face
)
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star, heuristic


def run_all_tests():
    passed = 0
    failed = 0

    def check(name, condition, err_msg=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}: {err_msg}")

    print("==================================================")
    print(" 1. TESTING CUBE STATE REPRESENTATION & INVARIANTS")
    print("==================================================")
    check("Solved state perm is (0..6)", SOLVED_STATE[0] == (0, 1, 2, 3, 4, 5, 6))
    check("Solved state orient is (0..0)", SOLVED_STATE[1] == (0, 0, 0, 0, 0, 0, 0))
    check("is_solved(SOLVED_STATE) is True", is_solved(SOLVED_STATE))
    check("is_valid_state(SOLVED_STATE) is True", is_valid_state(SOLVED_STATE))
    check("sum(orient) % 3 == 0 for solved state", sum(SOLVED_STATE[1]) % 3 == 0)

    # Permutation validity
    check("Valid perm accepted", is_valid_perm((0, 1, 2, 3, 4, 5, 6)))
    check("Duplicate in perm rejected", not is_valid_perm((0, 1, 2, 3, 4, 5, 5)))
    check("Piece index out of range rejected", not is_valid_perm((0, 1, 2, 3, 4, 5, 7)))

    # Orientation validity & invariant
    check("Valid orient accepted", is_valid_orient((0, 1, 2, 0, 1, 2, 0)))
    check("Orient >= 3 rejected", not is_valid_orient((0, 1, 2, 3, 0, 0, 0)))
    check("Orient sum % 3 != 0 rejected", not is_valid_orient_sum((1, 0, 0, 0, 0, 0, 0)))
    check("Invalid state with bad orient rejected", not is_valid_state(((0,1,2,3,4,5,6), (1,0,0,0,0,0,0))))

    # Hashability and Dict/Set usability
    s_set = {SOLVED_STATE}
    check("State usable in hash sets", SOLVED_STATE in s_set)
    s_dict = {SOLVED_STATE: 42}
    check("State usable in dict keys", s_dict[SOLVED_STATE] == 42)

    # Sticker grid representation
    grid = state_to_sticker_grid(SOLVED_STATE)
    check("Sticker grid has 6 faces", len(grid) == 6)
    check("Each face has 4 stickers", all(len(face) == 4 for face in grid))
    from cube.state import COLOR_WHITE, COLOR_YELLOW, sticker_grid_to_state
    check("U face is all white", all(c == COLOR_WHITE for c in grid[0]))
    check("D face is all yellow", all(c == COLOR_YELLOW for c in grid[1]))
    check("Sticker grid decodes back to solved state", sticker_grid_to_state(grid) == SOLVED_STATE)

    print("\n==================================================")
    print(" 2. TESTING MOVE MECHANICS, INVERSES & CYCLES")
    print("==================================================")
    for m in MOVE_NAMES:
        inv = INVERSE_MOVE[m]
        # M then M' is identity
        s1 = apply_move(SOLVED_STATE, m)
        s_back = apply_move(s1, inv)
        check(f"{m} then {inv} == SOLVED_STATE", s_back == SOLVED_STATE)

        # M^4 is identity
        s4 = SOLVED_STATE
        for _ in range(4):
            s4 = apply_move(s4, m)
        check(f"{m}^4 == SOLVED_STATE", s4 == SOLVED_STATE)

        # Invariant preserved
        check(f"{m} preserves sum(orient)%3==0", sum(s1[1]) % 3 == 0)
        check(f"{m} keeps state valid", is_valid_state(s1))

    # Test inverse sequence
    seq = ["R", "U", "F", "R'", "U'"]
    inv_seq = invert_sequence(seq)
    check("invert_sequence produces exact inverted reverse", inv_seq == ["U", "R", "F'", "U'", "R'"])
    s_seq = apply_moves(SOLVED_STATE, seq)
    check("Sequence then inverted sequence == SOLVED_STATE", apply_moves(s_seq, inv_seq) == SOLVED_STATE)

    # Successors
    succs = get_successors(SOLVED_STATE)
    check("get_successors returns 6 moves", len(succs) == 6)
    pruned_succs_run1 = get_successors_pruned(SOLVED_STATE, "R", run_length=1)
    check("get_successors_pruned drops immediate inverse (5 moves remaining)", len(pruned_succs_run1) == 5 and "R'" not in [m for m, _ in pruned_succs_run1])
    pruned_succs_run2 = get_successors_pruned(SOLVED_STATE, "R", run_length=2)
    check("get_successors_pruned drops same face after run_length 2 (4 moves remaining)", len(pruned_succs_run2) == 4 and all(m[0] != "R" for m, _ in pruned_succs_run2))

    print("\n==================================================")
    print(" 3. TESTING HEURISTIC ADMISSIBILITY (V5)")
    print("==================================================")
    check("h(SOLVED_STATE) == 0", heuristic(SOLVED_STATE) == 0)
    for m in MOVE_NAMES:
        h1 = heuristic(apply_move(SOLVED_STATE, m))
        check(f"h(s) <= 1 for 1-move scramble ({m})", h1 <= 1)

    print("\n==================================================")
    print(" 4. TESTING SEARCH ALGORITHMS (V1-V5)")
    print("==================================================")
    # Solved state base case
    check("V1 solved state returns []", v1_dfs_unpruned(SOLVED_STATE).solution == [])
    check("V2 solved state returns []", v2_bfs_unidirectional(SOLVED_STATE).solution == [])
    check("V3 solved state returns []", v3_bfs_move_pruned(SOLVED_STATE).solution == [])
    check("V4 solved state returns []", v4_bfs_bidirectional(SOLVED_STATE).solution == [])
    check("V5 solved state returns []", v5_ida_star(SOLVED_STATE).solution == [])

    # Test depth 1 scrambles across all optimal solvers
    for m in MOVE_NAMES:
        st = apply_move(SOLVED_STATE, m)
        r2 = v2_bfs_unidirectional(st)
        r3 = v3_bfs_move_pruned(st)
        r4 = v4_bfs_bidirectional(st)
        r5 = v5_ida_star(st)
        check(f"V2 solves 1-move scramble ({m}) optimally", r2.solution_length == 1 and is_solved(apply_moves(st, r2.solution)))
        check(f"V3 solves 1-move scramble ({m}) optimally", r3.solution_length == 1 and is_solved(apply_moves(st, r3.solution)))
        check(f"V4 solves 1-move scramble ({m}) optimally", r4.solution_length == 1 and is_solved(apply_moves(st, r4.solution)))
        check(f"V5 solves 1-move scramble ({m}) optimally", r5.solution_length == 1 and is_solved(apply_moves(st, r5.solution)))

    # Test depth 3 scramble: R U R'
    st3 = apply_moves(SOLVED_STATE, ["R", "U", "R'"])
    r2_3 = v2_bfs_unidirectional(st3)
    r3_3 = v3_bfs_move_pruned(st3)
    r4_3 = v4_bfs_bidirectional(st3)
    r5_3 = v5_ida_star(st3)
    check("V2 solves depth 3 (R U R') optimally in 3 moves", r2_3.solution_length == 3 and is_solved(apply_moves(st3, r2_3.solution)))
    check("V3 solves depth 3 (R U R') optimally in 3 moves", r3_3.solution_length == 3 and is_solved(apply_moves(st3, r3_3.solution)))
    check("V4 solves depth 3 (R U R') optimally in 3 moves", r4_3.solution_length == 3 and is_solved(apply_moves(st3, r4_3.solution)))
    check("V5 solves depth 3 (R U R') optimally in 3 moves", r5_3.solution_length == 3 and is_solved(apply_moves(st3, r5_3.solution)))

    print("\n==================================================")
    print(" 5. TESTING SHARED SCRAMBLE, INDEPENDENT SESSIONS & PERSISTENCE")
    print("==================================================")
    from database import (
        create_experiment, get_active_experiment, get_experiment_by_id,
        update_algorithm_session, reset_algorithm_session
    )

    scramble = ["R", "U", "R'", "F"]
    inv_scramble = invert_sequence(scramble)
    st_scrambled = apply_moves(SOLVED_STATE, scramble)

    # Invariant: inverse restores solved state
    check("Scramble inverse restores solved state", is_solved(apply_moves(st_scrambled, inv_scramble)))

    # Create experiment
    exp = create_experiment(
        scramble_moves=scramble,
        inverse_moves=inv_scramble,
        initial_perm=list(st_scrambled[0]),
        initial_orient=list(st_scrambled[1])
    )
    exp_id = exp["id"]

    # 1. Confirm every algorithm starts from the exact same shared initial state
    for algo in ["v1", "v2", "v3", "v4", "v5"]:
        sess = exp["sessions"][algo]
        check(f"{algo.upper()} starts at shared initial perm", sess["current_perm"] == list(st_scrambled[0]))
        check(f"{algo.upper()} starts at shared initial orient", sess["current_orient"] == list(st_scrambled[1]))

    # 2. Confirm independent algorithm execution (genuine search, not inverse shortcut)
    v2_res = v2_bfs_unidirectional(st_scrambled)
    v4_res = v4_bfs_bidirectional(st_scrambled)
    v5_res = v5_ida_star(st_scrambled)
    check("V2 solution is valid and solves the cube", is_solved(apply_moves(st_scrambled, v2_res.solution)))
    check("V4 solution is valid and solves the cube", is_solved(apply_moves(st_scrambled, v4_res.solution)))
    check("V5 solution is valid and solves the cube", is_solved(apply_moves(st_scrambled, v5_res.solution)))

    # 3. Confirm algorithms record distinct metrics
    check("V2 and V4 metrics independently recorded", v2_res.expanded_states > 0 and v4_res.expanded_states > 0)

    # 4. Confirm user moves modify ONLY that algorithm's session
    # Simulate user turning 'R' on V2
    user_move = "R"
    st_user = apply_move(st_scrambled, user_move)
    update_algorithm_session(
        experiment_id=exp_id,
        algorithm="v2",
        current_perm=list(st_user[0]),
        current_orient=list(st_user[1]),
        user_moves=[user_move],
        solver_solution=[],
        current_step_index=0,
        status="in_progress",
        has_manual_interaction=True
    )

    # Retrieve experiment from DB to verify isolation
    reloaded = get_experiment_by_id(exp_id)
    check("V2 working state updated with user move", reloaded["sessions"]["v2"]["current_perm"] == list(st_user[0]))
    check("V3 working state remained untouched at shared scramble", reloaded["sessions"]["v3"]["current_perm"] == list(st_scrambled[0]))
    check("V4 working state remained untouched at shared scramble", reloaded["sessions"]["v4"]["current_perm"] == list(st_scrambled[0]))

    # 5. Confirm solving from user's current state solves from THAT state, not original scramble
    v4_from_user = v4_bfs_bidirectional(st_user)
    check("V4 solves from user-modified state to solved", is_solved(apply_moves(st_user, v4_from_user.solution)))

    # 6. Reset V2 session back to shared scramble
    reset_algorithm_session(exp_id, "v2")
    reloaded_after_reset = get_experiment_by_id(exp_id)
    check("V2 reset restored working state to shared scramble", reloaded_after_reset["sessions"]["v2"]["current_perm"] == list(st_scrambled[0]))
    check("V2 reset cleared user moves", len(reloaded_after_reset["sessions"]["v2"]["user_moves"]) == 0)

    print("\n==================================================")
    print(" 6. TESTING STAGE 1 (V1 24-STICKER NAIVE DFS COMPLIANCE)")
    print("==================================================")
    import inspect
    from cube.stickers import (
        SOLVED_STICKERS, apply_sticker_move, apply_sticker_moves,
        is_sticker_solved, V1_MOVE_NAMES, MOVE_INVERSES
    )

    # 1. 24 stickers preserved by moves
    all_stickers_preserved = True
    for m in V1_MOVE_NAMES:
        after = apply_sticker_move(SOLVED_STICKERS, m)
        if len(after) != 24 or sorted(after) != sorted(SOLVED_STICKERS):
            all_stickers_preserved = False
            break
    check("All 24 stickers preserved by every legal move", all_stickers_preserved)

    # 2. Move followed by inverse restores sticker array
    inverses_pass = True
    for m in V1_MOVE_NAMES:
        inv = MOVE_INVERSES[m]
        after = apply_sticker_move(apply_sticker_move(SOLVED_STICKERS, m), inv)
        if tuple(after) != SOLVED_STICKERS:
            inverses_pass = False
            break
    check("Each move followed by inverse restores original sticker array", inverses_pass)

    # 3. Four identical quarter turns restore original array
    four_turns_pass = True
    for m in V1_MOVE_NAMES:
        curr = list(SOLVED_STICKERS)
        for _ in range(4):
            curr = apply_sticker_move(curr, m)
        if tuple(curr) != SOLVED_STICKERS:
            four_turns_pass = False
            break
    check("Four identical quarter turns restore original sticker array", four_turns_pass)

    # 4. Solved check on sticker array
    check("Sticker-array solved-state check works", is_sticker_solved(SOLVED_STICKERS) and not is_sticker_solved(apply_sticker_move(SOLVED_STICKERS, 'U')))

    # 5. V1 signature has no max_depth parameter
    sig = inspect.signature(v1_dfs_unpruned)
    check("V1 signature has no max_depth parameter", "max_depth" not in sig.parameters)

    # 6. V1 has no depth-limit condition during execution
    scramble_deep = apply_sticker_move(SOLVED_STICKERS, 'F')
    res_deep = v1_dfs_unpruned(scramble_deep, timeout_s=0.04)
    check("V1 has no depth-limit condition (depth exceeded 11)", res_deep.max_depth > 11)

    # 7. V1 has no visited-state tracking
    check("V1 has no visited-state tracking (visited_states == 0)", res_deep.visited_states == 0 and res_deep.extra.get("has_visited_set") is False)

    # 8. V1 can return valid solution for simple scrambles
    scramble_simple = apply_sticker_move(SOLVED_STICKERS, "U'")
    res_simple = v1_dfs_unpruned(scramble_simple, timeout_s=5.0)
    check("V1 returns valid solution for simple scramble before timeout", res_simple.found and res_simple.solution == ["U"])

    # 9. Timeout is reported separately from search exhaustion
    check("V1 reports timeout separately from search exhaustion", not res_deep.found and res_deep.extra.get("status") == "timed_out")

    print("\n==================================================")
    print(" 7. TESTING STAGE 2 (V2 UNIDIRECTIONAL BFS COMPLIANCE)")
    print("==================================================")
    # Helper to collect V2 events
    def _collect_v2_events(start_state, timeout_s=10.0):
        evs = []
        r = v2_bfs_unidirectional(start_state, timeout_s=timeout_s, event_callback=lambda e: evs.append(e))
        return r, evs

    # 1. Root attempts all 6 moves
    st_r = apply_moves(SOLVED_STATE, ["R", "U", "F"])
    _, ev_r = _collect_v2_events(st_r)
    root_attempts = [e for e in ev_r if e["type"] == "attempt" and e["depth"] == 0]
    check("V2 root state attempts all 6 moves", len(root_attempts) == 6)

    # 2. All 6 move names in root attempts
    root_attempt_moves = {e["move"] for e in root_attempts}
    check("V2 all 6 move names appear in root attempts", root_attempt_moves == set(MOVE_NAMES))

    # 3. Duplicate event produced when revisiting state
    st_ru = apply_moves(SOLVED_STATE, ["R", "U"])
    _, ev_ru = _collect_v2_events(st_ru)
    dup_events = [e for e in ev_ru if e["type"] == "duplicate"]
    check("V2 inverse moves/cycles produce duplicate events", len(dup_events) > 0 and any(e["depth"] >= 2 for e in dup_events))

    # 4. Same-face moves still attempted (no V3 pruning)
    depth1_attempt_moves = {e["move"] for e in ev_r if e["type"] == "attempt" and e["depth"] == 1}
    check("V2 consecutive same-face moves still attempted", set(MOVE_NAMES).issubset(depth1_attempt_moves))

    # 5. V2 has no previous-move parameter or queue carrying last_move
    import algorithms.v2_bfs as v2_mod
    v2_src = inspect.getsource(v2_mod)
    check("V2 has no last_move parameter/tracking", "last_move" not in v2_src)

    # 6. V2 does not call V3 pruning helpers
    check("V2 does not call get_successors_pruned or _same_face", "get_successors_pruned" not in v2_src and "_same_face" not in v2_src)

    # 7. Each discovered state enqueued exactly once
    enq_paths = [tuple(e["path"] + [e["move"]]) for e in ev_ru if e["type"] == "enqueue"]
    disc_count = len([e for e in ev_ru if e["type"] == "discover"])
    enq_count = len([e for e in ev_ru if e["type"] == "enqueue"])
    goal_count = len([e for e in ev_ru if e["type"] == "goal"])
    check("V2 each discovered state enqueued exactly once", len(enq_paths) == len(set(enq_paths)) and disc_count == enq_count + goal_count)

    # 8. FIFO order: depths nondecreasing
    expand_depths = [e["depth"] for e in ev_r if e["type"] == "expand"]
    check("V2 FIFO expansion depth nondecreasing", all(expand_depths[i] >= expand_depths[i-1] for i in range(1, len(expand_depths))))

    # 9. Duplicate events present in stream
    check("V2 duplicate events present in event stream", len(dup_events) > 0)

    # 10. Reconstructed solution reaches goal
    sol_ok = True
    for s_moves in [["R"], ["U"], ["F"], ["R", "U"], ["R", "F"], ["R", "U", "F"], ["R", "U", "R'"]]:
        s_st = apply_moves(SOLVED_STATE, s_moves)
        s_res = v2_bfs_unidirectional(s_st)
        if not s_res.found or apply_moves(s_st, s_res.solution) != SOLVED_STATE:
            sol_ok = False
            break
    check("V2 reconstructed solution reaches goal across scrambles", sol_ok)

    # 11. Solution length matches optimal reference
    opt_ok = True
    for s_moves in [["R"], ["R", "U"], ["R", "U", "F"]]:
        s_st = apply_moves(SOLVED_STATE, s_moves)
        r2 = v2_bfs_unidirectional(s_st)
        r3 = v3_bfs_move_pruned(s_st)
        if r2.solution_length != r3.solution_length:
            opt_ok = False
            break
    check("V2 solution length matches optimal reference", opt_ok)

    # 12. Maximum frontier size tracked correctly
    r_front = v2_bfs_unidirectional(st_r)
    check("V2 max frontier size >= 6 on depth-3 scramble", r_front.max_frontier_size >= 6)

    # 13. Single parent dictionary (no separate visited dict)
    check("V2 uses single parent dict (no duplicate visited dict)", "visited = {}" not in v2_src and "visited:" not in v2_src)

    # 14. Attempt events contain child_state
    att_evs = [e for e in ev_r if e["type"] == "attempt"]
    check("V2 attempt events contain child_state (perm & orient)", len(att_evs) > 0 and all("child_state" in e and "perm" in e["child_state"] and "orient" in e["child_state"] for e in att_evs[:6]))

    # 15. Expand immediately followed by 6 attempts
    block_ok = True
    i = 0
    checked_blocks = 0
    while i < len(ev_r):
        if ev_r[i]["type"] == "expand":
            attempts = []
            found_g = False
            j = i + 1
            while j < len(ev_r) and ev_r[j]["type"] in ("attempt", "discover", "duplicate", "enqueue", "goal"):
                if ev_r[j]["type"] == "attempt":
                    attempts.append(ev_r[j])
                if ev_r[j]["type"] == "goal":
                    found_g = True
                j += 1
            if not found_g:
                if len(attempts) != 6:
                    block_ok = False
                    break
                checked_blocks += 1
            i = j
        else:
            i += 1
    check("V2 expand event immediately followed by all 6 attempts", block_ok and checked_blocks >= 1)

    print("\n==================================================")
    print(" 8. TESTING STAGE 3 (V3 MOVE-PRUNED BFS COMPLIANCE)")
    print("==================================================")
    # 1. Scramble R R solved in 2 moves
    st_rr = apply_moves(SOLVED_STATE, ["R", "R"])
    res_rr = v3_bfs_move_pruned(st_rr)
    check("V3 solves R R half-turn scramble in 2 moves", res_rr.found and res_rr.solution_length == 2 and apply_moves(st_rr, res_rr.solution) == SOLVED_STATE)

    # 2. Scramble R R R solved in 1 move
    st_rrr = apply_moves(SOLVED_STATE, ["R", "R", "R"])
    res_rrr = v3_bfs_move_pruned(st_rrr)
    check("V3 solves R R R (3-turn cycle) in 1 move (R)", res_rrr.found and res_rrr.solution == ["R"] and apply_moves(st_rrr, res_rrr.solution) == SOLVED_STATE)

    # 3. Immediate inverse pruned
    ev_v3 = []
    st_ruf = apply_moves(SOLVED_STATE, ["R", "U", "F"])
    _ = v3_bfs_move_pruned(st_ruf, event_callback=lambda e: ev_v3.append(e))
    prunes = [e for e in ev_v3 if e["type"] == "prune"]
    check("V3 prunes immediate inverses before state generation", len(prunes) > 0 and any("inverse" in e.get("explanation", "").lower() for e in prunes))

    # 4. 3-turn consecutive cycle pruned
    ev_v3_run = []
    st_rruf = apply_moves(SOLVED_STATE, ["R", "R", "U", "F"])
    _ = v3_bfs_move_pruned(st_rruf, event_callback=lambda e: ev_v3_run.append(e))
    prunes_run = [e for e in ev_v3_run if e["type"] == "prune"]
    check("V3 prunes 3rd consecutive turn in same direction", any("3" in e.get("explanation", "") or "consecutive" in e.get("explanation", "") for e in prunes_run))

    # 5. Half-turn sequence solved optimally
    st_rru = apply_moves(SOLVED_STATE, ["R", "R", "U"])
    res_rru = v3_bfs_move_pruned(st_rru)
    res_rru_v2 = v2_bfs_unidirectional(st_rru)
    check("V3 solves state requiring same-face consecutive turns (R R U)", res_rru.found and res_rru.solution_length == res_rru_v2.solution_length and apply_moves(st_rru, res_rru.solution) == SOLVED_STATE)

    # 6. Optimality vs unpruned V2 on all depth-1 and depth-2 scrambles
    import itertools
    opt_v3_ok = True
    for d in [1, 2]:
        for seq in itertools.product(MOVE_NAMES, repeat=d):
            st_case = apply_moves(SOLVED_STATE, list(seq))
            r2_case = v2_bfs_unidirectional(st_case)
            r3_case = v3_bfs_move_pruned(st_case)
            if not r3_case.found or r3_case.solution_length != r2_case.solution_length:
                opt_v3_ok = False
                break
        if not opt_v3_ok:
            break
    check("V3 canonical pruning preserves shortest path vs V2 across depths 1 & 2", opt_v3_ok)

    # 7. All standard scrambles replay to goal
    all_replay = True
    for s_name, s_moves in [("R", ["R"]), ("U", ["U"]), ("RU", ["R", "U"]), ("RUF", ["R", "U", "F"]), ("RUR", ["R", "U", "R'"])]:
        st_test = apply_moves(SOLVED_STATE, s_moves)
        r3_test = v3_bfs_move_pruned(st_test)
        if not r3_test.found or apply_moves(st_test, r3_test.solution) != SOLVED_STATE:
            all_replay = False
            break
    check("V3 all returned solutions replay correctly to goal", all_replay)

    # 8. V3 source inspection: composite context search key used
    import inspect
    import algorithms.v3_bfs_pruned as v3_mod
    v3_src = inspect.getsource(v3_mod)
    check("V3 uses composite (state, context) visited search key", "child_key = (child, child_context)" in v3_src and "is_move_pruned" in v3_src)

    print("\n==================================================")
    print(" 9. TESTING STAGE 4 (V4 BIDIRECTIONAL BFS COMPLIANCE)")
    print("==================================================")
    # 1. Start == goal
    res_v4_0 = v4_bfs_bidirectional(SOLVED_STATE)
    check("V4 start equals goal returns empty solution", res_v4_0.found and res_v4_0.solution == [])

    # 2. 1-move scramble
    st_v4_1 = apply_moves(SOLVED_STATE, ["R"])
    res_v4_1 = v4_bfs_bidirectional(st_v4_1)
    check("V4 solves 1-move scramble", res_v4_1.found and res_v4_1.solution_length == 1 and apply_moves(st_v4_1, res_v4_1.solution) == SOLVED_STATE)

    # 3. 2-move scramble
    st_v4_2 = apply_moves(SOLVED_STATE, ["R", "U"])
    res_v4_2 = v4_bfs_bidirectional(st_v4_2)
    check("V4 solves 2-move scramble", res_v4_2.found and res_v4_2.solution_length == 2 and apply_moves(st_v4_2, res_v4_2.solution) == SOLVED_STATE)

    # 4. Multi-move scramble
    st_v4_3 = apply_moves(SOLVED_STATE, ["R", "U", "F"])
    res_v4_3 = v4_bfs_bidirectional(st_v4_3)
    check("V4 solves 3-move scramble optimally", res_v4_3.found and res_v4_3.solution_length == 3 and apply_moves(st_v4_3, res_v4_3.solution) == SOLVED_STATE)

    # 5. Forward and backward path reconstruction
    fwd_p = res_v4_3.extra.get("fwd_path", [])
    bwd_search_p = res_v4_3.extra.get("bwd_search_path", [])
    meeting = res_v4_3.extra.get("meeting_state")
    meeting_st = (tuple(meeting["perm"]), tuple(meeting["orient"])) if meeting else None
    check("V4 forward path reaches meeting state", meeting_st is not None and apply_moves(st_v4_3, fwd_p) == meeting_st)
    check("V4 backward search path reaches meeting state from goal", meeting_st is not None and apply_moves(SOLVED_STATE, bwd_search_p) == meeting_st)

    # 6. Correct concatenation
    inv_bwd = [INVERSE_MOVE[m] for m in reversed(bwd_search_p)]
    check("V4 full solution is fwd_path + inverted backward moves", res_v4_3.solution == fwd_p + inv_bwd)

    # 7. Level-by-level complete expansion
    import algorithms.v4_bidirectional as v4_mod
    v4_src = inspect.getsource(v4_mod)
    check("V4 uses complete level expansion via queue level_size", "fwd_level_size = len(fwd_queue)" in v4_src and "bwd_level_size = len(bwd_queue)" in v4_src)

    # 8. All 6 moves attempted in both directions
    evs_v4 = []
    _ = v4_bfs_bidirectional(st_v4_3, event_callback=lambda e: evs_v4.append(e))
    fwd_attempts = [e for e in evs_v4 if e["type"] == "attempt" and e.get("direction") == "forward" and e["depth"] == 0]
    bwd_attempts = [e for e in evs_v4 if e["type"] == "attempt" and e.get("direction") == "backward" and e["depth"] == 0]
    check("V4 attempts all 6 moves in both forward and backward directions", len(fwd_attempts) == 6 and len(bwd_attempts) == 6)

    # 9. Duplicate events emitted
    check("V4 emits duplicate events when states revisited", any(e["type"] == "duplicate" for e in evs_v4))

    # 10. No V3 move pruning in V4
    check("V4 does not use V3 move pruning", "get_successors_pruned" not in v4_src and "is_move_pruned" not in v4_src)

    # 11. Optimality matches unpruned V2 across depths 1, 2, 3
    opt_v4_ok = True
    for d in [1, 2, 3]:
        for seq in itertools.product(MOVE_NAMES, repeat=d):
            st_c = apply_moves(SOLVED_STATE, list(seq))
            r2_c = v2_bfs_unidirectional(st_c)
            r4_c = v4_bfs_bidirectional(st_c)
            if not r4_c.found or r4_c.solution_length != r2_c.solution_length:
                opt_v4_ok = False
                break
        if not opt_v4_ok:
            break
    check("V4 solution length matches V2 on all scrambles across depths 1, 2, 3", opt_v4_ok)

    # 12. Timeout safety and cleanup
    res_v4_to = v4_bfs_bidirectional(st_v4_3, timeout_s=0.0001)
    check("V4 timeout returns result and stops tracemalloc", res_v4_to.peak_memory_kb > 0 and "timed_out" in res_v4_to.extra)



    print("\n==================================================")
    print(f" TOTAL TESTS: {passed + failed} | PASSED: {passed} | FAILED: {failed}")
    print("==================================================")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
