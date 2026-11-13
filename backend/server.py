"""
Zero-Dependency Standalone Python HTTP Server for Pocket Cube AI Lab.
Runs on standard Python without needing pip, fastapi, or uvicorn.
Provides:
  1. REST API endpoints (/api/cube, /api/solve, /api/history, /api/health)
  2. Static file serving for the frontend UI (http://localhost:8000/)
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import random
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from cube.state import (
    SOLVED_STATE, make_state, is_valid_state, is_solved,
    state_to_sticker_grid, describe_state, COLOR_HEX, FACE_NAMES
)
from cube.moves import apply_move, apply_moves, invert_sequence, MOVE_NAMES, ALL_MOVE_NAMES, _same_face
from algorithms.v1_dfs import v1_dfs_unpruned
from algorithms.v2_bfs import v2_bfs_unidirectional
from algorithms.v3_bfs_pruned import v3_bfs_move_pruned
from algorithms.v4_bidirectional import v4_bfs_bidirectional
from algorithms.v5_ida_star import v5_ida_star
from database import (
    save_solve_record, get_recent_solves,
    get_latest_benchmark_summary, get_verification_test_results,
    get_connection,
    create_experiment, get_active_experiment, get_experiment_by_id,
    list_experiments, set_active_experiment, update_algorithm_session,
    reset_algorithm_session
)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(WORKSPACE_ROOT, 'frontend')

ALGO_MAP = {
    "v1": v1_dfs_unpruned,
    "v2": v2_bfs_unidirectional,
    "v3": v3_bfs_move_pruned,
    "v4": v4_bfs_bidirectional,
    "v5": v5_ida_star,
}


def generate_random_scramble(depth: int) -> list[str]:
    """Generate a random non-canceling scramble sequence using {U, U', R, R', F, F'}."""
    moves = []
    last_move = None
    for _ in range(depth):
        candidates = [m for m in MOVE_NAMES if not (last_move and _same_face(m, last_move))]
        m = random.choice(candidates)
        moves.append(m)
        last_move = m
    return moves


class PocketCubeRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE_ROOT, **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        # Root redirect to frontend
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(FRONTEND_DIR, 'index.html'), 'rb') as f:
                self.wfile.write(f.read())
            return

        # Check either FRONTEND_DIR or WORKSPACE_ROOT for static assets
        target_file = os.path.join(FRONTEND_DIR, path.lstrip('/'))
        if not os.path.exists(target_file) or os.path.isdir(target_file):
            target_file = os.path.join(WORKSPACE_ROOT, path.lstrip('/'))

        if os.path.exists(target_file) and not os.path.isdir(target_file):
            content_types = {
                ".js": "application/javascript",
                ".mjs": "application/javascript",
                ".css": "text/css",
                ".html": "text/html",
                ".svg": "image/svg+xml",
                ".json": "application/json",
            }
            ext = os.path.splitext(target_file)[1]
            self.send_response(200)
            self.send_header("Content-Type", content_types.get(ext, "application/octet-stream"))
            self.end_headers()
            with open(target_file, 'rb') as f:
                self.wfile.write(f.read())
            return

        # API: Health
        if path == "/api/health":
            self._send_json({"status": "ok", "version": "1.0.0", "engine": "Python Standard Server"})
            return

        # API: Cube Solved State
        if path == "/api/cube/solved":
            grid = state_to_sticker_grid(SOLVED_STATE)
            self._send_json({
                "perm": list(SOLVED_STATE[0]),
                "orient": list(SOLVED_STATE[1]),
                "is_solved": True,
                "is_valid": True,
                "sticker_grid": grid,
                "sticker_colors": [[COLOR_HEX[c] for c in face] for face in grid],
                "face_names": FACE_NAMES,
            })
            return

        # API: History Solves
        if path == "/api/history/solves":
            query = urllib.parse.parse_qs(url_parts.query)
            limit = int(query.get("limit", [20])[0])
            self._send_json({"solves": get_recent_solves(limit)})
            return

        # API: History Benchmarks
        if path == "/api/history/benchmarks":
            self._send_json({"benchmark_summary": get_latest_benchmark_summary()})
            return

        # API: History Tests
        if path == "/api/history/tests":
            self._send_json({"verification_tests": get_verification_test_results()})
            return

        # API: History Summary
        if path == "/api/history/summary":
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM benchmarks;")
                b_cnt = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM verification_tests;")
                t_cnt = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM solve_history;")
                s_cnt = c.fetchone()[0]
            self._send_json({
                "total_benchmarks_stored": b_cnt,
                "total_verification_cases_stored": t_cnt,
                "total_solves_stored": s_cnt,
            })
            return

        # API: Get Active Experiment with All 5 Sessions
        if path == "/api/experiment/active":
            exp = get_active_experiment()
            if not exp:
                default_scramble = ["R", "U", "R'", "F", "U'"]
                inv = invert_sequence(default_scramble)
                st = apply_moves(SOLVED_STATE, default_scramble)
                exp = create_experiment(default_scramble, inv, list(st[0]), list(st[1]))
            self._send_json({"experiment": exp})
            return

        # API: List Experiments
        if path == "/api/experiment/list":
            query = urllib.parse.parse_qs(url_parts.query)
            limit = int(query.get("limit", [20])[0])
            self._send_json({"experiments": list_experiments(limit)})
            return

        # Fallback to standard file server
        super().do_GET()

    def do_POST(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}

        # API: Solve
        if path == "/api/solve":
            algo_key = data.get("algorithm", "v4").lower()
            if algo_key not in ALGO_MAP:
                self._send_json({"error": f"Unknown algorithm '{algo_key}'"}, 400)
                return

            perm = tuple(data.get("perm", []))
            orient = tuple(data.get("orient", []))
            state = make_state(perm, orient)

            if not is_valid_state(state):
                self._send_json({"error": "Invalid cube state"}, 400)
                return

            algo_fn = ALGO_MAP[algo_key]
            # V1 runs with safety timeout (unpruned 24-sticker DFS has no depth limit)
            timeout = float(data.get("timeout_s", 10.0 if algo_key == "v1" else 30.0))
            events = []
            max_events = int(data.get("max_events", 500))

            def on_event(evt):
                if len(events) < max_events:
                    events.append(evt)

            kwargs = {
                "timeout_s": timeout,
                "event_callback": on_event
            }

            res = algo_fn(state, **kwargs)
            res_dict = res.to_dict()

            # Pre-calculate step-by-step intermediate states along the solution path
            if res.found and res.solution:
                intermediate_states = []
                curr = state
                intermediate_states.append({
                    "step": 0,
                    "move": None,
                    "perm": list(curr[0]),
                    "orient": list(curr[1]),
                    "is_solved": is_solved(curr),
                })
                for step_idx, m in enumerate(res.solution, 1):
                    curr = apply_move(curr, m)
                    intermediate_states.append({
                        "step": step_idx,
                        "move": m,
                        "perm": list(curr[0]),
                        "orient": list(curr[1]),
                        "is_solved": is_solved(curr),
                    })
                res_dict["intermediate_states"] = intermediate_states

            res_dict["events"] = events
            res_dict["event_count"] = len(events)

            try:
                save_solve_record(
                    algorithm=algo_key,
                    start_perm=perm,
                    start_orient=orient,
                    result=res_dict
                )
            except Exception:
                pass

            self._send_json(res_dict)
            return

        # API: Compare All
        if path == "/api/solve/compare":
            perm = tuple(data.get("perm", []))
            orient = tuple(data.get("orient", []))
            state = make_state(perm, orient)

            if not is_valid_state(state):
                self._send_json({"error": "Invalid cube state"}, 400)
                return

            results = {}
            for name, fn in ALGO_MAP.items():
                timeout = 2.0 if name == "v1" else 15.0
                kwargs = {"timeout_s": timeout}
                try:
                    r = fn(state, **kwargs)
                    r_dict = r.to_dict()
                    results[name] = r_dict
                    try:
                        save_solve_record(
                            algorithm=name,
                            start_perm=perm,
                            start_orient=orient,
                            result=r_dict
                        )
                    except Exception:
                        pass
                except Exception as e:
                    results[name] = {"error": str(e), "found": False}

            self._send_json({"results": results})
            return

        # API: Visualize / Event collection
        if path == "/api/visualize/run":
            algo_key = data.get("algorithm", "v4").lower()
            if algo_key not in ALGO_MAP:
                self._send_json({"error": f"Unknown algorithm '{algo_key}'"}, 400)
                return

            perm = tuple(data.get("perm", []))
            orient = tuple(data.get("orient", []))
            state = make_state(perm, orient)

            events = []
            max_events = int(data.get("max_events", 1000))

            def on_event(evt):
                if len(events) < max_events:
                    events.append(evt)

            algo_fn = ALGO_MAP[algo_key]
            timeout = float(data.get("timeout_s", 10.0 if algo_key == "v1" else 30.0))
            kwargs = {
                "timeout_s": timeout,
                "event_callback": on_event
            }

            res = algo_fn(state, **kwargs)
            res_dict = res.to_dict()

            self._send_json({
                "result": res_dict,
                "events": events,
                "event_count": len(events)
            })
            return

        # API: Create Shared Experiment
        if path == "/api/experiment/create":
            moves = data.get("scramble_moves")
            depth = int(data.get("depth", 5))
            if not moves:
                moves = generate_random_scramble(depth)
            else:
                for m in moves:
                    if m not in ALL_MOVE_NAMES:
                        self._send_json({"error": f"Invalid move '{m}' for scramble. Valid: {ALL_MOVE_NAMES}"}, 400)
                        return

            initial_state = apply_moves(SOLVED_STATE, moves)
            inverse_moves = invert_sequence(moves)
            exp = create_experiment(
                scramble_moves=moves,
                inverse_moves=inverse_moves,
                initial_perm=list(initial_state[0]),
                initial_orient=list(initial_state[1])
            )
            self._send_json({"experiment": exp})
            return

        # API: Load Experiment
        if path == "/api/experiment/load":
            exp_id = data.get("experiment_id")
            if not exp_id:
                self._send_json({"error": "Missing experiment_id"}, 400)
                return
            set_active_experiment(exp_id)
            exp = get_experiment_by_id(exp_id)
            if not exp:
                self._send_json({"error": "Experiment not found"}, 404)
                return
            self._send_json({"experiment": exp})
            return

        # API: Update Algorithm Session
        if path == "/api/session/update":
            exp_id = data.get("experiment_id")
            algo = data.get("algorithm")
            if not exp_id or not algo:
                self._send_json({"error": "Missing experiment_id or algorithm"}, 400)
                return
            update_algorithm_session(
                experiment_id=exp_id,
                algorithm=algo,
                current_perm=data.get("current_perm", []),
                current_orient=data.get("current_orient", []),
                user_moves=data.get("user_moves", []),
                solver_solution=data.get("solver_solution", []),
                current_step_index=int(data.get("current_step_index", 0)),
                status=data.get("status", "not_started"),
                elapsed_ms=float(data.get("elapsed_ms", 0.0)),
                expanded_states=int(data.get("expanded_states", 0)),
                solution_length=int(data.get("solution_length", 0)),
                peak_memory_kb=float(data.get("peak_memory_kb", 0.0)),
                has_manual_interaction=bool(data.get("has_manual_interaction", False))
            )
            self._send_json({"status": "ok"})
            return

        # API: Reset Algorithm Session
        if path == "/api/session/reset":
            exp_id = data.get("experiment_id")
            algo = data.get("algorithm")
            if not exp_id or not algo:
                self._send_json({"error": "Missing experiment_id or algorithm"}, 400)
                return
            session = reset_algorithm_session(exp_id, algo)
            if not session:
                self._send_json({"error": "Failed to reset session"}, 404)
                return
            self._send_json({"session": session})
            return

        # API: Session Solve (Solves from the session's CURRENT state)
        if path == "/api/session/solve":
            exp_id = data.get("experiment_id")
            algo_key = data.get("algorithm", "v4").lower()
            if algo_key not in ALGO_MAP:
                self._send_json({"error": f"Unknown algorithm '{algo_key}'"}, 400)
                return

            perm = tuple(data.get("current_perm", []))
            orient = tuple(data.get("current_orient", []))
            state = make_state(perm, orient)

            if not is_valid_state(state):
                self._send_json({"error": "Invalid cube state"}, 400)
                return

            algo_fn = ALGO_MAP[algo_key]
            # V1 runs with safety timeout (unpruned 24-sticker DFS has no depth limit)
            timeout = float(data.get("timeout_s", 10.0 if algo_key == "v1" else 30.0))
            events = []
            max_events = int(data.get("max_events", 500))

            def on_event(evt):
                if len(events) < max_events:
                    events.append(evt)

            kwargs = {
                "timeout_s": timeout,
                "event_callback": on_event
            }

            res = algo_fn(state, **kwargs)
            res_dict = res.to_dict()

            intermediate_states = []
            if res.found:
                curr = state
                intermediate_states.append({
                    "step": 0,
                    "move": None,
                    "perm": list(curr[0]),
                    "orient": list(curr[1]),
                    "is_solved": is_solved(curr),
                })
                for step_idx, m in enumerate(res.solution, 1):
                    curr = apply_move(curr, m)
                    intermediate_states.append({
                        "step": step_idx,
                        "move": m,
                        "perm": list(curr[0]),
                        "orient": list(curr[1]),
                        "is_solved": is_solved(curr),
                    })
                res_dict["intermediate_states"] = intermediate_states

            res_dict["events"] = events
            res_dict["event_count"] = len(events)

            # Update session in DB if exp_id is provided
            user_moves = data.get("user_moves", [])
            new_status = "solved" if (res.found and len(res.solution) == 0 and is_solved(state)) else ("in_progress" if res.found else "failed")
            if exp_id:
                update_algorithm_session(
                    experiment_id=exp_id,
                    algorithm=algo_key,
                    current_perm=list(perm),
                    current_orient=list(orient),
                    user_moves=user_moves,
                    solver_solution=res.solution if res.found else [],
                    current_step_index=0,
                    status=new_status,
                    elapsed_ms=res.elapsed_ms,
                    expanded_states=res.expanded_states,
                    solution_length=res.solution_length,
                    peak_memory_kb=res.peak_memory_kb,
                    has_manual_interaction=len(user_moves) > 0
                )

            try:
                save_solve_record(
                    algorithm=algo_key,
                    start_perm=perm,
                    start_orient=orient,
                    result=res_dict
                )
            except Exception:
                pass

            self._send_json({
                "result": res_dict,
                "intermediate_states": intermediate_states,
                "events": events,
                "event_count": len(events)
            })
            return

        # API: Cube Apply Move (Validated server-side transition)
        if path == "/api/cube/apply-move":
            perm = tuple(data.get("perm", []))
            orient = tuple(data.get("orient", []))
            move = data.get("move")
            if move not in ALL_MOVE_NAMES:
                self._send_json({"error": f"Invalid move '{move}'. Permitted: {ALL_MOVE_NAMES}"}, 400)
                return

            state = make_state(perm, orient)
            if not is_valid_state(state):
                self._send_json({"error": "Invalid initial cube state"}, 400)
                return

            new_state = apply_move(state, move)
            self._send_json({
                "perm": list(new_state[0]),
                "orient": list(new_state[1]),
                "move": move,
                "is_valid": is_valid_state(new_state),
                "is_solved": is_solved(new_state),
                "orient_sum": sum(new_state[1]) % 3
            })
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def _send_json(self, payload: dict, status_code: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(server_address, PocketCubeRequestHandler)
    print("\n" + "=" * 65)
    print(" POCKET CUBE AI LAB — PYTHON SERVER STARTED")
    print("=" * 65)
    print(f" URL: http://127.0.0.1:{port}/")
    print(f" API: http://127.0.0.1:{port}/api/health")
    print(" SQLite Database: backend/pocket_cube.db")
    print(" Press Ctrl+C to terminate.")
    print("=" * 65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
