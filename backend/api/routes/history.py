"""
History API routes — query SQLite persistent experiment records.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter
from database import (
    get_recent_solves,
    get_latest_benchmark_summary,
    get_verification_test_results,
    get_connection
)

router = APIRouter()


@router.get("/solves")
def list_recent_solves(limit: int = 50):
    """Retrieve recent interactive solve records."""
    return {"solves": get_recent_solves(limit)}


@router.get("/benchmarks")
def list_benchmarks():
    """Retrieve latest aggregated benchmark results from SQLite."""
    summary = get_latest_benchmark_summary()
    return {"benchmark_summary": summary}


@router.get("/tests")
def list_verification_tests():
    """Retrieve saved verification suite test results from SQLite."""
    tests = get_verification_test_results()
    return {"verification_tests": tests}


@router.get("/summary")
def get_overall_summary():
    """Retrieve high-level experiment statistics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM benchmarks;")
        bench_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM verification_tests;")
        test_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM solve_history;")
        solve_count = cursor.fetchone()[0]

    return {
        "total_benchmarks_stored": bench_count,
        "total_verification_cases_stored": test_count,
        "total_solves_stored": solve_count,
    }
