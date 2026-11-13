"""
SQLite Database Layer for Pocket Cube AI Lab.
Persists all benchmark experiments, verification suite test runs,
algorithm statistics, and interactive solve histories.
Uses Python standard library `sqlite3` — zero external dependencies.
"""
from __future__ import annotations
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'pocket_cube.db')


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH):
    """Initialize database tables and indices."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Benchmarks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            depth INTEGER NOT NULL,
            algorithm TEXT NOT NULL,
            case_index INTEGER,
            scramble TEXT,
            found INTEGER NOT NULL,
            solution TEXT,
            solution_length INTEGER,
            expanded_states INTEGER,
            generated_states INTEGER,
            visited_states INTEGER,
            peak_memory_kb REAL,
            elapsed_ms REAL,
            extra TEXT
        )
        """)

        # 2. Verification suite tests table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            case_number INTEGER NOT NULL,
            scramble_depth INTEGER NOT NULL,
            scramble TEXT NOT NULL,
            optimal_length INTEGER,
            all_passed INTEGER NOT NULL,
            v2_len INTEGER, v2_ms REAL, v2_expanded INTEGER,
            v3_len INTEGER, v3_ms REAL, v3_expanded INTEGER,
            v4_len INTEGER, v4_ms REAL, v4_expanded INTEGER,
            v5_len INTEGER, v5_ms REAL, v5_expanded INTEGER
        )
        """)

        # 3. Solve history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS solve_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            scramble TEXT,
            start_perm TEXT NOT NULL,
            start_orient TEXT NOT NULL,
            found INTEGER NOT NULL,
            solution TEXT,
            solution_length INTEGER,
            expanded_states INTEGER,
            generated_states INTEGER,
            visited_states INTEGER,
            elapsed_ms REAL,
            peak_memory_kb REAL,
            extra TEXT
        )
        """)

        # 4. Experiments table (Shared Scramble & State)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            scramble_moves TEXT NOT NULL,
            inverse_moves TEXT NOT NULL,
            initial_perm TEXT NOT NULL,
            initial_orient TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """)

        # 5. Algorithm sessions table (Independent V1-V5 Progress)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS algorithm_sessions (
            id TEXT PRIMARY KEY,
            experiment_id TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            current_perm TEXT NOT NULL,
            current_orient TEXT NOT NULL,
            user_moves TEXT NOT NULL,
            solver_solution TEXT NOT NULL,
            current_step_index INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'not_started',
            elapsed_ms REAL DEFAULT 0.0,
            expanded_states INTEGER DEFAULT 0,
            solution_length INTEGER DEFAULT 0,
            peak_memory_kb REAL DEFAULT 0.0,
            has_manual_interaction INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id)
        )
        """)

        # Indices for efficient querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bench_depth_algo ON benchmarks(depth, algorithm);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bench_time ON benchmarks(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_solve_time ON solve_history(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_exp ON algorithm_sessions(experiment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_active ON experiments(is_active);")
        conn.commit()


# ---------------------------------------------------------------------------
# Insert operations
# ---------------------------------------------------------------------------

def save_benchmark_record(
    depth: int,
    algorithm: str,
    case_index: int,
    scramble: List[str],
    res: Dict[str, Any],
    timestamp: Optional[str] = None,
    db_path: str = DB_PATH,
) -> int:
    ts = timestamp or datetime.utcnow().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO benchmarks (
            timestamp, depth, algorithm, case_index, scramble,
            found, solution, solution_length, expanded_states,
            generated_states, visited_states, peak_memory_kb,
            elapsed_ms, extra
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            depth,
            algorithm,
            case_index,
            " ".join(scramble) if isinstance(scramble, list) else str(scramble),
            1 if res.get("found") else 0,
            json.dumps(res.get("solution", [])),
            res.get("solution_length", 0),
            res.get("expanded_states", 0),
            res.get("generated_states", 0),
            res.get("visited_states", 0),
            res.get("peak_memory_kb", 0.0),
            res.get("elapsed_ms", 0.0),
            json.dumps(res.get("extra", {})),
        ))
        conn.commit()
        return cursor.lastrowid


