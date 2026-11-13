/**
 * Python Backend API Client
 *
 * ARCHITECTURAL MANDATE:
 * All search algorithms (V1-V5), heuristic evaluations, and state validations
 * execute exclusively in Python. This client sends requests to the Python FastAPI
 * backend and returns the authentic execution measurements and solution paths.
 */

const API_BASE = "http://127.0.0.1:8000/api";

/**
 * Check if the Python backend is live.
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "ok";
  } catch (e) {
    return false;
  }
}

/**
 * Request Python to solve the cube state.
 * @param {number[]} perm
 * @param {number[]} orient
 * @param {string} algorithm - "v1"|"v2"|"v3"|"v4"|"v5"
 * @param {number} maxDepth
 * @param {number} timeoutS
 */
export async function solveCubeWithPython(perm, orient, algorithm = "v4", maxDepth = 11, timeoutS = 30.0) {
  const res = await fetch(`${API_BASE}/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      perm,
      orient,
      algorithm,
      max_depth: maxDepth,
      timeout_s: timeoutS
    })
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Python solver failed");
  }

  return await res.json();
}

/**
 * Request Python to run real search with collected trace events.
 */
export async function visualizeSearchWithPython(perm, orient, algorithm = "v4", maxDepth = 11) {
  const res = await fetch(`${API_BASE}/visualize/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      perm,
      orient,
      algorithm,
      max_depth: maxDepth,
      timeout_s: 30.0,
      max_events: 1000
    })
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Python visualization runner failed");
  }

  return await res.json();
}

/**
 * Request Python to run head-to-head comparison across all algorithms.
 */
export async function compareAllWithPython(perm, orient) {
  const res = await fetch(`${API_BASE}/solve/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      perm,
      orient,
      algorithm: "v2",
      timeout_s: 15.0
    })
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Python compare failed");
  }

  return await res.json();
}

/**
 * Fetch SQLite persistent experiment history.
 */
export async function fetchHistorySummary() {
  try {
    const res = await fetch(`${API_BASE}/history/summary`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("History summary fetch failed:", e);
  }
  return null;
}

export async function fetchRecentSolves(limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/history/solves?limit=${limit}`);
    if (res.ok) {
      const data = await res.json();
      return data.solves || [];
    }
  } catch (e) {
    console.warn("History fetch failed:", e);
  }
  return [];
}

export async function fetchBenchmarkSummary() {
  try {
    const res = await fetch(`${API_BASE}/history/benchmarks`);
    if (res.ok) {
      const data = await res.json();
      return data.benchmark_summary || [];
    }
  } catch (e) {
    console.warn("Benchmark history fetch failed:", e);
  }
  return [];
}

export async function fetchVerificationTests() {
  try {
    const res = await fetch(`${API_BASE}/history/tests`);
    if (res.ok) {
      const data = await res.json();
      return data.verification_tests || [];
    }
  } catch (e) {
    console.warn("Verification tests fetch failed:", e);
  }
  return [];
}

/**
 * Shared Scramble & Independent Session API
 */

export async function fetchActiveExperiment() {
  const res = await fetch(`${API_BASE}/experiment/active`);
  if (!res.ok) throw new Error("Failed to load active experiment");
  const data = await res.json();
  return data.experiment;
}

export async function createSharedExperiment(scrambleMoves = null, depth = 5) {
  const payload = {};
  if (scrambleMoves && scrambleMoves.length > 0) {
    payload.scramble_moves = scrambleMoves;
  } else {
    payload.depth = depth;
  }
  const res = await fetch(`${API_BASE}/experiment/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to create experiment");
  }
  const data = await res.json();
  return data.experiment;
}

export async function listAllExperiments(limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/experiment/list?limit=${limit}`);
    if (res.ok) {
      const data = await res.json();
      return data.experiments || [];
    }
  } catch (e) {
    console.warn("Failed to list experiments:", e);
  }
  return [];
}

export async function loadSavedExperiment(experimentId) {
  const res = await fetch(`${API_BASE}/experiment/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ experiment_id: experimentId })
  });
  if (!res.ok) throw new Error("Failed to load experiment");
  const data = await res.json();
  return data.experiment;
}

export async function updateSessionProgress(sessionData) {
  const res = await fetch(`${API_BASE}/session/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionData)
  });
  return res.ok;
}

export async function resetSessionToSharedScramble(experimentId, algorithm) {
  const res = await fetch(`${API_BASE}/session/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ experiment_id: experimentId, algorithm })
  });
  if (!res.ok) throw new Error("Failed to reset session");
  const data = await res.json();
  return data.session;
}

export async function solveFromCurrentState(experimentId, algorithm, currentPerm, currentOrient, userMoves = [], timeoutS = 30.0) {
  const res = await fetch(`${API_BASE}/session/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      experiment_id: experimentId,
      algorithm,
      current_perm: currentPerm,
      current_orient: currentOrient,
      user_moves: userMoves,
      timeout_s: timeoutS
    })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Solver failed");
  }
  return await res.json();
}

export async function applyMoveServerSide(perm, orient, move) {
  const res = await fetch(`${API_BASE}/cube/apply-move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ perm, orient, move })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Move rejected by server");
  }
  return await res.json();
}
