#!/usr/bin/env python3
"""
Pocket Cube AI Lab — Command Line Interface (CLI)
===================================================
Academic evaluation tool providing independent execution of all algorithms,
verification suites, benchmark experiments, SQLite history inspection,
and theoretical hand-worked traces directly from Python.

Usage:
    python3 backend/cli.py test
    python3 backend/cli.py verify
    python3 backend/cli.py benchmark [--depths 2,4,6]
    python3 backend/cli.py solve --algo v4 --scramble "R U R'"
    python3 backend/cli.py compare --scramble "R U R' F"
    python3 backend/cli.py history
    python3 backend/cli.py trace
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import argparse
import json
from cube.state import SOLVED_STATE, is_solved, describe_state
from cube.moves import apply_moves, MOVE_NAMES
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star
from database import get_recent_solves, get_latest_benchmark_summary, get_verification_test_results
from run_tests import run_all_tests
from benchmark.run_experiments import run_verification_suite, run_depth_benchmark

ALGO_MAP = {
    "v1": ("V1 Unpruned DFS", v1_dfs_unpruned),
    "v2": ("V2 Unidirectional BFS", v2_bfs_unidirectional),
    "v3": ("V3 Move-Pruned BFS", v3_bfs_move_pruned),
    "v4": ("V4 Bidirectional BFS", v4_bfs_bidirectional),
    "v5": ("V5 IDA*", v5_ida_star),
}


def cmd_test(args):
    """Run all 87 unit tests."""
    success = run_all_tests()
    sys.exit(0 if success else 1)


def cmd_verify(args):
    """Run the 20-case randomized verification suite."""
    n = args.n or 20
    results = run_verification_suite(n_cases=n)
    passed = sum(1 for r in results if r["passed"])
    print(f"\nVerification Score: {passed}/{n} cases passed.")


def cmd_benchmark(args):
    """Run multi-depth empirical benchmarking."""
    depths = [int(d.strip()) for d in args.depths.split(",")]
    n_per_depth = args.samples or 3
    run_depth_benchmark(depths=depths, n_per_depth=n_per_depth)


def cmd_solve(args):
    """Solve a scrambled cube using the specified algorithm."""
    algo_key = args.algo.lower()
    if algo_key not in ALGO_MAP:
        print(f"Error: Unknown algorithm '{algo_key}'. Choices: {list(ALGO_MAP.keys())}")
        sys.exit(1)

    scramble_moves = [m.strip() for m in args.scramble.split() if m.strip()]
    for m in scramble_moves:
        if m not in MOVE_NAMES:
            print(f"Error: Illegal move '{m}'. Valid quarter turns: {MOVE_NAMES}")
            sys.exit(1)

    label, fn = ALGO_MAP[algo_key]
    start = apply_moves(SOLVED_STATE, scramble_moves)
    print(f"Scramble: {' '.join(scramble_moves)} (length: {len(scramble_moves)})")
    print(f"Initial State Solved: {is_solved(start)}")
    print(f"Running {label}...")

    timeout = 5.0 if algo_key == "v1" else (args.timeout or 30.0)
    kwargs = {"timeout_s": timeout}

    res = fn(start, **kwargs)

    print("\n" + "=" * 50)
    print(f" RESULT: {label}")
    print("=" * 50)
    print(f"Found Solution    : {res.found}")
    print(f"Solution Length   : {res.solution_length}")
    print(f"Solution Sequence : {' '.join(res.solution) if res.solution else 'None'}")
    print(f"States Expanded   : {res.expanded_states:,}")
    print(f"States Generated  : {res.generated_states:,}")
    print(f"Wall-Clock Time   : {res.elapsed_ms:.2f} ms")
    print(f"Peak Memory       : {res.peak_memory_kb:.2f} KB")

    if res.found:
        final_state = apply_moves(start, res.solution)
        print(f"Verification Check: Goal reached? {is_solved(final_state)}")


def cmd_compare(args):
    """Compare all 5 algorithms head-to-head on the same state."""
    scramble_moves = [m.strip() for m in args.scramble.split() if m.strip()]
    start = apply_moves(SOLVED_STATE, scramble_moves)
    print(f"Scramble: {' '.join(scramble_moves)}")
    print("\n" + "-" * 75)
    print(f"{'Algorithm':<22} | {'Found':<6} | {'Len':<4} | {'Expanded':<9} | {'Time (ms)':<10} | {'Peak KB':<8}")
    print("-" * 75)

    for k in ["v1", "v2", "v3", "v4", "v5"]:
        label, fn = ALGO_MAP[k]
        kwargs = {"timeout_s": 2.0 if k == "v1" else 15.0}
        try:
            r = fn(start, **kwargs)
            print(f"{label:<22} | {str(r.found):<6} | {r.solution_length:<4} | {r.expanded_states:<9,} | {r.elapsed_ms:<10.2f} | {r.peak_memory_kb:<8.1f}")
        except Exception as e:
            print(f"{label:<22} | ERROR: {e}")
    print("-" * 75)


def cmd_history(args):
    """Print persistent SQLite experiment history."""
    solves = get_recent_solves(limit=10)
    summary = get_latest_benchmark_summary()
    tests = get_verification_test_results()

    print("\n=== SQLITE PERSISTENT EXPERIMENT SUMMARY ===")
    print(f"Stored Benchmarks Groups : {len(summary)}")
    print(f"Stored Verification Runs : {len(tests)}")
    print(f"Stored Solves Logged     : {len(solves)}")

    if solves:
        print("\n--- Recent Solves (Top 5) ---")
        for s in solves[:5]:
            print(f"[{s['timestamp'][:19]}] Algo: {s['algorithm'].upper():<3} | Len: {s['solution_length']} | Expanded: {s['expanded_states']:<6} | Time: {s['elapsed_ms']:6.1f}ms | Sol: {s['solution']}")


def cmd_trace(args):
    """Print hand-worked tuple trace for Q1 (R -> U -> R')."""
    from cube.moves import apply_move
    s0 = SOLVED_STATE
    s1 = apply_move(s0, "R")
    s2 = apply_move(s1, "U")
    s3 = apply_move(s2, "R'")

    print("\n=== HAND-WORKED TUPLE TRACE (Q1) ===")
    print(f"s0 (Solved)  : perm={s0[0]}, orient={s0[1]}")
    print(f"s1 (After R) : perm={s1[0]}, orient={s1[1]} (orient sum = {sum(s1[1])} = 0 mod 3)")
    print(f"s2 (After U) : perm={s2[0]}, orient={s2[1]} (orient sum = {sum(s2[1])} = 0 mod 3)")
    print(f"s3 (After R'): perm={s3[0]}, orient={s3[1]} (orient sum = {sum(s3[1])} = 0 mod 3)")


def main():
    parser = argparse.ArgumentParser(description="Pocket Cube AI Lab Academic CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # test
    sub.add_parser("test", help="Run automated test suite (87 tests)")

    # verify
    p_ver = sub.add_parser("verify", help="Run 20-case randomized verification suite")
    p_ver.add_argument("-n", type=int, default=20, help="Number of test cases (default: 20)")

    # benchmark
    p_bm = sub.add_parser("benchmark", help="Run empirical multi-depth benchmark")
    p_bm.add_argument("--depths", default="2,4,6", help="Comma-separated depths (default: 2,4,6)")
    p_bm.add_argument("--samples", type=int, default=3, help="Cases per depth (default: 3)")

    # solve
    p_solve = sub.add_parser("solve", help="Solve a scramble with a specified algorithm")
    p_solve.add_argument("--algo", default="v4", choices=["v1", "v2", "v3", "v4", "v5"], help="Algorithm")
    p_solve.add_argument("--scramble", required=True, help="Space-separated moves (e.g. \"R U R'\")")
    p_solve.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    p_solve.add_argument("--max-depth", type=int, default=11, help="Max depth (for V1)")

    # compare
    p_cmp = sub.add_parser("compare", help="Compare all 5 algorithms on a scramble")
    p_cmp.add_argument("--scramble", required=True, help="Space-separated moves")

    # history
    sub.add_parser("history", help="Show SQLite persistent experiment history")

    # trace
    sub.add_parser("trace", help="Show Q1 hand-worked tuple trace")

    args = parser.parse_args()

    cmds = {
        "test": cmd_test,
        "verify": cmd_verify,
        "benchmark": cmd_benchmark,
        "solve": cmd_solve,
        "compare": cmd_compare,
        "history": cmd_history,
        "trace": cmd_trace,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