def save_verification_test(
    case_number: int,
    scramble_depth: int,
    scramble: List[str],
    optimal_length: int,
    all_passed: bool,
    v2_info: Dict[str, Any],
    v3_info: Dict[str, Any],
    v4_info: Dict[str, Any],
    v5_info: Dict[str, Any],
    timestamp: Optional[str] = None,
    db_path: str = DB_PATH,
) -> int:
    ts = timestamp or datetime.utcnow().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO verification_tests (
            timestamp, case_number, scramble_depth, scramble, optimal_length, all_passed,
            v2_len, v2_ms, v2_expanded,
            v3_len, v3_ms, v3_expanded,
            v4_len, v4_ms, v4_expanded,
            v5_len, v5_ms, v5_expanded
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            case_number,
            scramble_depth,
            " ".join(scramble) if isinstance(scramble, list) else str(scramble),
            optimal_length,
            1 if all_passed else 0,
            v2_info.get("len", 0), v2_info.get("ms", 0.0), v2_info.get("exp", 0),
            v3_info.get("len", 0), v3_info.get("ms", 0.0), v3_info.get("exp", 0),
            v4_info.get("len", 0), v4_info.get("ms", 0.0), v4_info.get("exp", 0),
            v5_info.get("len", 0), v5_info.get("ms", 0.0), v5_info.get("exp", 0),
        ))
        conn.commit()
        return cursor.lastrowid


def save_solve_record(
    algorithm: str,
    start_perm: tuple,
    start_orient: tuple,
    result: Dict[str, Any],
    scramble: Optional[List[str]] = None,
    db_path: str = DB_PATH,
) -> int:
    ts = datetime.utcnow().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO solve_history (
            timestamp, algorithm, scramble, start_perm, start_orient,
            found, solution, solution_length, expanded_states,
            generated_states, visited_states, elapsed_ms, peak_memory_kb, extra
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            algorithm,
            " ".join(scramble) if scramble else "",
            json.dumps(list(start_perm)),
            json.dumps(list(start_orient)),
            1 if result.get("found") else 0,
            json.dumps(result.get("solution", [])),
            result.get("solution_length", 0),
            result.get("expanded_states", 0),
            result.get("generated_states", 0),
            result.get("visited_states", 0),
            result.get("elapsed_ms", 0.0),
            result.get("peak_memory_kb", 0.0),
            json.dumps(result.get("extra", {})),
        ))
        conn.commit()
        return cursor.lastrowid


# ---------------------------------------------------------------------------
# Query operations
# ---------------------------------------------------------------------------

def get_recent_solves(limit: int = 50, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM solve_history ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_latest_benchmark_summary(db_path: str = DB_PATH) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT depth, algorithm,
               COUNT(*) as count,
               AVG(elapsed_ms) as avg_ms,
               AVG(expanded_states) as avg_expanded,
               AVG(peak_memory_kb) as avg_memory_kb,
               AVG(solution_length) as avg_length
        FROM benchmarks
        WHERE found = 1
        GROUP BY depth, algorithm
        ORDER BY depth ASC, algorithm ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_verification_test_results(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM verification_tests ORDER BY id DESC LIMIT 50
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Experiment & Algorithm Session Persistence
# ---------------------------------------------------------------------------

def create_experiment(
    scramble_moves: List[str],
    inverse_moves: List[str],
    initial_perm: List[int],
    initial_orient: List[int],
    experiment_id: Optional[str] = None,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Create a new shared experiment and initialize independent sessions for V1..V5.
    Marks this experiment as the active one.
    """
    exp_id = experiment_id or f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    created_at = datetime.utcnow().isoformat()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Deactivate previous active experiments
        cursor.execute("UPDATE experiments SET is_active = 0 WHERE is_active = 1;")

        # Insert new experiment
        cursor.execute("""
        INSERT INTO experiments (
            id, created_at, scramble_moves, inverse_moves, initial_perm, initial_orient, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            exp_id,
            created_at,
            json.dumps(scramble_moves),
            json.dumps(inverse_moves),
            json.dumps(initial_perm),
            json.dumps(initial_orient)
        ))

        # Initialize independent sessions for all 5 algorithms
        algo_names = ["v1", "v2", "v3", "v4", "v5"]
        sessions = {}
        for algo in algo_names:
            sess_id = f"{exp_id}_{algo}"
            cursor.execute("""
            INSERT INTO algorithm_sessions (
                id, experiment_id, algorithm, current_perm, current_orient,
                user_moves, solver_solution, current_step_index, status,
                elapsed_ms, expanded_states, solution_length, peak_memory_kb,
                has_manual_interaction, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'not_started', 0.0, 0, 0, 0.0, 0, ?)
            """, (
                sess_id,
                exp_id,
                algo,
                json.dumps(initial_perm),
                json.dumps(initial_orient),
                json.dumps([]),
                json.dumps([]),
                created_at
            ))
            sessions[algo] = {
                "id": sess_id,
                "experiment_id": exp_id,
                "algorithm": algo,
                "current_perm": initial_perm,
                "current_orient": initial_orient,
                "user_moves": [],
                "solver_solution": [],
                "current_step_index": 0,
                "status": "not_started",
                "elapsed_ms": 0.0,
                "expanded_states": 0,
                "solution_length": 0,
                "peak_memory_kb": 0.0,
                "has_manual_interaction": False,
                "updated_at": created_at
            }

        conn.commit()

    return {
        "id": exp_id,
        "created_at": created_at,
        "scramble_moves": scramble_moves,
        "inverse_moves": inverse_moves,
        "initial_perm": initial_perm,
        "initial_orient": initial_orient,
        "is_active": 1,
        "sessions": sessions
    }


def get_active_experiment(db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the currently active experiment with all 5 algorithm sessions."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            return None

        exp = dict(row)
        exp["scramble_moves"] = json.loads(exp["scramble_moves"])
        exp["inverse_moves"] = json.loads(exp["inverse_moves"])
        exp["initial_perm"] = json.loads(exp["initial_perm"])
        exp["initial_orient"] = json.loads(exp["initial_orient"])

        # Fetch algorithm sessions
        cursor.execute("SELECT * FROM algorithm_sessions WHERE experiment_id = ? ORDER BY algorithm ASC;", (exp["id"],))
        sess_rows = cursor.fetchall()
        sessions = {}
        for s in sess_rows:
            sd = dict(s)
            sd["current_perm"] = json.loads(sd["current_perm"])
            sd["current_orient"] = json.loads(sd["current_orient"])
            sd["user_moves"] = json.loads(sd["user_moves"])
            sd["solver_solution"] = json.loads(sd["solver_solution"])
            sd["has_manual_interaction"] = bool(sd["has_manual_interaction"])
            sessions[sd["algorithm"]] = sd
        exp["sessions"] = sessions
        return exp


def get_experiment_by_id(exp_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve an experiment by ID with all 5 algorithm sessions."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?;", (exp_id,))
        row = cursor.fetchone()
        if not row:
            return None

        exp = dict(row)
        exp["scramble_moves"] = json.loads(exp["scramble_moves"])
        exp["inverse_moves"] = json.loads(exp["inverse_moves"])
        exp["initial_perm"] = json.loads(exp["initial_perm"])
        exp["initial_orient"] = json.loads(exp["initial_orient"])

        cursor.execute("SELECT * FROM algorithm_sessions WHERE experiment_id = ? ORDER BY algorithm ASC;", (exp["id"],))
        sess_rows = cursor.fetchall()
        sessions = {}
        for s in sess_rows:
            sd = dict(s)
            sd["current_perm"] = json.loads(sd["current_perm"])
            sd["current_orient"] = json.loads(sd["current_orient"])
            sd["user_moves"] = json.loads(sd["user_moves"])
            sd["solver_solution"] = json.loads(sd["solver_solution"])
            sd["has_manual_interaction"] = bool(sd["has_manual_interaction"])
            sessions[sd["algorithm"]] = sd
        exp["sessions"] = sessions
        return exp


def list_experiments(limit: int = 20, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List recent experiments summary."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.id, e.created_at, e.scramble_moves, e.is_active,
               COUNT(s.id) as session_count,
               SUM(CASE WHEN s.status = 'solved' THEN 1 ELSE 0 END) as solved_count
        FROM experiments e
        LEFT JOIN algorithm_sessions s ON e.id = s.experiment_id
        GROUP BY e.id
        ORDER BY e.created_at DESC
        LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            rd = dict(r)
            rd["scramble_moves"] = json.loads(rd["scramble_moves"])
            result.append(rd)
        return result


def set_active_experiment(exp_id: str, db_path: str = DB_PATH) -> bool:
    """Set the specified experiment as active."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE experiments SET is_active = 0;")
        cursor.execute("UPDATE experiments SET is_active = 1 WHERE id = ?;", (exp_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_algorithm_session(
    experiment_id: str,
    algorithm: str,
    current_perm: List[int],
    current_orient: List[int],
    user_moves: List[str],
    solver_solution: List[str],
    current_step_index: int,
    status: str,
    elapsed_ms: float = 0.0,
    expanded_states: int = 0,
    solution_length: int = 0,
    peak_memory_kb: float = 0.0,
    has_manual_interaction: bool = False,
    db_path: str = DB_PATH
) -> bool:
    """Update progress, moves, metrics and state for a single algorithm session."""
    now = datetime.utcnow().isoformat()
    sess_id = f"{experiment_id}_{algorithm}"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO algorithm_sessions (
            id, experiment_id, algorithm, current_perm, current_orient,
            user_moves, solver_solution, current_step_index, status,
            elapsed_ms, expanded_states, solution_length, peak_memory_kb,
            has_manual_interaction, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            current_perm = excluded.current_perm,
            current_orient = excluded.current_orient,
            user_moves = excluded.user_moves,
            solver_solution = excluded.solver_solution,
            current_step_index = excluded.current_step_index,
            status = excluded.status,
            elapsed_ms = excluded.elapsed_ms,
            expanded_states = excluded.expanded_states,
            solution_length = excluded.solution_length,
            peak_memory_kb = excluded.peak_memory_kb,
            has_manual_interaction = excluded.has_manual_interaction,
            updated_at = excluded.updated_at;
        """, (
            sess_id,
            experiment_id,
            algorithm,
            json.dumps(current_perm),
            json.dumps(current_orient),
            json.dumps(user_moves),
            json.dumps(solver_solution),
            current_step_index,
            status,
            elapsed_ms,
            expanded_states,
            solution_length,
            peak_memory_kb,
            1 if has_manual_interaction else 0,
            now
        ))
        conn.commit()
        return True


def reset_algorithm_session(
    experiment_id: str,
    algorithm: str,
    db_path: str = DB_PATH
) -> Optional[Dict[str, Any]]:
    """Reset an algorithm session back to the shared initial scramble state."""
    exp = get_experiment_by_id(experiment_id, db_path)
    if not exp:
        return None

    init_perm = exp["initial_perm"]
    init_orient = exp["initial_orient"]
    now = datetime.utcnow().isoformat()
    sess_id = f"{experiment_id}_{algorithm}"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE algorithm_sessions SET
            current_perm = ?,
            current_orient = ?,
            user_moves = ?,
            solver_solution = ?,
            current_step_index = 0,
            status = 'not_started',
            elapsed_ms = 0.0,
            expanded_states = 0,
            solution_length = 0,
            peak_memory_kb = 0.0,
            has_manual_interaction = 0,
            updated_at = ?
        WHERE id = ?;
        """, (
            json.dumps(init_perm),
            json.dumps(init_orient),
            json.dumps([]),
            json.dumps([]),
            now,
            sess_id
        ))
        conn.commit()

    return {
        "id": sess_id,
        "experiment_id": experiment_id,
        "algorithm": algorithm,
        "current_perm": init_perm,
        "current_orient": init_orient,
        "user_moves": [],
        "solver_solution": [],
        "current_step_index": 0,
        "status": "not_started",
        "elapsed_ms": 0.0,
        "expanded_states": 0,
        "solution_length": 0,
        "peak_memory_kb": 0.0,
        "has_manual_interaction": False,
        "updated_at": now
    }


# Auto-initialize table schema on import
init_db()
