/**
 * Pocket Cube AI Lab — Frontend Application Controller
 * Shared Scramble, Independent V1-V5 Sessions & Step-by-Step Python Solver
 *
 * All state-space search algorithms (V1-V5), heuristic evaluations,
 * state validations, and database persistence execute strictly in Python.
 */

import {
  getSolvedState, isSolved, applyMove, applyMoves, invertSequence,
  MOVE_NAMES, ALL_MOVE_NAMES, INVERSE_MOVE, MOVE_EXPLANATIONS,
  stateToStickers, COLOR_HEX
} from './cube.js';

import { Cube3D } from './cube3d.js';

import {
  checkBackendHealth,
  fetchActiveExperiment,
  createSharedExperiment,
  listAllExperiments,
  loadSavedExperiment,
  updateSessionProgress,
  resetSessionToSharedScramble,
  solveFromCurrentState,
  compareAllWithPython,
  fetchHistorySummary,
  fetchRecentSolves
} from './api.js';

// Application State
let activeExperiment = null;
let selectedAlgorithm = "v4";
let isBackendConnected = false;
let isPlaying = false;
let playLoopTimer = null;
let playbackSpeed = 1.0;

// Undo / Redo for manual turns on the current algorithm session
const undoStack = [];
const redoStack = [];

// Initialize 3D Cube Canvas
const cubeContainer = document.getElementById('cube-3d-container');
const cube3d = new Cube3D(cubeContainer);

// DOM Elements: Top Banner
const expIdBadge = document.getElementById('exp-id-badge');
const sharedScrambleDisplay = document.getElementById('shared-scramble-display');
const sharedInverseDisplay = document.getElementById('shared-inverse-display');
const depthInput = document.getElementById('scramble-depth-input');
const depthDisplay = document.getElementById('depth-display');
const newRandomScrambleBtn = document.getElementById('new-random-scramble-btn');
const customScrambleInput = document.getElementById('custom-scramble-input');
const applyCustomScrambleBtn = document.getElementById('apply-custom-scramble-btn');
const resetExpBtn = document.getElementById('reset-exp-btn');
const expHistoryBtn = document.getElementById('exp-history-btn');

// Modal Elements
const expModal = document.getElementById('exp-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const modalExpList = document.getElementById('modal-exp-list');

// Left Column: 3D Stage & Manual Turns
const activeAlgoCubeTitle = document.getElementById('active-algo-cube-title');
const cubeStatusBadge = document.getElementById('cube-status-badge');
const cubeStatusText = document.getElementById('cube-status-text');
const resetCameraBtn = document.getElementById('reset-camera-btn');
const undoBtn = document.getElementById('undo-btn');
const redoBtn = document.getElementById('redo-btn');

// Right Column: Solver & Sessions
const backendStatus = document.getElementById('backend-status');
const solveBtn = document.getElementById('solve-btn');
const metricTime = document.getElementById('metric-time');
const metricExpanded = document.getElementById('metric-expanded');
const metricLength = document.getElementById('metric-length');
const metricMemory = document.getElementById('metric-memory');

const restartBtn = document.getElementById('restart-btn');
const prevStepBtn = document.getElementById('prev-step-btn');
const playBtn = document.getElementById('play-btn');
const nextStepBtn = document.getElementById('next-step-btn');
const resetSessionBtn = document.getElementById('reset-session-btn');
const speedSelect = document.getElementById('speed-select');
const progressIndicator = document.getElementById('progress-indicator');

// Move Explanation & Educational Panel
const expMoveBadge = document.getElementById('exp-move-badge');
const expMoveTitle = document.getElementById('exp-move-title');
const expMoveDir = document.getElementById('exp-move-dir');
const expMoveDesc = document.getElementById('exp-move-desc');
const eduModeToggle = document.getElementById('edu-mode-toggle');
const eduPanel = document.getElementById('edu-panel');
const eduPermDisplay = document.getElementById('edu-perm-display');
const eduOrientDisplay = document.getElementById('edu-orient-display');
const eduExplanationText = document.getElementById('edu-explanation-text');
const stateValidationBadge = document.getElementById('state-validation-badge');

// 3 Separate History Displays
const historyScrambleRow = document.getElementById('history-scramble-row');
const historyUserAlgoLabel = document.getElementById('history-user-algo-label');
const historyUserRow = document.getElementById('history-user-row');
const historySolverAlgoLabel = document.getElementById('history-solver-algo-label');
const solutionBreadcrumbs = document.getElementById('solution-breadcrumbs');

// Compare & SQLite History Tabs
const compareAllBtn = document.getElementById('compare-all-btn');
const compareTableBody = document.getElementById('compare-table-body');
const historyTableBody = document.getElementById('history-table-body');
const historySummaryBadge = document.getElementById('history-summary-badge');

// Exploration Trace Elements (Requirements: Inspect Machine Exploration & Play Events)
const explorationSection = document.getElementById('exploration-section');
const exploreAlgoTitle = document.getElementById('explore-algo-title');
const exploreMetaExpanded = document.getElementById('explore-meta-expanded');
const exploreMetaGenerated = document.getElementById('explore-meta-generated');
const exploreMetaEvents = document.getElementById('explore-meta-events');
const exploreSync3D = document.getElementById('explore-sync-3d');
const exploreReturnCubeBtn = document.getElementById('explore-return-cube-btn');
const exploreFirstBtn = document.getElementById('explore-first-btn');
const explorePrevBtn = document.getElementById('explore-prev-btn');
const explorePlayBtn = document.getElementById('explore-play-btn');
const exploreNextBtn = document.getElementById('explore-next-btn');
const exploreLastBtn = document.getElementById('explore-last-btn');
const exploreSlider = document.getElementById('explore-slider');
const exploreStepCounter = document.getElementById('explore-step-counter');
const exploreSpeedSelect = document.getElementById('explore-speed-select');
const exploreEventTypeBadge = document.getElementById('explore-event-type-badge');
const exploreEventDepth = document.getElementById('explore-event-depth');
const exploreEventMove = document.getElementById('explore-event-move');
const exploreEventTitle = document.getElementById('explore-event-title');
const exploreEventExplanation = document.getElementById('explore-event-explanation');
const exploreEventExpanded = document.getElementById('explore-event-expanded');
const exploreEventGenerated = document.getElementById('explore-event-generated');
const exploreEventTime = document.getElementById('explore-event-time');
const exploreTableBody = document.getElementById('explore-table-body');

// Search Tree Visualization Elements
const viewTreeTabBtn = document.getElementById('view-tree-tab-btn');
const viewTableTabBtn = document.getElementById('view-table-tab-btn');
const treeBreadcrumb = document.getElementById('tree-breadcrumb');
const treePathDisplay = document.getElementById('tree-path-display');
const treeControlsGroup = document.getElementById('tree-controls-group');
const treeFilterAllBtn = document.getElementById('tree-filter-all-btn');
const treeFilterSolBtn = document.getElementById('tree-filter-sol-btn');
const treeZoomInBtn = document.getElementById('tree-zoom-in-btn');
const treeZoomOutBtn = document.getElementById('tree-zoom-out-btn');
const treeZoomFitBtn = document.getElementById('tree-zoom-fit-btn');
const treeViewport = document.getElementById('tree-viewport');
const searchTreeSvg = document.getElementById('search-tree-svg');
const treePanLayer = document.getElementById('tree-pan-layer');
const treeLinksLayer = document.getElementById('tree-links-layer');
const treeNodesLayer = document.getElementById('tree-nodes-layer');
const treeEmptyNotice = document.getElementById('tree-empty-notice');
const treeLegendBar = document.getElementById('tree-legend-bar');
const eventTableContainer = document.getElementById('event-table-container');

// V4 Dual-Tree Visualization Elements
const v4DualTreeViewport = document.getElementById('v4-dual-tree-viewport');
const v4LayoutToggleGroup = document.getElementById('v4-layout-toggle-group');
const v4ViewConnectedBtn = document.getElementById('v4-view-connected-btn');
const v4ViewSplitBtn = document.getElementById('v4-view-split-btn');

// Inverted Connected Tree Elements
const v4ConnectedContainer = document.getElementById('v4-connected-container');
const v4ConnectedTreeSvg = document.getElementById('v4-connected-tree-svg');
const v4ConnectedPanLayer = document.getElementById('v4-connected-pan-layer');
const v4ConnFwdLinks = document.getElementById('v4-conn-fwd-links');
const v4ConnBridgeLayer = document.getElementById('v4-conn-bridge-layer');
const v4ConnBwdLinks = document.getElementById('v4-conn-bwd-links');
const v4ConnFwdNodes = document.getElementById('v4-conn-fwd-nodes');
const v4ConnBwdNodes = document.getElementById('v4-conn-bwd-nodes');

// Split Side-by-Side Elements
const v4SplitContainer = document.getElementById('v4-split-container');
const v4FwdPanel = document.getElementById('v4-fwd-panel');
const v4BwdPanel = document.getElementById('v4-bwd-panel');
const v4FwdContainer = document.getElementById('v4-fwd-container');
const v4BwdContainer = document.getElementById('v4-bwd-container');
const v4FwdTreeSvg = document.getElementById('v4-fwd-tree-svg');
const v4BwdTreeSvg = document.getElementById('v4-bwd-tree-svg');
const v4FwdPanLayer = document.getElementById('v4-fwd-pan-layer');
const v4BwdPanLayer = document.getElementById('v4-bwd-pan-layer');
const v4FwdLinksLayer = document.getElementById('v4-fwd-links');
const v4FwdNodesLayer = document.getElementById('v4-fwd-nodes');
const v4BwdLinksLayer = document.getElementById('v4-bwd-links');
const v4BwdNodesLayer = document.getElementById('v4-bwd-nodes');

const v4BridgePanel = document.getElementById('v4-bridge-panel');
const v4FwdPathText = document.getElementById('v4-fwd-path-text');
const v4BwdPathText = document.getElementById('v4-bwd-path-text');
const v4SolPathText = document.getElementById('v4-sol-path-text');
const v4MeetingExplanation = document.getElementById('v4-meeting-explanation');
const v4FocusMeetingBtn = document.getElementById('v4-focus-meeting-btn');
const v4ReplayCubeBtn = document.getElementById('v4-replay-cube-btn');
const v4BridgeMinimizeBtn = document.getElementById('v4-bridge-minimize-btn');

let isV4Mode = false;
let v4LayoutMode = "connected"; // "connected" (inverted hourglass) | "split" (side-by-side)
let v4FwdTreeData = null;
let v4BwdTreeData = null;
let v4FwdNodesByKey = new Map();
let v4BwdNodesByKey = new Map();
let v4ConnPan = { x: 0, y: 0 };
let v4ConnScale = 1.0;
let isV4ConnPanning = false;
let v4ConnPanStart = { x: 0, y: 0 };
let v4FwdPan = { x: 0, y: 0 };
let v4FwdScale = 1.0;
let v4BwdPan = { x: 0, y: 0 };
let v4BwdScale = 1.0;
let isV4FwdPanning = false;
let v4FwdPanStart = { x: 0, y: 0 };
let isV4BwdPanning = false;
let v4BwdPanStart = { x: 0, y: 0 };

// ---------------------------------------------------------------------------
// Navigation Tabs
// ---------------------------------------------------------------------------
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

    if (btn.dataset.tab === 'history') {
      loadHistoryFromSQLite();
    }
  });
});

// Camera Reset
resetCameraBtn.addEventListener('click', () => {
  cube3d.resetCamera();
});

// Speed Control
function getTurnDuration() {
  const base = 360;
  return Math.max(70, Math.round(base / playbackSpeed));
}

function getInterMovePause() {
  const base = 180;
  return Math.max(40, Math.round(base / playbackSpeed));
}

speedSelect.addEventListener('change', (e) => {
  playbackSpeed = parseFloat(e.target.value) || 1.0;
});

// ---------------------------------------------------------------------------
// Active Session Helper
// ---------------------------------------------------------------------------
function getActiveSession() {
  if (!activeExperiment || !activeExperiment.sessions) return null;
  return activeExperiment.sessions[selectedAlgorithm];
}

// ---------------------------------------------------------------------------
// Sync 3D Cube & UI to Current Active Session
// ---------------------------------------------------------------------------
function syncActiveSessionToUI() {
  const session = getActiveSession();
  if (!session) return;

  stopAutoPlay();
  undoStack.length = 0;
  redoStack.length = 0;
  updateUndoRedoButtons();

  activeAlgoCubeTitle.textContent = `${session.algorithm.toUpperCase()} Working State`;
  historyUserAlgoLabel.textContent = session.algorithm.toUpperCase();
  historySolverAlgoLabel.textContent = session.algorithm.toUpperCase();

  // Replay all moves to reconstruct the exact 3D cube for this method
  const scrambleMoves = activeExperiment.scramble_moves || [];
  const userMoves = session.user_moves || [];
  const solverSolution = session.solver_solution || [];
  const executedSolverMoves = solverSolution.slice(0, session.current_step_index || 0);

  const totalMoves = [...scrambleMoves, ...userMoves, ...executedSolverMoves];
  cube3d.setFromMoveSequence(totalMoves);

  // Update 2D net and status
  const currState = { perm: session.current_perm, orient: session.current_orient };
  updateCube2DNet(currState);

  // Update Status Badges
  updateStatusBadges();

  // Update Metrics
  metricTime.textContent = `${(session.elapsed_ms || 0.0).toFixed(1)} ms`;
  metricExpanded.textContent = (session.expanded_states || 0).toLocaleString();
  metricLength.textContent = session.solution_length || (session.solver_solution ? session.solver_solution.length : 0);
  metricMemory.textContent = `${(session.peak_memory_kb || 0.0).toFixed(1)} KB`;

  // Update 3 Separate History Panels
  renderScrambleHistory();
  renderUserActionHistory();
  renderSolverHistory();

  // Playback Controls State
  const hasSolution = session.solver_solution && session.solver_solution.length > 0;
  playBtn.disabled = !hasSolution || session.current_step_index >= session.solver_solution.length;
  restartBtn.disabled = !hasSolution && (!session.user_moves || session.user_moves.length === 0);
  prevStepBtn.disabled = !hasSolution || session.current_step_index <= 0;
  nextStepBtn.disabled = !hasSolution || session.current_step_index >= session.solver_solution.length;

  // Move Explanation
  if (hasSolution && session.solver_solution[session.current_step_index]) {
    updateExplanationBox(session.solver_solution[session.current_step_index]);
  } else {
    expMoveBadge.textContent = "—";
    expMoveTitle.textContent = `${session.algorithm.toUpperCase()} Ready`;
    expMoveDir.textContent = "";
    expMoveDesc.textContent = session.status === "solved"
      ? "This algorithm has solved the cube."
      : "Turn cube manually or click 'Solve from Current State'.";
  }

  // Educational Panel
  updateEducationalPanel(null, null, currState);

  // Sync Exploration Viewer to this session
  if (session.exploration_events && session.exploration_events.length > 0) {
    loadExplorationEvents(
      session.exploration_events,
      session.algorithm,
      session.expanded_states || 0,
      session.generated_states || session.expanded_states || 0
    );
  } else {
    resetExplorationViewer(session.algorithm);
  }
}

// ---------------------------------------------------------------------------
// Render the 3 Separate Histories
// ---------------------------------------------------------------------------
function renderScrambleHistory() {
  if (!activeExperiment || !activeExperiment.scramble_moves || activeExperiment.scramble_moves.length === 0) {
    historyScrambleRow.innerHTML = `<span class="history-empty-text">Cube started at Solved state (No scramble)</span>`;
    return;
  }
  historyScrambleRow.innerHTML = activeExperiment.scramble_moves.map(m => `
    <span class="move-tag" style="background:#0369a120; border-color:#0284c7; color:#38bdf8;">${m}</span>
  `).join('');
}

function renderUserActionHistory() {
  const session = getActiveSession();
  if (!session || !session.user_moves || session.user_moves.length === 0) {
    historyUserRow.innerHTML = `<span class="history-empty-text">No manual moves performed on ${session ? session.algorithm.toUpperCase() : ''}</span>`;
    return;
  }
  historyUserRow.innerHTML = session.user_moves.map(m => `
    <span class="move-tag" style="background:#78350f30; border-color:#d97706; color:#fbbf24;">${m}</span>
  `).join('');
}

function renderSolverHistory() {
  const session = getActiveSession();
  if (!session || !session.solver_solution || session.solver_solution.length === 0) {
    solutionBreadcrumbs.innerHTML = `<span class="history-empty-text">Click "Solve from Current State with Python" to compute solution</span>`;
    progressIndicator.textContent = "Move 0 / 0";
    return;
  }

  const moves = session.solver_solution;
  const currentIdx = session.current_step_index || 0;
  progressIndicator.textContent = `Move ${currentIdx} / ${moves.length}`;

  solutionBreadcrumbs.innerHTML = moves.map((m, idx) => {
    let cls = "move-tag";
    if (idx < currentIdx) cls += " completed";
    else if (idx === currentIdx) cls += " current";
    return `<span class="${cls}" id="tag-${idx}">${m}</span>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Update Status Badges on Algorithm Pills
// ---------------------------------------------------------------------------
function updateStatusBadges() {
  if (!activeExperiment || !activeExperiment.sessions) return;

  for (const algo of ["v1", "v2", "v3", "v4", "v5"]) {
    const sess = activeExperiment.sessions[algo];
    const badge = document.getElementById(`status-badge-${algo}`);
    if (badge && sess) {
      badge.className = `algo-status-badge ${sess.status}`;
      if (sess.status === "solved") {
        badge.textContent = "Solved";
      } else if (sess.status === "in_progress") {
        badge.textContent = "In progress";
      } else {
        badge.textContent = "Not started";
      }
    }
  }

  // Active cube status badge
  const activeSess = getActiveSession();
  if (activeSess) {
    const solved = isSolved({ perm: activeSess.current_perm, orient: activeSess.current_orient });
    if (solved) {
      cubeStatusBadge.className = "status-badge solved";
      cubeStatusText.textContent = "Solved";
    } else {
      cubeStatusBadge.className = "status-badge scrambled";
      cubeStatusText.textContent = "Scrambled";
    }
  }
}

// ---------------------------------------------------------------------------
// Algorithm Pill Selection
// ---------------------------------------------------------------------------
document.querySelectorAll('#algo-selector .algo-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    const algo = pill.dataset.algo;
    if (algo === selectedAlgorithm) return;

    document.querySelectorAll('#algo-selector .algo-pill').forEach(p => p.classList.remove('selected'));
    pill.classList.add('selected');
    selectedAlgorithm = algo;

    syncActiveSessionToUI();
  });
});

// ---------------------------------------------------------------------------
// Manual Move Handlers (Applied only to active session)
// ---------------------------------------------------------------------------
async function executeManualMove(moveName) {
  const session = getActiveSession();
  if (!session || cube3d.isAnimating) return;

  stopAutoPlay();

  const stateBefore = {
    perm: [...session.current_perm],
    orient: [...session.current_orient]
  };

  undoStack.push({
    move: moveName,
    stateBefore: JSON.parse(JSON.stringify(stateBefore))
  });
  redoStack.length = 0;
  updateUndoRedoButtons();

  // Physical 3D animation
  const duration = getTurnDuration();
  await cube3d.animateMove(moveName, duration);

  // Compute transition
  const nextState = applyMove(stateBefore, moveName);
  session.current_perm = [...nextState.perm];
  session.current_orient = [...nextState.orient];

  // Record user action
  if (!session.user_moves) session.user_moves = [];
  session.user_moves.push(moveName);
  session.has_manual_interaction = true;

  // Manual move modifies the cube -> invalidate old solver path
  session.solver_solution = [];
  session.current_step_index = 0;
  session.status = isSolved(nextState) ? "solved" : "in_progress";

  // Update backend persistence asynchronously
  persistActiveSession();

  // Update UI
  updateCube2DNet(nextState);
  updateStatusBadges();
  renderUserActionHistory();
  renderSolverHistory();
  updateExplanationBox(moveName);
  updateEducationalPanel(moveName, stateBefore, nextState);

  playBtn.disabled = true;
  restartBtn.disabled = false;
  prevStepBtn.disabled = true;
  nextStepBtn.disabled = true;
}

document.querySelectorAll('[data-move]').forEach(btn => {
  btn.addEventListener('click', () => {
    const move = btn.dataset.move;
    executeManualMove(move);
  });
});

function updateUndoRedoButtons() {
  undoBtn.disabled = undoStack.length === 0;
  redoBtn.disabled = redoStack.length === 0;
}

undoBtn.addEventListener('click', async () => {
  const session = getActiveSession();
  if (!session || undoStack.length === 0 || cube3d.isAnimating) return;

  const lastAction = undoStack.pop();
  redoStack.push({
    move: lastAction.move,
    stateBefore: { perm: [...session.current_perm], orient: [...session.current_orient] }
  });
  updateUndoRedoButtons();

  const invMove = INVERSE_MOVE[lastAction.move];
  await cube3d.animateMove(invMove, getTurnDuration());

  session.current_perm = [...lastAction.stateBefore.perm];
  session.current_orient = [...lastAction.stateBefore.orient];
  session.user_moves.pop();

  persistActiveSession();
  updateCube2DNet(lastAction.stateBefore);
  updateStatusBadges();
  renderUserActionHistory();
  renderSolverHistory();
  updateExplanationBox(invMove);
  updateEducationalPanel(invMove, null, lastAction.stateBefore);
});

redoBtn.addEventListener('click', async () => {
  const session = getActiveSession();
  if (!session || redoStack.length === 0 || cube3d.isAnimating) return;

  const nextAction = redoStack.pop();
  undoStack.push({
    move: nextAction.move,
    stateBefore: { perm: [...session.current_perm], orient: [...session.current_orient] }
  });
  updateUndoRedoButtons();

  await cube3d.animateMove(nextAction.move, getTurnDuration());
  const nextState = applyMove({ perm: session.current_perm, orient: session.current_orient }, nextAction.move);

  session.current_perm = [...nextState.perm];
  session.current_orient = [...nextState.orient];
  session.user_moves.push(nextAction.move);

  persistActiveSession();
  updateCube2DNet(nextState);
  updateStatusBadges();
  renderUserActionHistory();
  renderSolverHistory();
  updateExplanationBox(nextAction.move);
  updateEducationalPanel(nextAction.move, null, nextState);
});

async function persistActiveSession() {
  const session = getActiveSession();
  if (!session || !activeExperiment) return;

  try {
    await updateSessionProgress({
      experiment_id: activeExperiment.id,
      algorithm: session.algorithm,
      current_perm: session.current_perm,
      current_orient: session.current_orient,
      user_moves: session.user_moves || [],
      solver_solution: session.solver_solution || [],
      current_step_index: session.current_step_index || 0,
      status: session.status || "not_started",
      elapsed_ms: session.elapsed_ms || 0.0,
      expanded_states: session.expanded_states || 0,
      solution_length: session.solution_length || 0,
      peak_memory_kb: session.peak_memory_kb || 0.0,
      has_manual_interaction: session.has_manual_interaction || false
    });
  } catch (e) {
    console.warn("Failed to persist session to SQLite:", e);
  }
}

// ---------------------------------------------------------------------------
// Solve from Current State (Requirement 4)
// ---------------------------------------------------------------------------
solveBtn.addEventListener('click', async () => {
  const session = getActiveSession();
  if (!session || cube3d.isAnimating) return;

  const currentState = { perm: session.current_perm, orient: session.current_orient };
  if (isSolved(currentState)) {
    alert("This algorithm's working cube is already solved!");
    session.status = "solved";
    updateStatusBadges();
    return;
  }

  solveBtn.disabled = true;
  solveBtn.textContent = `Python ${session.algorithm.toUpperCase()} Computing...`;

  try {
    const res = await solveFromCurrentState(
      activeExperiment.id,
      session.algorithm,
      session.current_perm,
      session.current_orient,
      session.user_moves || []
    );

    solveBtn.disabled = false;
    solveBtn.textContent = "⚡ Solve from Current State with Python";

    const result = res.result;
    if (result && result.found) {
      session.solver_solution = result.solution;
      session.intermediate_states = res.intermediate_states;
      session.solver_result = result;
      session.current_step_index = 0;
      session.status = "in_progress";
      session.elapsed_ms = result.elapsed_ms;
      session.expanded_states = result.expanded_states;
      session.solution_length = result.solution_length;
      session.peak_memory_kb = result.peak_memory_kb;
      session.exploration_events = res.events || result.events || [];

      // Update metrics
      metricTime.textContent = `${result.elapsed_ms.toFixed(1)} ms`;
      metricExpanded.textContent = result.expanded_states.toLocaleString();
      metricLength.textContent = result.solution_length;
      metricMemory.textContent = `${result.peak_memory_kb.toFixed(1)} KB`;

      renderSolverHistory();
      updateStatusBadges();

      // Load search tree exploration trace
      loadExplorationEvents(
        session.exploration_events,
        session.algorithm,
        result.expanded_states,
        result.generated_states || result.expanded_states
      );

      playBtn.disabled = false;
      restartBtn.disabled = false;
      prevStepBtn.disabled = true;
      nextStepBtn.disabled = session.solver_solution.length === 0;

      if (session.solver_solution.length > 0) {
        updateExplanationBox(session.solver_solution[0]);
      }
    } else {
      session.exploration_events = res.events || (result ? result.events : []) || [];
      if (session.exploration_events.length > 0) {
        loadExplorationEvents(
          session.exploration_events,
          session.algorithm,
          result ? result.expanded_states : 0,
          result ? (result.generated_states || result.expanded_states) : 0
        );
      }
      solutionBreadcrumbs.innerHTML = `<span style="color:#ef4444; font-weight:600;">No solution found or search timed out in Python.</span>`;
    }
  } catch (err) {
    solveBtn.disabled = false;
    solveBtn.textContent = "⚡ Solve from Current State with Python";
    solutionBreadcrumbs.innerHTML = `<span style="color:#ef4444;">Error connecting to Python: ${err.message}</span>`;
  }
});

// ---------------------------------------------------------------------------
// Step-by-Step Playback
// ---------------------------------------------------------------------------
async function stepForward() {
  const session = getActiveSession();
  if (!session || !session.solver_solution || cube3d.isAnimating) return;

  if (session.current_step_index >= session.solver_solution.length) {
    stopAutoPlay();
    return;
  }

  const move = session.solver_solution[session.current_step_index];
  const stateBefore = { perm: [...session.current_perm], orient: [...session.current_orient] };

  // Animate physical turn
  const duration = getTurnDuration();
  await cube3d.animateMove(move, duration);

  // Apply math transition
  const nextState = applyMove(stateBefore, move);
  session.current_perm = [...nextState.perm];
  session.current_orient = [...nextState.orient];
  session.current_step_index++;

  if (session.current_step_index >= session.solver_solution.length && isSolved(nextState)) {
    session.status = "solved";
  }

  persistActiveSession();
  updateCube2DNet(nextState);
  renderSolverHistory();
  updateStatusBadges();
  validateStateWithPython(session.current_step_index);
  updateEducationalPanel(move, stateBefore, nextState);

  prevStepBtn.disabled = false;
  if (session.current_step_index >= session.solver_solution.length) {
    nextStepBtn.disabled = true;
    stopAutoPlay();
    expMoveBadge.textContent = "✔";
    expMoveTitle.textContent = `${session.algorithm.toUpperCase()} Solved!`;
    expMoveDir.textContent = "Target state reached";
    expMoveDesc.textContent = "All 8 corners are in canonical positions with 0 twist.";
  }
}

async function stepBackward() {
  const session = getActiveSession();
  if (!session || !session.solver_solution || cube3d.isAnimating) return;

  if (session.current_step_index <= 0) return;

  session.current_step_index--;
  const move = session.solver_solution[session.current_step_index];
  const invMove = INVERSE_MOVE[move];
  const stateBefore = { perm: [...session.current_perm], orient: [...session.current_orient] };

  await cube3d.animateMove(invMove, getTurnDuration());
  const prevState = applyMove(stateBefore, invMove);
  session.current_perm = [...prevState.perm];
  session.current_orient = [...prevState.orient];
  session.status = "in_progress";

  persistActiveSession();
  updateCube2DNet(prevState);
  renderSolverHistory();
  updateStatusBadges();
  validateStateWithPython(session.current_step_index);
  updateEducationalPanel(invMove, stateBefore, prevState);
  updateExplanationBox(move);

  nextStepBtn.disabled = false;
  if (session.current_step_index === 0) {
    prevStepBtn.disabled = true;
  }
}

async function restartSolution() {
  const session = getActiveSession();
  if (!session || cube3d.isAnimating) return;
  stopAutoPlay();

  // Reset 3D cube and state back to this session's state before the solver started
  const scrambleMoves = activeExperiment.scramble_moves || [];
  const userMoves = session.user_moves || [];
  cube3d.setFromMoveSequence([...scrambleMoves, ...userMoves]);

  // Compute state
  const startState = applyMoves(getSolvedState(), [...scrambleMoves, ...userMoves]);
  session.current_perm = [...startState.perm];
  session.current_orient = [...startState.orient];
  session.current_step_index = 0;
  session.status = "in_progress";

  persistActiveSession();
  updateCube2DNet(startState);
  renderSolverHistory();
  updateStatusBadges();

  prevStepBtn.disabled = true;
  nextStepBtn.disabled = !session.solver_solution || session.solver_solution.length === 0;
  if (session.solver_solution && session.solver_solution.length > 0) {
    updateExplanationBox(session.solver_solution[0]);
  }
}

// Reset Session back to Shared Scramble
resetSessionBtn.addEventListener('click', async () => {
  const session = getActiveSession();
  if (!session || !activeExperiment || cube3d.isAnimating) return;

  if (!confirm(`Reset ${session.algorithm.toUpperCase()} session back to the shared scramble? This clears manual moves on this method.`)) {
    return;
  }

  stopAutoPlay();
  const res = await resetSessionToSharedScramble(activeExperiment.id, session.algorithm);
  activeExperiment.sessions[session.algorithm] = res;
  syncActiveSessionToUI();
});

playBtn.addEventListener('click', async () => {
  const session = getActiveSession();
  if (!session) return;

  if (isPlaying) {
    stopAutoPlay();
    return;
  }

  // If user has modified the cube and no solution exists for current state, solve first!
  if (!session.solver_solution || session.solver_solution.length === 0) {
    await solveBtn.click();
    if (!session.solver_solution || session.solver_solution.length === 0) return;
  }

  startAutoPlay();
});

async function startAutoPlay() {
  const session = getActiveSession();
  if (!session || !session.solver_solution || session.solver_solution.length === 0) return;

  stopExplorationAutoPlay();

  if (session.current_step_index >= session.solver_solution.length) {
    session.current_step_index = 0;
    await restartSolution();
  }

  isPlaying = true;
  playBtn.textContent = "⏸ Pause";
  playBtn.classList.remove('btn-primary');
  playBtn.classList.add('btn-danger');

  while (isPlaying && session.current_step_index < session.solver_solution.length) {
    await stepForward();
    if (!isPlaying) break;
    if (session.current_step_index >= session.solver_solution.length) break;

    const pauseMs = getInterMovePause();
    await new Promise(resolve => {
      playLoopTimer = setTimeout(resolve, pauseMs);
    });
    playLoopTimer = null;
  }

  stopAutoPlay();
}

function stopAutoPlay() {
  isPlaying = false;
  if (playLoopTimer) {
    clearTimeout(playLoopTimer);
    playLoopTimer = null;
  }
  playBtn.textContent = "▶ Play";
  playBtn.classList.remove('btn-danger');
  playBtn.classList.add('btn-primary');
}

nextStepBtn.addEventListener('click', () => {
  stopAutoPlay();
  stepForward();
});

prevStepBtn.addEventListener('click', () => {
  stopAutoPlay();
  stepBackward();
});

restartBtn.addEventListener('click', () => {
  restartSolution();
});

// ---------------------------------------------------------------------------
// Search Space Exploration & Trace Viewer Logic (Expanded States Inspector)
// ---------------------------------------------------------------------------
let currentExplorationEvents = [];
let currentExplorationIndex = 0;
let isExplorationPlaying = false;
let explorationTimer = null;

function snapCubeBackToSolutionStep() {
  const session = getActiveSession();
  if (!session || !activeExperiment) return;
  const scrambleMoves = activeExperiment.scramble_moves || [];
  const userMoves = session.user_moves || [];
  const solverSolution = session.solver_solution || [];
  const executedSolverMoves = solverSolution.slice(0, session.current_step_index || 0);
  const totalMoves = [...scrambleMoves, ...userMoves, ...executedSolverMoves];
  cube3d.setFromMoveSequence(totalMoves);
  const currState = { perm: session.current_perm, orient: session.current_orient };
  updateCube2DNet(currState);
}

function resetExplorationViewer(algoName = "V4") {
  stopExplorationAutoPlay();
  currentExplorationEvents = [];
  currentExplorationIndex = 0;
  treeData = null;
  v4FwdTreeData = null;
  v4BwdTreeData = null;

  const isV4 = (algoName || "").toLowerCase() === "v4";
  isV4Mode = isV4;

  if (isV4) {
    if (searchTreeSvg) searchTreeSvg.style.display = "none";
    if (v4DualTreeViewport) v4DualTreeViewport.style.display = "flex";
    if (v4LayoutToggleGroup) v4LayoutToggleGroup.style.display = "inline-flex";
    if (v4BridgePanel) v4BridgePanel.style.display = "none";
    if (v4ConnFwdLinks) v4ConnFwdLinks.innerHTML = "";
    if (v4ConnBridgeLayer) v4ConnBridgeLayer.innerHTML = "";
    if (v4ConnBwdLinks) v4ConnBwdLinks.innerHTML = "";
    if (v4ConnFwdNodes) v4ConnFwdNodes.innerHTML = "";
    if (v4ConnBwdNodes) v4ConnBwdNodes.innerHTML = "";
    if (v4FwdLinksLayer) v4FwdLinksLayer.innerHTML = "";
    if (v4FwdNodesLayer) v4FwdNodesLayer.innerHTML = "";
    if (v4BwdLinksLayer) v4BwdLinksLayer.innerHTML = "";
    if (v4BwdNodesLayer) v4BwdNodesLayer.innerHTML = "";
  } else {
    if (v4DualTreeViewport) v4DualTreeViewport.style.display = "none";
    if (v4LayoutToggleGroup) v4LayoutToggleGroup.style.display = "none";
    if (v4BridgePanel) v4BridgePanel.style.display = "none";
    if (searchTreeSvg) searchTreeSvg.style.display = "block";
    renderSearchTreeSVG();
  }

  if (treePathDisplay) treePathDisplay.innerHTML = `<span style="color:#38bdf8;">Root (Initial State)</span>`;
  if (exploreAlgoTitle) exploreAlgoTitle.textContent = (algoName || "V4").toUpperCase();
  if (exploreMetaExpanded) exploreMetaExpanded.textContent = "0";
  if (exploreMetaGenerated) exploreMetaGenerated.textContent = "0";
  if (exploreMetaEvents) exploreMetaEvents.textContent = "0";
  if (exploreSlider) {
    exploreSlider.min = 0;
    exploreSlider.max = 0;
    exploreSlider.value = 0;
  }
  if (exploreStepCounter) exploreStepCounter.textContent = "0 / 0";
  if (exploreEventTypeBadge) {
    exploreEventTypeBadge.className = "event-type-pill expand";
    exploreEventTypeBadge.textContent = "EXPAND";
  }
  if (exploreEventDepth) exploreEventDepth.textContent = "Depth: 0";
  if (exploreEventMove) exploreEventMove.textContent = "—";
  if (exploreEventTitle) exploreEventTitle.textContent = "Search State Evaluation";
  if (exploreEventExplanation) exploreEventExplanation.textContent = "Click 'Solve from Current State with Python' to capture the search tree exploration trace.";
  if (exploreEventExpanded) exploreEventExpanded.textContent = "0";
  if (exploreEventGenerated) exploreEventGenerated.textContent = "0";
  if (exploreEventTime) exploreEventTime.textContent = "0.0 ms";
  if (exploreTableBody) {
    exploreTableBody.innerHTML = `
      <tr>
        <td colspan="6" style="padding:24px; text-align:center; color:var(--text-muted); font-style:italic;">
          Click "⚡ Solve from Current State with Python" to stream the state-space search trace.
        </td>
      </tr>
    `;
  }
}

function loadExplorationEvents(events, algoName, expandedCount, generatedCount) {
  stopExplorationAutoPlay();
  currentExplorationEvents = events || [];
  currentExplorationIndex = 0;

  const isV4 = (algoName || "v4").toLowerCase() === "v4";
  isV4Mode = isV4;

  if (exploreAlgoTitle) exploreAlgoTitle.textContent = (algoName || "V4").toUpperCase();
  if (exploreMetaExpanded) exploreMetaExpanded.textContent = (expandedCount || 0).toLocaleString();
  if (exploreMetaGenerated) exploreMetaGenerated.textContent = (generatedCount || expandedCount || 0).toLocaleString();
  if (exploreMetaEvents) exploreMetaEvents.textContent = currentExplorationEvents.length.toLocaleString();

  if (!currentExplorationEvents || currentExplorationEvents.length === 0) {
    resetExplorationViewer(algoName);
    return;
  }

  const session = getActiveSession();
  const solMoves = session ? (session.solver_solution || []) : [];

  if (isV4) {
    if (searchTreeSvg) searchTreeSvg.style.display = "none";
    if (v4DualTreeViewport) v4DualTreeViewport.style.display = "flex";
    if (v4LayoutToggleGroup) v4LayoutToggleGroup.style.display = "inline-flex";

    // Set initial layout container display based on v4LayoutMode
    if (v4LayoutMode === "connected") {
      if (v4ConnectedContainer) v4ConnectedContainer.style.display = "block";
      if (v4SplitContainer) v4SplitContainer.style.display = "none";
    } else {
      if (v4ConnectedContainer) v4ConnectedContainer.style.display = "none";
      if (v4SplitContainer) v4SplitContainer.style.display = "flex";
    }

    let fwdSolPath = null;
    let bwdSolPath = null;

    const resExtra = (session && session.solver_result && session.solver_result.extra) || {};
    if (Array.isArray(resExtra.fwd_path) && Array.isArray(resExtra.bwd_search_path)) {
      fwdSolPath = resExtra.fwd_path;
      bwdSolPath = resExtra.bwd_search_path;
    }

    if (!fwdSolPath || !bwdSolPath) {
      for (const e of currentExplorationEvents) {
        if (e.type === "goal" || e.type === "intersection") {
          if (Array.isArray(e.fwd_path)) fwdSolPath = e.fwd_path;
          if (Array.isArray(e.bwd_search_path)) bwdSolPath = e.bwd_search_path;
        }
      }
    }

    if (!fwdSolPath || !bwdSolPath) {
      const half = Math.floor(solMoves.length / 2);
      fwdSolPath = solMoves.slice(0, half);
      bwdSolPath = solMoves.slice(half).map(m => INVERSE_MOVE[m] || m).reverse();
    }

    const fwdEvents = currentExplorationEvents.filter(e => (e.direction || 'forward') !== 'backward');
    const bwdEvents = currentExplorationEvents.filter(e => e.direction === 'backward');

    const fwdRoot = buildSearchTree(fwdEvents, fwdSolPath || [], "forward");
    v4FwdTreeData = fwdRoot;
    v4FwdNodesByKey = fwdRoot ? fwdRoot.nodesByKey : new Map();

    const bwdRoot = buildSearchTree(bwdEvents, bwdSolPath || [], "backward");
    v4BwdTreeData = bwdRoot;
    v4BwdNodesByKey = bwdRoot ? bwdRoot.nodesByKey : new Map();

    renderV4DualTrees();
    updateV4Bridge(fwdSolPath || [], bwdSolPath || [], solMoves, resExtra);
  } else {
    if (v4DualTreeViewport) v4DualTreeViewport.style.display = "none";
    if (v4BridgePanel) v4BridgePanel.style.display = "none";
    if (v4LayoutToggleGroup) v4LayoutToggleGroup.style.display = "none";
    if (searchTreeSvg) searchTreeSvg.style.display = "block";

    const root = buildSearchTree(currentExplorationEvents, solMoves, "forward");
    treeData = root;
    treeNodesByKey = root ? root.nodesByKey : new Map();
    allTreeNodesList = root ? root.allNodes : [];
    renderSearchTreeSVG();
  }

  if (exploreSlider) {
    exploreSlider.min = 0;
    exploreSlider.max = currentExplorationEvents.length - 1;
    exploreSlider.value = 0;
  }

  // Populate Table rows
  if (exploreTableBody) {
    const rowsHtml = currentExplorationEvents.map((evt, idx) => {
      const typeStr = (evt.type || 'expand').toLowerCase();
      const typeLabel = typeStr === 'recursion_limit' ? 'REC_LIMIT' : typeStr.toUpperCase();
      const moveStr = evt.move || '—';
      const depthStr = evt.depth ?? 0;
      const elapsedStr = (evt.elapsed_ms || 0).toFixed(1) + ' ms';
      const safeDesc = escapeHtml(evt.explanation || '');
      return `
        <tr data-idx="${idx}" class="${idx === 0 ? 'selected' : ''}">
          <td style="color:var(--text-muted);">${idx + 1}</td>
          <td><span class="event-type-pill ${typeStr}">${typeLabel}</span></td>
          <td style="color:#94a3b8;">${depthStr}</td>
          <td style="font-weight:bold; color:var(--accent);">${moveStr}</td>
          <td style="color:#e2e8f0; max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${safeDesc}">${safeDesc}</td>
          <td style="text-align:right; color:#38bdf8;">${elapsedStr}</td>
        </tr>
      `;
    }).join('');
    exploreTableBody.innerHTML = rowsHtml;

    // Attach click events to rows
    exploreTableBody.querySelectorAll('tr').forEach(tr => {
      tr.addEventListener('click', () => {
        stopExplorationAutoPlay();
        const idx = parseInt(tr.dataset.idx, 10);
        if (!isNaN(idx)) {
          renderExplorationEvent(idx);
        }
      });
    });
  }

  renderExplorationEvent(0);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderExplorationEvent(index) {
  if (!currentExplorationEvents || currentExplorationEvents.length === 0) return;

  index = Math.max(0, Math.min(index, currentExplorationEvents.length - 1));
  currentExplorationIndex = index;

  if (exploreSlider) exploreSlider.value = index;
  if (exploreStepCounter) exploreStepCounter.textContent = `${index + 1} / ${currentExplorationEvents.length}`;

  const evt = currentExplorationEvents[index];
  const typeStr = (evt.type || 'expand').toLowerCase();

  if (exploreEventTypeBadge) {
    exploreEventTypeBadge.className = `event-type-pill ${typeStr}`;
    exploreEventTypeBadge.textContent = typeStr === 'recursion_limit' ? 'REC_LIMIT' : typeStr.toUpperCase();
  }

  if (exploreEventDepth) exploreEventDepth.textContent = `Depth: ${evt.depth ?? 0}`;
  if (exploreEventMove) exploreEventMove.textContent = evt.move || '—';

  const typeTitles = {
    start:          "Search Initialized",
    expand:         "Search Node Dequeued & Expanded",
    attempt:        "Move Attempted",
    discover:       "New State Discovered",
    duplicate:      "Duplicate State — Already Visited",
    enqueue:        "State Added to FIFO Queue",
    generate:       "Child State Generated",
    visit:          "New State Discovered",
    prune:          "Pruned by Move Symmetry / Heuristic",
    skip:           "Duplicate Visited State Skipped",
    backtrack:      "Backtracking to Parent Stack Frame",
    recursion_limit:"Python Call Stack Limit Reached",
    threshold:      "IDA* Threshold Increased",
    goal:           "Goal Target State Found!",
    complete:       "Search Complete",
  };
  if (exploreEventTitle) exploreEventTitle.textContent = typeTitles[typeStr] || "Search Event";
  if (exploreEventExplanation) exploreEventExplanation.textContent = evt.explanation || "Evaluating state...";
  // Support both old (generated) and new (attempts) field names
  if (exploreEventExpanded) exploreEventExpanded.textContent = (evt.expanded ?? index).toLocaleString();
  if (exploreEventGenerated) exploreEventGenerated.textContent = (
    evt.attempts ?? evt.generated ?? index
  ).toLocaleString();
  if (exploreEventTime) exploreEventTime.textContent = `${(evt.elapsed_ms || 0).toFixed(1)} ms`;

  // Highlight table row and scroll into view
  if (exploreTableBody) {
    const prevSelected = exploreTableBody.querySelector('tr.selected');
    if (prevSelected) prevSelected.classList.remove('selected');
    const currRow = exploreTableBody.querySelector(`tr[data-idx="${index}"]`);
    if (currRow) {
      currRow.classList.add('selected');
      currRow.scrollIntoView({ block: 'nearest' });
    }
  }

  // Highlight active path & node in Search Tree
  highlightTreeNodeForEvent(evt);

  // 3D Cube Preview
  if (exploreSync3D && exploreSync3D.checked) {
    const isBwd = evt.direction === 'backward';
    if (isBwd && isV4Mode) {
      const pathMoves = evt.path || [];
      cube3d.setFromMoveSequence(pathMoves);
      const st = applyMoves(getSolvedState(), pathMoves);
      updateCube2DNet(st);
    } else {
      const session = getActiveSession();
      if (session && activeExperiment) {
        const scrambleMoves = activeExperiment.scramble_moves || [];
        const userMoves = session.user_moves || [];
        const pathMoves = evt.path || [];
        const fullSequence = [...scrambleMoves, ...userMoves, ...pathMoves];
        cube3d.setFromMoveSequence(fullSequence);
        const st = applyMoves(getSolvedState(), fullSequence);
        updateCube2DNet(st);
      }
    }
  }
}

function getExplorationDelay() {
  const speedVal = exploreSpeedSelect ? parseFloat(exploreSpeedSelect.value) : 5;
  switch (speedVal) {
    case 1: return 400;
    case 2: return 200;
    case 5: return 80;
    case 10: return 35;
    case 20: return 15;
    default: return 80;
  }
}

function startExplorationAutoPlay() {
  if (!currentExplorationEvents || currentExplorationEvents.length === 0) return;
  stopAutoPlay(); // Stop solution autoplay if active

  if (currentExplorationIndex >= currentExplorationEvents.length - 1) {
    currentExplorationIndex = 0;
    renderExplorationEvent(0);
  }

  isExplorationPlaying = true;
  if (explorePlayBtn) {
    explorePlayBtn.textContent = "⏸ Pause Trace";
    explorePlayBtn.classList.remove('btn-primary');
    explorePlayBtn.classList.add('btn-danger');
  }

  runExplorationStep();
}

function runExplorationStep() {
  if (!isExplorationPlaying) return;

  if (currentExplorationIndex < currentExplorationEvents.length - 1) {
    renderExplorationEvent(currentExplorationIndex + 1);
    const delay = getExplorationDelay();
    explorationTimer = setTimeout(runExplorationStep, delay);
  } else {
    stopExplorationAutoPlay();
  }
}

function stopExplorationAutoPlay() {
  isExplorationPlaying = false;
  if (explorationTimer) {
    clearTimeout(explorationTimer);
    explorationTimer = null;
  }
  if (explorePlayBtn) {
    explorePlayBtn.textContent = "▶ Play Search Trace";
    explorePlayBtn.classList.remove('btn-danger');
    explorePlayBtn.classList.add('btn-primary');
  }
}

// Exploration Controls Event Listeners
if (exploreFirstBtn) {
  exploreFirstBtn.addEventListener('click', () => {
    stopExplorationAutoPlay();
    renderExplorationEvent(0);
  });
}

if (explorePrevBtn) {
  explorePrevBtn.addEventListener('click', () => {
    stopExplorationAutoPlay();
    renderExplorationEvent(currentExplorationIndex - 1);
  });
}

if (exploreNextBtn) {
  exploreNextBtn.addEventListener('click', () => {
    stopExplorationAutoPlay();
    renderExplorationEvent(currentExplorationIndex + 1);
  });
}

if (exploreLastBtn) {
  exploreLastBtn.addEventListener('click', () => {
    stopExplorationAutoPlay();
    if (currentExplorationEvents.length > 0) {
      renderExplorationEvent(currentExplorationEvents.length - 1);
    }
  });
}

if (explorePlayBtn) {
  explorePlayBtn.addEventListener('click', () => {
    if (isExplorationPlaying) {
      stopExplorationAutoPlay();
    } else {
      startExplorationAutoPlay();
    }
  });
}

if (exploreSlider) {
  exploreSlider.addEventListener('input', (e) => {
    stopExplorationAutoPlay();
    const idx = parseInt(e.target.value, 10);
    if (!isNaN(idx)) {
      renderExplorationEvent(idx);
    }
  });
}

if (exploreReturnCubeBtn) {
  exploreReturnCubeBtn.addEventListener('click', () => {
    stopExplorationAutoPlay();
    snapCubeBackToSolutionStep();
  });
}

if (exploreSync3D) {
  exploreSync3D.addEventListener('change', () => {
    if (exploreSync3D.checked) {
      renderExplorationEvent(currentExplorationIndex);
    } else {
      snapCubeBackToSolutionStep();
    }
  });
}

// ---------------------------------------------------------------------------
// Interactive Search Tree Visualization Engine (Hierarchical State-Space Tree)
// ---------------------------------------------------------------------------
let treeData = null;
let allTreeNodesList = [];
let treeNodesByKey = new Map(); // module-level: keyed by null-byte path key
let treeFilterMode = "all"; // "all" | "solution"
let treePan = { x: 0, y: 0 };
let treeScale = 1.0;
let isTreePanning = false;
let treePanStart = { x: 0, y: 0 };

function buildSearchTree(events, solution = [], direction = "forward") {
  if (!events || events.length === 0) return null;

  // ── Build a unique node key ──────────────────────────────────────────────
  // We key nodes by their PATH (move sequence from root) rather than by cube
  // state so that the tree faithfully mirrors the event log's expansion order.
  const makeKey = (path) => path.join('\x00'); // null-byte separator avoids clash

  const isBwd = direction === "backward";
  const root = {
    id: isBwd ? "GOAL_ROOT" : "ROOT",
    pathKey: makeKey([]),
    path: [],
    move: isBwd ? "Goal" : "Start",
    depth: 0,
    parent: null,
    children: [],            // ordered exactly as events were emitted
    childKeys: new Set(),    // for dedup without duplicating children list
    status: isBwd ? "bwd_root" : "start",
    explanation: isBwd ? "Solved state — backward search begins here" : "Initial scrambled state — search begins here",
    isSolution: true,
    isGoal: solution.length === 0,
    isMeeting: solution.length === 0,
    firstEventIdx: 0,
    lastEventIdx: 0,
    eventIndices: [],
    expanded: false,
  };

  const nodesByKey = new Map();
  nodesByKey.set(root.pathKey, root);

  // Pre-compute solution path keys for fast lookup
  const solPathKeys = new Set();
  let acc2 = [];
  solPathKeys.add(makeKey([]));
  for (const m of solution) {
    acc2.push(m);
    solPathKeys.add(makeKey(acc2));
  }
  const solLeafKey = makeKey(solution);

  // ── Helpers ──────────────────────────────────────────────────────────────
  function getOrCreateNode(parentNode, move, path, eventIdx) {
    const key = makeKey(path);
    let node = nodesByKey.get(key);
    if (!node) {
      const isSol = solPathKeys.has(key);
      const isLeaf = key === solLeafKey;
      node = {
        id: key || (isBwd ? "GOAL_ROOT" : "ROOT"),
        pathKey: key,
        path: [...path],
        move,
        depth: path.length,
        parent: parentNode,
        children: [],
        childKeys: new Set(),
        status: "visit",
        explanation: "",
        isSolution: isSol,
        isGoal: isLeaf,
        isMeeting: isLeaf,
        firstEventIdx: eventIdx,
        lastEventIdx: eventIdx,
        eventIndices: [],
        expanded: false,
      };
      if (!parentNode.childKeys.has(key)) {
        parentNode.children.push(node);
        parentNode.childKeys.add(key);
      }
      nodesByKey.set(key, node);
    }
    return node;
  }

  // Walk path array to get (or create) the node at that path, ensuring all ancestors exist.
  function walkToPath(path, eventIdx) {
    if (path.length === 0) return root;
    let curr = root;
    for (let d = 0; d < path.length; d++) {
      const childPath = path.slice(0, d + 1);
      curr = getOrCreateNode(curr, path[d], childPath, eventIdx);
    }
    return curr;
  }

  // Guarantee that all nodes along the solution path exist in the tree
  if (solution.length > 0) {
    walkToPath(solution, 0);
  }

  // ── Process events in order ──────────────────────────────────────────────
  let currentExpandNode = root;

  events.forEach((evt, evtIdx) => {
    const ePath = evt.path || [];
    const eType = evt.type || "";
    const eMove = evt.move || "";
    const eExpl = evt.explanation || "";

    // ── Meta events that anchor to root ─────────────────────────────────────
    if (eType === "start" || eType === "frontier" || eType === "frontier_complete" || eType === "iteration" || eType === "complete") {
      root.eventIndices.push(evtIdx);
      return;
    }

    // ── expand ───────────────────────────────────────────────────────────────
    if (eType === "expand") {
      const node = walkToPath(ePath, evtIdx);
      node.status = "expand";
      node.expanded = true;
      node.eventIndices.push(evtIdx);
      if (eExpl) node.explanation = eExpl;
      currentExpandNode = node;
      return;
    }

    // ── attempt ──────────────────────────────────────────────────────────────
    if (eType === "attempt") {
      const childPath = eMove && currentExpandNode
        ? [...currentExpandNode.path, eMove]
        : (ePath.length > 0 ? ePath : null);
      if (!childPath) { root.eventIndices.push(evtIdx); return; }
      const parentNode = currentExpandNode || root;
      const childNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      if (childNode.status === "visit") childNode.status = "attempt";
      childNode.eventIndices.push(evtIdx);
      if (eExpl && childNode.status === "attempt") childNode.explanation = eExpl;
      return;
    }

    // ── discover ─────────────────────────────────────────────────────────────
    if (eType === "discover") {
      let childPath, parentNode;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
        parentNode = currentExpandNode;
      } else {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      }
      const childNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      childNode.status = "discover";
      childNode.eventIndices.push(evtIdx);
      if (eExpl) childNode.explanation = eExpl;
      return;
    }

    // ── duplicate ────────────────────────────────────────────────────────────
    if (eType === "duplicate") {
      let childPath;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
      } else {
        return;
      }
      const parentNode = childPath.length > 1
        ? walkToPath(childPath.slice(0, -1), evtIdx)
        : root;
      const dupNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      if (dupNode.status === "visit" || dupNode.status === "attempt") {
        dupNode.status = "duplicate";
      }
      dupNode.eventIndices.push(evtIdx);
      if (eExpl) dupNode.explanation = eExpl;
      return;
    }

    // ── intersection ─────────────────────────────────────────────────────────
    if (eType === "intersection") {
      let childPath;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
      } else {
        childPath = ePath;
      }
      const parentNode = childPath.length > 1
        ? walkToPath(childPath.slice(0, -1), evtIdx)
        : root;
      const interNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      interNode.status = "intersection";
      interNode.isMeeting = true;
      interNode.eventIndices.push(evtIdx);
      if (eExpl) interNode.explanation = eExpl;
      return;
    }

    // ── enqueue ───────────────────────────────────────────────────────────────
    if (eType === "enqueue") {
      let childPath;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
      } else {
        return;
      }
      const parentNode = childPath.length > 1
        ? walkToPath(childPath.slice(0, -1), evtIdx)
        : root;
      const enqNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      enqNode.eventIndices.push(evtIdx);
      return;
    }

    // ── visit / generate ─────────────────────────────────────────────────────
    if (eType === "visit" || eType === "generate") {
      let childPath, parentNode;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
        parentNode = currentExpandNode;
      } else {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      }
      const childNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      childNode.status = eType;
      childNode.eventIndices.push(evtIdx);
      if (eExpl) childNode.explanation = eExpl;
      return;
    }

    // ── skip ─────────────────────────────────────────────────────────────────
    if (eType === "skip") {
      let childPath;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
      } else {
        return;
      }
      const parentNode = childPath.length > 1
        ? walkToPath(childPath.slice(0, -1), evtIdx)
        : root;
      const skipNode = getOrCreateNode(parentNode, eMove, childPath, evtIdx);
      if (skipNode.status === "visit" || skipNode.status === "generate" ||
          skipNode.status === "attempt" || skipNode.status === "discover") {
        skipNode.status = "skip";
      }
      skipNode.eventIndices.push(evtIdx);
      if (eExpl) skipNode.explanation = eExpl;
      return;
    }

    // ── prune ────────────────────────────────────────────────────────────────
    if (eType === "prune") {
      let childPath, parentNode;
      if (ePath.length > 0 && eMove && ePath[ePath.length - 1] === eMove) {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      } else if (eMove && currentExpandNode) {
        childPath = [...currentExpandNode.path, eMove];
        parentNode = currentExpandNode;
      } else {
        childPath = ePath;
        parentNode = walkToPath(ePath.slice(0, -1), evtIdx);
      }
      const pruneNode = getOrCreateNode(parentNode, eMove || "?", childPath, evtIdx);
      pruneNode.status = "prune";
      pruneNode.eventIndices.push(evtIdx);
      if (eExpl) pruneNode.explanation = eExpl;
      return;
    }

    // ── backtrack ────────────────────────────────────────────────────────────
    if (eType === "backtrack") {
      const node = walkToPath(ePath, evtIdx);
      node.status = "backtrack";
      node.eventIndices.push(evtIdx);
      if (eExpl) node.explanation = eExpl;
      if (node.parent) {
        currentExpandNode = node.parent;
      }
      return;
    }

    // ── goal ─────────────────────────────────────────────────────────────────
    if (eType === "goal") {
      const node = walkToPath(ePath, evtIdx);
      node.status = "goal";
      node.isGoal = true;
      node.isMeeting = true;
      node.isSolution = true;
      node.eventIndices.push(evtIdx);
      if (eExpl) node.explanation = eExpl;
      return;
    }

    // Catch-all
    if (ePath.length > 0) {
      const node = walkToPath(ePath, evtIdx);
      node.eventIndices.push(evtIdx);
    }
  });

  // Stamp solution path
  for (const key of solPathKeys) {
    const n = nodesByKey.get(key);
    if (n) n.isSolution = true;
  }
  if (solution.length > 0) {
    const goalNode = nodesByKey.get(solLeafKey);
    if (goalNode) {
      goalNode.isGoal = true;
      goalNode.isMeeting = true;
      goalNode.isSolution = true;
      if (goalNode.status !== "goal") goalNode.status = "goal";
    }
  }

  root.nodesByKey = nodesByKey;
  root.allNodes = Array.from(nodesByKey.values());
  return root;
}

function computeTreeLayout(root, filterMode = "all") {
  if (!root) return { width: 0, height: 0, minX: 0, maxX: 0 };

  function getVisibleChildren(node) {
    if (filterMode === "solution") {
      return node.children.filter(c => c.isSolution || c.isGoal || c.isMeeting);
    }
    return node.children;
  }

  const levelGapY = 95;
  const nodeGapX = 62;
  let nextLeafX = 50;
  const levelMaxX = [];

  function positionNode(node, depth) {
    node.depth = depth;
    node.y = depth * levelGapY + 50;

    const visibleKids = getVisibleChildren(node);
    node.visibleChildren = visibleKids;

    if (visibleKids.length === 0) {
      let proposedX = nextLeafX;
      if (levelMaxX[depth] !== undefined && proposedX < levelMaxX[depth] + nodeGapX) {
        proposedX = levelMaxX[depth] + nodeGapX;
      }
      node.x = proposedX;
      levelMaxX[depth] = node.x;
      nextLeafX = node.x + nodeGapX;
    } else {
      visibleKids.forEach(kid => positionNode(kid, depth + 1));
      const firstChildX = visibleKids[0].x;
      const lastChildX = visibleKids[visibleKids.length - 1].x;

      let proposedX = (firstChildX + lastChildX) / 2;
      if (levelMaxX[depth] !== undefined && proposedX < levelMaxX[depth] + nodeGapX) {
        const shift = (levelMaxX[depth] + nodeGapX) - proposedX;
        shiftSubtree(node, shift);
        proposedX = (visibleKids[0].x + visibleKids[visibleKids.length - 1].x) / 2;
      }
      node.x = proposedX;
      levelMaxX[depth] = node.x;
      nextLeafX = Math.max(nextLeafX, node.x + nodeGapX);
    }
  }

  function shiftSubtree(n, shiftAmount) {
    n.x += shiftAmount;
    if (levelMaxX[n.depth] === undefined || n.x > levelMaxX[n.depth]) {
      levelMaxX[n.depth] = n.x;
    }
    if (n.visibleChildren) {
      n.visibleChildren.forEach(kid => shiftSubtree(kid, shiftAmount));
    }
  }

  positionNode(root, 0);

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  function findBounds(n) {
    minX = Math.min(minX, n.x);
    maxX = Math.max(maxX, n.x);
    minY = Math.min(minY, n.y);
    maxY = Math.max(maxY, n.y);
    if (n.visibleChildren) n.visibleChildren.forEach(findBounds);
  }
  findBounds(root);

  return {
    minX, maxX, minY, maxY,
    width:  Math.max(400, maxX - minX + 160),
    height: Math.max(300, maxY - minY + 160)
  };
}

function renderTreeToLayers(root, linksLayer, nodesLayer, isBackward = false) {
  if (!root) {
    if (linksLayer) linksLayer.innerHTML = "";
    if (nodesLayer) nodesLayer.innerHTML = "";
    return { width: 0, height: 0, minX: 0, maxX: 0 };
  }

  const bounds = computeTreeLayout(root, treeFilterMode);
  let linksHtml = "";
  let nodesHtml = "";
  const encKey = k => k.replace(/\x00/g, '_');

  function traverseRender(node) {
    const kids = node.visibleChildren || [];
    for (const kid of kids) {
      const isSolEdge = node.isSolution && kid.isSolution;
      const kidStatus  = kid.status || "discover";
      const isPruned   = kidStatus === "prune";
      const isSkip     = kidStatus === "skip";
      const isDuplicate = kidStatus === "duplicate";
      const isAttempt  = kidStatus === "attempt";
      let edgeClass = "tree-link";
      if (isBackward) edgeClass += " bwd-edge";
      if (isSolEdge) edgeClass += " solution";
      else if (isPruned) edgeClass += " pruned";
      else if (isSkip || isDuplicate) edgeClass += " skip-edge";
      else if (isAttempt) edgeClass += " attempt-edge";

      const x1 = node.x, y1 = node.y;
      const x2 = kid.x,  y2 = kid.y;
      const midY = (y1 + y2) / 2;
      const pathD = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;

      const moveLabel = kid.move || "";
      const labelX = (x1 + x2) / 2;
      const labelY = midY - 8;
      linksHtml += `<path d="${pathD}" class="${edgeClass}" data-parent="${encKey(node.pathKey)}" data-child="${encKey(kid.pathKey)}" />`;
      linksHtml += `<text x="${labelX}" y="${labelY}" class="tree-link-label${isSolEdge ? ' solution' : ''}">${moveLabel}</text>`;

      traverseRender(kid);
    }

    // Node visual
    const st = node.status || "discover";
    let nodeClasses = ["tree-node", st];
    if (node.isSolution && st !== "prune" && st !== "duplicate") nodeClasses.push("solution");
    if (node.isMeeting || node.isGoal) {
      nodeClasses.push("goal");
      nodeClasses.push("meeting-node");
    }
    if (node.path.length === 0) {
      nodeClasses.push("start");
      if (isBackward) nodeClasses.push("bwd-root");
    }

    const isMeetingNode = node.isMeeting || node.isGoal;
    const isSolNode = node.isSolution && !isMeetingNode;
    const isMinor = st === "attempt" || st === "duplicate";
    const r = isMeetingNode ? 22 : (isSolNode ? 18 : (st === "expand" ? 17 : (isMinor ? 10 : 14)));

    let label;
    if (isMeetingNode) label = "★";
    else if (node.path.length === 0) label = isBackward ? "G" : "S";
    else label = node.move || "";
    if (label.length > 3) label = label.slice(0, 3);

    const orderNum = node.expanded ? (node.eventIndices.length > 0 ? node.eventIndices[0] + 1 : "") : "";

    nodesHtml += `
      <g class="${nodeClasses.join(' ')}" data-path="${encKey(node.pathKey)}" data-dir="${isBackward ? 'backward' : 'forward'}" transform="translate(${node.x}, ${node.y})" title="${escapeHtml(node.explanation)}">
        <circle r="${r}" />
        <text y="1">${label}</text>
        ${orderNum ? `<text y="${r + 10}" class="node-depth-badge">#${orderNum}</text>` : ""}
      </g>`;
  }

  traverseRender(root);

  if (linksLayer) linksLayer.innerHTML = linksHtml;
  if (nodesLayer) {
    nodesLayer.innerHTML = nodesHtml;
    nodesLayer.querySelectorAll('.tree-node').forEach(g => {
      g.addEventListener('click', e => {
        e.stopPropagation();
        if (isV4Mode) {
          selectDirectionalTreeNode(g.dataset.path, g.dataset.dir === 'backward');
        } else {
          selectTreeNodeByEncodedKey(g.dataset.path);
        }
      });
    });
  }

  return bounds;
}

function renderSearchTreeSVG() {
  if (!treeData) {
    if (treeEmptyNotice) treeEmptyNotice.style.display = "flex";
    if (treeLinksLayer) treeLinksLayer.innerHTML = "";
    if (treeNodesLayer) treeNodesLayer.innerHTML = "";
    return;
  }
  if (treeEmptyNotice) treeEmptyNotice.style.display = "none";

  const bounds = renderTreeToLayers(treeData, treeLinksLayer, treeNodesLayer, false);
  fitSearchTreeToView(bounds);
}

function updateV4ConnTransform() {
  if (v4ConnectedPanLayer) {
    v4ConnectedPanLayer.setAttribute("transform", `translate(${v4ConnPan.x}, ${v4ConnPan.y}) scale(${v4ConnScale})`);
  }
}

function fitV4ConnectedTreeToView(bounds) {
  if (!v4ConnectedContainer) return;
  const vw = v4ConnectedContainer.clientWidth || 800;
  const vh = v4ConnectedContainer.clientHeight || 550;
  if (!bounds) {
    bounds = renderV4ConnectedTree();
  }
  const tw = bounds.width || 500;
  const th = bounds.height || 400;
  const scaleX = (vw - 80) / tw;
  const scaleY = (vh - 80) / th;
  v4ConnScale = Math.min(1.1, Math.max(0.18, Math.min(scaleX, scaleY)));
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  v4ConnPan.x = (vw / 2) - (centerX * v4ConnScale);
  v4ConnPan.y = (vh / 2) - (centerY * v4ConnScale);
  updateV4ConnTransform();
}

function renderV4ConnectedTree() {
  if (!v4FwdTreeData && !v4BwdTreeData) {
    if (v4ConnFwdLinks) v4ConnFwdLinks.innerHTML = "";
    if (v4ConnBwdLinks) v4ConnBwdLinks.innerHTML = "";
    if (v4ConnFwdNodes) v4ConnFwdNodes.innerHTML = "";
    if (v4ConnBwdNodes) v4ConnBwdNodes.innerHTML = "";
    if (v4ConnBridgeLayer) v4ConnBridgeLayer.innerHTML = "";
    return { width: 400, height: 300, minX: 0, maxX: 400, minY: 0, maxY: 300 };
  }

  const fwdBounds = v4FwdTreeData
    ? computeTreeLayout(v4FwdTreeData, treeFilterMode)
    : { minX: 100, maxX: 300, minY: 50, maxY: 150, width: 200, height: 100 };

  const bwdBounds = v4BwdTreeData
    ? computeTreeLayout(v4BwdTreeData, treeFilterMode)
    : { minX: 100, maxX: 300, minY: 50, maxY: 150, width: 200, height: 100 };

  // Calculate max depth in Tree B
  let maxDepthB = 0;
  function findMaxDepthB(n) {
    if (n.depth > maxDepthB) maxDepthB = n.depth;
    if (n.visibleChildren) n.visibleChildren.forEach(findMaxDepthB);
  }
  if (v4BwdTreeData) findMaxDepthB(v4BwdTreeData);
  if (maxDepthB === 0) maxDepthB = 1;

  // Inverted vertical positioning:
  // Forward tree: y = 50 + depth * 95
  // Bridge gap between deepest forward level and inverted backward leaves
  const bridgeGap = 140;
  const yBridgeTop = fwdBounds.maxY + bridgeGap;

  // Find meeting node in Tree A & Tree B for horizontal alignment and bridge connection
  let meetingA = null;
  function scanMeetingA(n) {
    if (n.isMeeting || n.isGoal) meetingA = n;
    if (n.visibleChildren) n.visibleChildren.forEach(scanMeetingA);
  }
  if (v4FwdTreeData) scanMeetingA(v4FwdTreeData);

  let meetingB = null;
  function scanMeetingB(n) {
    if (n.isMeeting || n.isGoal) meetingB = n;
    if (n.visibleChildren) n.visibleChildren.forEach(scanMeetingB);
  }
  if (v4BwdTreeData) scanMeetingB(v4BwdTreeData);

  let deltaX = 0;
  if (meetingA && meetingB) {
    deltaX = meetingA.x - meetingB.x;
  } else {
    const centerA = (fwdBounds.minX + fwdBounds.maxX) / 2;
    const centerB = (bwdBounds.minX + bwdBounds.maxX) / 2;
    deltaX = centerA - centerB;
  }

  // Render Forward Tree into v4ConnFwdLinks and v4ConnFwdNodes
  if (v4FwdTreeData) {
    renderTreeToLayers(v4FwdTreeData, v4ConnFwdLinks, v4ConnFwdNodes, false);
  } else {
    if (v4ConnFwdLinks) v4ConnFwdLinks.innerHTML = "";
    if (v4ConnFwdNodes) v4ConnFwdNodes.innerHTML = "";
  }

  // Render Inverted Backward Tree
  const encKey = k => k.replace(/\x00/g, '_');
  let bwdLinksHtml = "";
  let bwdNodesHtml = "";

  function traverseInvertedBwd(node) {
    // Inverted coordinates
    node.invX = node.x + deltaX;
    node.invY = yBridgeTop + (maxDepthB - node.depth) * 95;

    const kids = node.visibleChildren || [];
    for (const kid of kids) {
      kid.invX = kid.x + deltaX;
      kid.invY = yBridgeTop + (maxDepthB - kid.depth) * 95;

      const isSolEdge = node.isSolution && kid.isSolution;
      const kidStatus = kid.status || "discover";
      const isPruned = kidStatus === "prune";
      const isSkip = kidStatus === "skip";
      const isDuplicate = kidStatus === "duplicate";
      const isAttempt = kidStatus === "attempt";
      let edgeClass = "tree-link bwd-edge";
      if (isSolEdge) edgeClass += " solution";
      else if (isPruned) edgeClass += " pruned";
      else if (isSkip || isDuplicate) edgeClass += " skip-edge";
      else if (isAttempt) edgeClass += " attempt-edge";

      const x1 = node.invX, y1 = node.invY;
      const x2 = kid.invX,  y2 = kid.invY;
      const midY = (y1 + y2) / 2;
      const pathD = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;

      const moveLabel = kid.move || "";
      const labelX = (x1 + x2) / 2;
      const labelY = midY - 8;
      bwdLinksHtml += `<path d="${pathD}" class="${edgeClass}" data-parent="${encKey(node.pathKey)}" data-child="${encKey(kid.pathKey)}" />`;
      bwdLinksHtml += `<text x="${labelX}" y="${labelY}" class="tree-link-label bwd-link-label${isSolEdge ? ' solution' : ''}">${moveLabel}</text>`;

      traverseInvertedBwd(kid);
    }

    const st = node.status || "discover";
    let nodeClasses = ["tree-node", st];
    if (node.isSolution && st !== "prune" && st !== "duplicate") nodeClasses.push("solution");
    if (node.isMeeting || node.isGoal) {
      nodeClasses.push("goal");
      nodeClasses.push("meeting-node");
    }
    if (node.path.length === 0) {
      nodeClasses.push("start");
      nodeClasses.push("bwd-root");
    }

    const isMeetingNode = node.isMeeting || node.isGoal;
    const isSolNode = node.isSolution && !isMeetingNode;
    const isMinor = st === "attempt" || st === "duplicate";
    const r = isMeetingNode ? 22 : (isSolNode ? 18 : (st === "expand" ? 17 : (isMinor ? 10 : 14)));

    let label;
    if (isMeetingNode) label = "★";
    else if (node.path.length === 0) label = "G";
    else label = node.move || "";
    if (label.length > 3) label = label.slice(0, 3);

    const orderNum = node.expanded ? (node.eventIndices.length > 0 ? node.eventIndices[0] + 1 : "") : "";

    bwdNodesHtml += `
      <g class="${nodeClasses.join(' ')}" data-path="${encKey(node.pathKey)}" data-dir="backward" transform="translate(${node.invX}, ${node.invY})" title="${escapeHtml(node.explanation)}">
        <circle r="${r}" />
        <text y="1">${label}</text>
        ${orderNum ? `<text y="${r + 10}" class="node-depth-badge">#${orderNum}</text>` : ""}
      </g>`;
  }

  if (v4BwdTreeData) {
    traverseInvertedBwd(v4BwdTreeData);
  }

  if (v4ConnBwdLinks) v4ConnBwdLinks.innerHTML = bwdLinksHtml;
  if (v4ConnBwdNodes) {
    v4ConnBwdNodes.innerHTML = bwdNodesHtml;
    v4ConnBwdNodes.querySelectorAll('.tree-node').forEach(g => {
      g.addEventListener('click', e => {
        e.stopPropagation();
        selectDirectionalTreeNode(g.dataset.path, true);
      });
    });
  }

  // Draw Central Golden Bridge Connection Edge
  if (v4ConnBridgeLayer) {
    if (meetingA && meetingB) {
      const ax = meetingA.x, ay = meetingA.y;
      const bx = meetingB.invX, by = meetingB.invY;
      const midY = (ay + by) / 2;
      const bridgePath = `M ${ax} ${ay} C ${ax} ${midY}, ${bx} ${midY}, ${bx} ${by}`;
      v4ConnBridgeLayer.innerHTML = `
        <path d="${bridgePath}" class="v4-bridge-connection-edge" />
        <g transform="translate(${(ax + bx) / 2}, ${midY})">
          <rect x="-95" y="-14" width="190" height="28" rx="14" fill="#0f172a" stroke="#f59e0b" stroke-width="2" filter="drop-shadow(0 0 8px rgba(245,158,11,0.5))" />
          <text x="0" y="4" text-anchor="middle" fill="#fbbf24" font-size="11" font-weight="700" letter-spacing="0.5">🎯 MEETING INTERSECTION</text>
        </g>
      `;
    } else {
      v4ConnBridgeLayer.innerHTML = "";
    }
  }

  const minX = Math.min(fwdBounds.minX, bwdBounds.minX + deltaX);
  const maxX = Math.max(fwdBounds.maxX, bwdBounds.maxX + deltaX);
  const minY = fwdBounds.minY;
  const maxY = yBridgeTop + maxDepthB * 95 + 60;
  return {
    minX, maxX, minY, maxY,
    width: Math.max(500, maxX - minX + 160),
    height: Math.max(400, maxY - minY + 160)
  };
}

function renderV4DualTrees() {
  if (!v4FwdTreeData && !v4BwdTreeData) {
    if (treeEmptyNotice) treeEmptyNotice.style.display = "flex";
    if (v4FwdLinksLayer) v4FwdLinksLayer.innerHTML = "";
    if (v4FwdNodesLayer) v4FwdNodesLayer.innerHTML = "";
    if (v4BwdLinksLayer) v4BwdLinksLayer.innerHTML = "";
    if (v4BwdNodesLayer) v4BwdNodesLayer.innerHTML = "";
    if (v4ConnFwdLinks) v4ConnFwdLinks.innerHTML = "";
    if (v4ConnBwdLinks) v4ConnBwdLinks.innerHTML = "";
    if (v4ConnFwdNodes) v4ConnFwdNodes.innerHTML = "";
    if (v4ConnBwdNodes) v4ConnBwdNodes.innerHTML = "";
    if (v4ConnBridgeLayer) v4ConnBridgeLayer.innerHTML = "";
    return;
  }
  if (treeEmptyNotice) treeEmptyNotice.style.display = "none";

  // Always render connected tree
  const connBounds = renderV4ConnectedTree();

  // Always render split side-by-side trees
  if (v4FwdTreeData) {
    renderTreeToLayers(v4FwdTreeData, v4FwdLinksLayer, v4FwdNodesLayer, false);
  }
  if (v4BwdTreeData) {
    renderTreeToLayers(v4BwdTreeData, v4BwdLinksLayer, v4BwdNodesLayer, true);
  }

  // Set container visibility according to current v4LayoutMode
  if (v4LayoutMode === "connected") {
    if (v4ConnectedContainer) v4ConnectedContainer.style.display = "block";
    if (v4SplitContainer) v4SplitContainer.style.display = "none";
    if (v4ViewConnectedBtn) {
      v4ViewConnectedBtn.classList.add('active', 'btn-primary');
      v4ViewConnectedBtn.classList.remove('btn-secondary');
    }
    if (v4ViewSplitBtn) {
      v4ViewSplitBtn.classList.remove('active', 'btn-primary');
      v4ViewSplitBtn.classList.add('btn-secondary');
    }
    fitV4ConnectedTreeToView(connBounds);
  } else {
    if (v4ConnectedContainer) v4ConnectedContainer.style.display = "none";
    if (v4SplitContainer) v4SplitContainer.style.display = "flex";
    if (v4ViewSplitBtn) {
      v4ViewSplitBtn.classList.add('active', 'btn-primary');
      v4ViewSplitBtn.classList.remove('btn-secondary');
    }
    if (v4ViewConnectedBtn) {
      v4ViewConnectedBtn.classList.remove('active', 'btn-primary');
      v4ViewConnectedBtn.classList.add('btn-secondary');
    }
    fitV4TreesToView();
  }
}

function updateTreeTransform() {
  if (treePanLayer) {
    treePanLayer.setAttribute("transform", `translate(${treePan.x}, ${treePan.y}) scale(${treeScale})`);
  }
}

function updateV4FwdTransform() {
  if (v4FwdPanLayer) {
    v4FwdPanLayer.setAttribute("transform", `translate(${v4FwdPan.x}, ${v4FwdPan.y}) scale(${v4FwdScale})`);
  }
}

function updateV4BwdTransform() {
  if (v4BwdPanLayer) {
    v4BwdPanLayer.setAttribute("transform", `translate(${v4BwdPan.x}, ${v4BwdPan.y}) scale(${v4BwdScale})`);
  }
}

function fitSearchTreeToView(bounds) {
  if (!treeViewport || !treeData) return;
  const vw = treeViewport.clientWidth || 800;
  const vh = treeViewport.clientHeight || 480;

  if (!bounds) {
    bounds = computeTreeLayout(treeData, treeFilterMode);
  }

  const tw = bounds.width || 400;
  const th = bounds.height || 300;

  const scaleX = (vw - 80) / tw;
  const scaleY = (vh - 80) / th;
  treeScale = Math.min(1.2, Math.max(0.2, Math.min(scaleX, scaleY)));

  const centerX = (bounds.minX + bounds.maxX) / 2;
  treePan.x = (vw / 2) - (centerX * treeScale);
  treePan.y = 35;

  updateTreeTransform();
}

function fitV4TreesToView() {
  if (v4FwdTreeData && v4FwdContainer) {
    const fwdBounds = computeTreeLayout(v4FwdTreeData, treeFilterMode);
    const vw = v4FwdContainer.clientWidth || 400;
    const vh = v4FwdContainer.clientHeight || 450;
    const tw = fwdBounds.width || 400;
    const th = fwdBounds.height || 300;
    const scaleX = (vw - 60) / tw;
    const scaleY = (vh - 60) / th;
    v4FwdScale = Math.min(1.2, Math.max(0.2, Math.min(scaleX, scaleY)));
    const centerX = (fwdBounds.minX + fwdBounds.maxX) / 2;
    v4FwdPan.x = (vw / 2) - (centerX * v4FwdScale);
    v4FwdPan.y = 35;
    updateV4FwdTransform();
  }

  if (v4BwdTreeData && v4BwdContainer) {
    const bwdBounds = computeTreeLayout(v4BwdTreeData, treeFilterMode);
    const vw = v4BwdContainer.clientWidth || 400;
    const vh = v4BwdContainer.clientHeight || 450;
    const tw = bwdBounds.width || 400;
    const th = bwdBounds.height || 300;
    const scaleX = (vw - 60) / tw;
    const scaleY = (vh - 60) / th;
    v4BwdScale = Math.min(1.2, Math.max(0.2, Math.min(scaleX, scaleY)));
    const centerX = (bwdBounds.minX + bwdBounds.maxX) / 2;
    v4BwdPan.x = (vw / 2) - (centerX * v4BwdScale);
    v4BwdPan.y = 35;
    updateV4BwdTransform();
  }
}

function updateV4Bridge(fwdPath = [], bwdPath = [], solution = [], extra = {}) {
  if (!v4BridgePanel) return;
  v4BridgePanel.style.display = 'block';

  if (v4FwdPathText) {
    v4FwdPathText.innerHTML = fwdPath.length > 0
      ? fwdPath.map(m => `<span style="background:#0284c725; color:#38bdf8; padding:1px 6px; border-radius:4px; border:1px solid #0284c7;">${m}</span>`).join(' <span style="color:#64748b;">➔</span> ')
      : '<span style="color:var(--text-muted); font-style:italic;">(Start is meeting state)</span>';
  }

  if (v4BwdPathText) {
    v4BwdPathText.innerHTML = bwdPath.length > 0
      ? bwdPath.map(m => `<span style="background:#05966925; color:#34d399; padding:1px 6px; border-radius:4px; border:1px solid #10b981;">${m}</span>`).join(' <span style="color:#64748b;">➔</span> ')
      : '<span style="color:var(--text-muted); font-style:italic;">(Goal is meeting state)</span>';
  }

  if (v4SolPathText) {
    v4SolPathText.innerHTML = solution.length > 0
      ? solution.map(m => `<span style="background:#f59e0b25; color:#fbbf24; padding:1px 6px; border-radius:4px; border:1px solid #f59e0b; font-weight:700;">${m}</span>`).join(' <span style="color:#fbbf24;">➔</span> ')
      : '<span style="color:#10b981; font-weight:700;">Solved (0 moves)</span>';
  }

  if (v4MeetingExplanation) {
    const fwdLen = fwdPath.length;
    const bwdLen = bwdPath.length;
    const totalLen = solution.length;
    const invBwd = bwdPath.map(m => INVERSE_MOVE[m] || m).reverse();
    v4MeetingExplanation.innerHTML = `
      <strong>Optimal Meeting Point:</strong> Forward depth <code>${fwdLen}</code> + Backward depth <code>${bwdLen}</code> = <code>${totalLen}</code> moves.<br>
      Backward search path from goal <code>[${bwdPath.join(', ')}]</code> is inverted to <code>[${invBwd.join(', ')}]</code> and appended to forward path to produce the complete shortest solution.
    `;
  }
}

function highlightTreeNodeForEvent(evt) {
  if (isV4Mode) {
    highlightV4TreeNodeForEvent(evt);
    return;
  }

  if (!treeData || !treeNodesLayer) return;

  const encKey = k => k.replace(/\x00/g, '_');
  const rawPath = evt.path || [];
  const key = rawPath.join('\x00');
  const eKey = encKey(key);

  treeNodesLayer.querySelectorAll('.active-focus').forEach(el => el.classList.remove('active-focus'));
  if (treeLinksLayer) {
    treeLinksLayer.querySelectorAll('.active-path').forEach(el => el.classList.remove('active-path'));
  }

  const nodeEl = treeNodesLayer.querySelector(`.tree-node[data-path="${eKey}"]`);
  if (nodeEl) {
    nodeEl.classList.add('active-focus');
    nodeEl.scrollIntoViewIfNeeded && nodeEl.scrollIntoViewIfNeeded(false);
  }

  if (treeLinksLayer && rawPath.length > 0) {
    for (let i = 0; i < rawPath.length; i++) {
      const parentK = encKey(rawPath.slice(0, i).join('\x00'));
      const childK = encKey(rawPath.slice(0, i + 1).join('\x00'));
      const linkEl = treeLinksLayer.querySelector(`path[data-parent="${parentK}"][data-child="${childK}"]`);
      if (linkEl) {
        linkEl.classList.add('active-path');
      }
    }
  }

  if (treePathDisplay) {
    if (rawPath.length === 0) {
      treePathDisplay.innerHTML = `<span style="color:#38bdf8;">Root (Initial State)</span>`;
    } else {
      const pathHtml = rawPath.map(m => `<span style="background:#0284c725; color:#38bdf8; padding:1px 6px; border-radius:4px; border:1px solid #0284c7;">${m}</span>`).join(' <span style="color:#64748b;">➔</span> ');
      treePathDisplay.innerHTML = `<span style="color:#94a3b8;">Root</span> <span style="color:#64748b;">➔</span> ${pathHtml} <span style="color:var(--text-muted); font-size:0.75rem;">(Depth ${rawPath.length})</span>`;
    }
  }
}

function highlightV4TreeNodeForEvent(evt) {
  const encKey = k => k.replace(/\x00/g, '_');
  const rawPath = evt.path || [];
  const key = rawPath.join('\x00');
  const eKey = encKey(key);
  const isBwd = evt.direction === 'backward';

  // Clear focus in both split layers and connected layers
  if (v4FwdNodesLayer) v4FwdNodesLayer.querySelectorAll('.active-focus').forEach(el => el.classList.remove('active-focus'));
  if (v4BwdNodesLayer) v4BwdNodesLayer.querySelectorAll('.active-focus').forEach(el => el.classList.remove('active-focus'));
  if (v4FwdLinksLayer) v4FwdLinksLayer.querySelectorAll('.active-path').forEach(el => el.classList.remove('active-path'));
  if (v4BwdLinksLayer) v4BwdLinksLayer.querySelectorAll('.active-path').forEach(el => el.classList.remove('active-path'));
  if (v4ConnFwdNodes) v4ConnFwdNodes.querySelectorAll('.active-focus').forEach(el => el.classList.remove('active-focus'));
  if (v4ConnBwdNodes) v4ConnBwdNodes.querySelectorAll('.active-focus').forEach(el => el.classList.remove('active-focus'));
  if (v4ConnFwdLinks) v4ConnFwdLinks.querySelectorAll('.active-path').forEach(el => el.classList.remove('active-path'));
  if (v4ConnBwdLinks) v4ConnBwdLinks.querySelectorAll('.active-path').forEach(el => el.classList.remove('active-path'));

  const targetNodesLayer = isBwd ? v4BwdNodesLayer : v4FwdNodesLayer;
  const targetLinksLayer = isBwd ? v4BwdLinksLayer : v4FwdLinksLayer;
  const targetConnNodesLayer = isBwd ? v4ConnBwdNodes : v4ConnFwdNodes;
  const targetConnLinksLayer = isBwd ? v4ConnBwdLinks : v4ConnFwdLinks;

  if (targetNodesLayer) {
    const nodeEl = targetNodesLayer.querySelector(`.tree-node[data-path="${eKey}"]`);
    if (nodeEl) nodeEl.classList.add('active-focus');
  }
  if (targetConnNodesLayer) {
    const nodeEl = targetConnNodesLayer.querySelector(`.tree-node[data-path="${eKey}"]`);
    if (nodeEl) nodeEl.classList.add('active-focus');
  }

  if (rawPath.length > 0) {
    for (let i = 0; i < rawPath.length; i++) {
      const parentK = encKey(rawPath.slice(0, i).join('\x00'));
      const childK = encKey(rawPath.slice(0, i + 1).join('\x00'));
      if (targetLinksLayer) {
        const linkEl = targetLinksLayer.querySelector(`path[data-parent="${parentK}"][data-child="${childK}"]`);
        if (linkEl) linkEl.classList.add('active-path');
      }
      if (targetConnLinksLayer) {
        const linkEl = targetConnLinksLayer.querySelector(`path[data-parent="${parentK}"][data-child="${childK}"]`);
        if (linkEl) linkEl.classList.add('active-path');
      }
    }
  }

  if (evt.type === 'goal' || evt.type === 'intersection') {
    if (v4BridgePanel) v4BridgePanel.style.display = 'block';
    [v4FwdNodesLayer, v4BwdNodesLayer, v4ConnFwdNodes, v4ConnBwdNodes].forEach(layer => {
      if (layer) {
        const mn = layer.querySelector('.tree-node.meeting-node');
        if (mn) mn.classList.add('active-focus');
      }
    });
  }

  if (treePathDisplay) {
    const dirTag = isBwd
      ? `<span style="background:#05966930; color:#34d399; padding:2px 8px; border-radius:4px; font-weight:700; border:1px solid #10b981;">Tree B (Backward)</span>`
      : `<span style="background:#0284c730; color:#38bdf8; padding:2px 8px; border-radius:4px; font-weight:700; border:1px solid #0284c7;">Tree A (Forward)</span>`;
    const rootName = isBwd ? "Goal (Solved)" : "Root (Start)";
    if (rawPath.length === 0) {
      treePathDisplay.innerHTML = `${dirTag} <span style="color:#94a3b8; margin-left:8px;">${rootName}</span>`;
    } else {
      const pathHtml = rawPath.map(m => `<span style="background:rgba(255,255,255,0.06); color:${isBwd ? '#34d399' : '#38bdf8'}; padding:1px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.15);">${m}</span>`).join(' <span style="color:#64748b;">➔</span> ');
      treePathDisplay.innerHTML = `${dirTag} <span style="color:#94a3b8; margin-left:8px;">${rootName}</span> <span style="color:#64748b;">➔</span> ${pathHtml} <span style="color:var(--text-muted); font-size:0.75rem;">(Depth ${rawPath.length})</span>`;
    }
  }
}

function selectDirectionalTreeNode(encodedKey, isBackward) {
  const nodesByKey = isBackward ? v4BwdNodesByKey : v4FwdNodesByKey;
  if (!nodesByKey) return;
  const rawKey = encodedKey.replace(/_/g, '\x00');
  const curr = nodesByKey.get(rawKey);
  if (!curr) return;

  const pathMoves = curr.path || [];
  highlightTreeNodeForEvent({ path: pathMoves, direction: isBackward ? 'backward' : 'forward' });

  const typeStr = (curr.status || 'expand').toLowerCase();
  if (exploreEventTypeBadge) {
    exploreEventTypeBadge.className = `event-type-pill ${typeStr}`;
    exploreEventTypeBadge.textContent = typeStr === 'recursion_limit' ? 'REC_LIMIT' : typeStr.toUpperCase();
  }
  if (exploreEventDepth) exploreEventDepth.textContent = `Depth: ${curr.depth}`;
  if (exploreEventMove) exploreEventMove.textContent = curr.move || (isBackward ? 'Goal' : 'Root');
  if (exploreEventTitle) {
    exploreEventTitle.textContent = (curr.isMeeting || curr.isGoal)
      ? "🎯 Intersection Meeting State!"
      : (curr.isSolution ? (isBackward ? "⭐ Backward Path to Meeting" : "⭐ Forward Path to Meeting") : (isBackward ? "Tree B Exploration" : "Tree A Exploration"));
  }
  if (exploreEventExplanation) {
    exploreEventExplanation.textContent = curr.explanation || `Branch reached via path: [${pathMoves.join(', ')}]`;
  }

  const eventIndices = curr.eventIndices || [];
  if (exploreEventExpanded) {
    exploreEventExpanded.textContent = `${eventIndices.length > 0 ? eventIndices[0] + 1 : '—'}`;
  }

  if (eventIndices.length > 0) {
    const evtIdx = eventIndices[0];
    currentExplorationIndex = evtIdx;
    if (exploreSlider) exploreSlider.value = evtIdx;
    if (exploreStepCounter) exploreStepCounter.textContent = `${evtIdx + 1} / ${currentExplorationEvents.length}`;
    if (exploreTableBody) {
      const prevSelected = exploreTableBody.querySelector('tr.selected');
      if (prevSelected) prevSelected.classList.remove('selected');
      const currRow = exploreTableBody.querySelector(`tr[data-idx="${evtIdx}"]`);
      if (currRow) {
        currRow.classList.add('selected');
        currRow.scrollIntoView({ block: 'nearest' });
      }
    }
  }

  if (exploreSync3D && exploreSync3D.checked) {
    if (isBackward) {
      cube3d.setFromMoveSequence(pathMoves);
      const st = applyMoves(getSolvedState(), pathMoves);
      updateCube2DNet(st);
    } else {
      const session = getActiveSession();
      if (session && activeExperiment) {
        const scrambleMoves = activeExperiment.scramble_moves || [];
        const userMoves = session.user_moves || [];
        const fullSequence = [...scrambleMoves, ...userMoves, ...pathMoves];
        cube3d.setFromMoveSequence(fullSequence);
        const st = applyMoves(getSolvedState(), fullSequence);
        updateCube2DNet(st);
      }
    }
  }
}

function selectTreeNodeByEncodedKey(encodedKey) {
  if (!treeData || !treeNodesByKey) return;

  // Decode: encoded uses '_' where null-bytes were. Move names never contain '_'.
  const rawKey = encodedKey.replace(/_/g, '\x00');
  const curr = treeNodesByKey.get(rawKey);
  if (!curr) return;

  const pathMoves = curr.path || [];
  highlightTreeNodeForEvent({ path: pathMoves });

  const typeStr = (curr.status || 'expand').toLowerCase();
  if (exploreEventTypeBadge) {
    exploreEventTypeBadge.className = `event-type-pill ${typeStr}`;
    exploreEventTypeBadge.textContent = typeStr === 'recursion_limit' ? 'REC_LIMIT' : typeStr.toUpperCase();
  }
  if (exploreEventDepth) exploreEventDepth.textContent = `Depth: ${curr.depth}`;
  if (exploreEventMove) exploreEventMove.textContent = curr.move || 'Root';
  if (exploreEventTitle) {
    exploreEventTitle.textContent = curr.isGoal
      ? "🎯 Target Goal Reached!"
      : (curr.isSolution ? "⭐ Chosen Solution Path Step" : "Search Branch Exploration");
  }
  if (exploreEventExplanation) {
    exploreEventExplanation.textContent = curr.explanation || `Branch reached via path: [${pathMoves.join(', ')}]`;
  }

  const eventIndices = curr.eventIndices || [];
  if (exploreEventExpanded) {
    exploreEventExpanded.textContent = `${eventIndices.length > 0 ? eventIndices[0] + 1 : '—'}`;
  }

  if (eventIndices.length > 0) {
    const evtIdx = eventIndices[0];
    currentExplorationIndex = evtIdx;
    if (exploreSlider) exploreSlider.value = evtIdx;
    if (exploreStepCounter) exploreStepCounter.textContent = `${evtIdx + 1} / ${currentExplorationEvents.length}`;
    if (exploreTableBody) {
      const prevSelected = exploreTableBody.querySelector('tr.selected');
      if (prevSelected) prevSelected.classList.remove('selected');
      const currRow = exploreTableBody.querySelector(`tr[data-idx="${evtIdx}"]`);
      if (currRow) {
        currRow.classList.add('selected');
        currRow.scrollIntoView({ block: 'nearest' });
      }
    }
  }

  if (exploreSync3D && exploreSync3D.checked) {
    const session = getActiveSession();
    if (session && activeExperiment) {
      const scrambleMoves = activeExperiment.scramble_moves || [];
      const userMoves = session.user_moves || [];
      const fullSequence = [...scrambleMoves, ...userMoves, ...pathMoves];
      cube3d.setFromMoveSequence(fullSequence);
      const st = applyMoves(getSolvedState(), fullSequence);
      updateCube2DNet(st);
    }
  }
}

// Tree Pan & Zoom Event Listeners (Single-tree viewport)
if (treeViewport && searchTreeSvg) {
  treeViewport.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isTreePanning = true;
    treePanStart.x = e.clientX - treePan.x;
    treePanStart.y = e.clientY - treePan.y;
    searchTreeSvg.style.cursor = 'grabbing';
  });

  window.addEventListener('mousemove', (e) => {
    if (!isTreePanning) return;
    treePan.x = e.clientX - treePanStart.x;
    treePan.y = e.clientY - treePanStart.y;
    updateTreeTransform();
  });

  window.addEventListener('mouseup', () => {
    if (isTreePanning) {
      isTreePanning = false;
      if (searchTreeSvg) searchTreeSvg.style.cursor = 'grab';
    }
  });

  treeViewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const rect = treeViewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const newScale = Math.min(2.5, Math.max(0.15, treeScale * zoomFactor));
    treePan.x = mouseX - (mouseX - treePan.x) * (newScale / treeScale);
    treePan.y = mouseY - (mouseY - treePan.y) * (newScale / treeScale);
    treeScale = newScale;
    updateTreeTransform();
  }, { passive: false });
}

// V4 Connected Inverted Tree Pan & Zoom Listeners
if (v4ConnectedContainer && v4ConnectedTreeSvg) {
  v4ConnectedContainer.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isV4ConnPanning = true;
    v4ConnPanStart.x = e.clientX - v4ConnPan.x;
    v4ConnPanStart.y = e.clientY - v4ConnPan.y;
    v4ConnectedTreeSvg.style.cursor = 'grabbing';
  });

  v4ConnectedContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const rect = v4ConnectedContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const newScale = Math.min(2.5, Math.max(0.15, v4ConnScale * zoomFactor));
    v4ConnPan.x = mouseX - (mouseX - v4ConnPan.x) * (newScale / v4ConnScale);
    v4ConnPan.y = mouseY - (mouseY - v4ConnPan.y) * (newScale / v4ConnScale);
    v4ConnScale = newScale;
    updateV4ConnTransform();
  }, { passive: false });
}

// V4 Dual-Tree Independent Pan & Zoom Listeners
if (v4FwdContainer && v4FwdTreeSvg) {
  v4FwdContainer.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isV4FwdPanning = true;
    v4FwdPanStart.x = e.clientX - v4FwdPan.x;
    v4FwdPanStart.y = e.clientY - v4FwdPan.y;
    v4FwdTreeSvg.style.cursor = 'grabbing';
  });

  v4FwdContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const rect = v4FwdContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const newScale = Math.min(2.5, Math.max(0.15, v4FwdScale * zoomFactor));
    v4FwdPan.x = mouseX - (mouseX - v4FwdPan.x) * (newScale / v4FwdScale);
    v4FwdPan.y = mouseY - (mouseY - v4FwdPan.y) * (newScale / v4FwdScale);
    v4FwdScale = newScale;
    updateV4FwdTransform();
  }, { passive: false });
}

if (v4BwdContainer && v4BwdTreeSvg) {
  v4BwdContainer.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isV4BwdPanning = true;
    v4BwdPanStart.x = e.clientX - v4BwdPan.x;
    v4BwdPanStart.y = e.clientY - v4BwdPan.y;
    v4BwdTreeSvg.style.cursor = 'grabbing';
  });

  v4BwdContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const rect = v4BwdContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const newScale = Math.min(2.5, Math.max(0.15, v4BwdScale * zoomFactor));
    v4BwdPan.x = mouseX - (mouseX - v4BwdPan.x) * (newScale / v4BwdScale);
    v4BwdPan.y = mouseY - (mouseY - v4BwdPan.y) * (newScale / v4BwdScale);
    v4BwdScale = newScale;
    updateV4BwdTransform();
  }, { passive: false });
}

window.addEventListener('mousemove', (e) => {
  if (isV4ConnPanning) {
    v4ConnPan.x = e.clientX - v4ConnPanStart.x;
    v4ConnPan.y = e.clientY - v4ConnPanStart.y;
    updateV4ConnTransform();
  }
  if (isV4FwdPanning) {
    v4FwdPan.x = e.clientX - v4FwdPanStart.x;
    v4FwdPan.y = e.clientY - v4FwdPanStart.y;
    updateV4FwdTransform();
  }
  if (isV4BwdPanning) {
    v4BwdPan.x = e.clientX - v4BwdPanStart.x;
    v4BwdPan.y = e.clientY - v4BwdPanStart.y;
    updateV4BwdTransform();
  }
});

window.addEventListener('mouseup', () => {
  if (isV4ConnPanning) {
    isV4ConnPanning = false;
    if (v4ConnectedTreeSvg) v4ConnectedTreeSvg.style.cursor = 'grab';
  }
  if (isV4FwdPanning) {
    isV4FwdPanning = false;
    if (v4FwdTreeSvg) v4FwdTreeSvg.style.cursor = 'grab';
  }
  if (isV4BwdPanning) {
    isV4BwdPanning = false;
    if (v4BwdTreeSvg) v4BwdTreeSvg.style.cursor = 'grab';
  }
});

// V4 Layout Mode Toggle Listeners (Connected Inverted vs Split Side-by-Side)
if (v4ViewConnectedBtn && v4ViewSplitBtn) {
  v4ViewConnectedBtn.addEventListener('click', () => {
    v4LayoutMode = "connected";
    if (v4ConnectedContainer) v4ConnectedContainer.style.display = "block";
    if (v4SplitContainer) v4SplitContainer.style.display = "none";
    v4ViewConnectedBtn.classList.add('active', 'btn-primary');
    v4ViewConnectedBtn.classList.remove('btn-secondary');
    v4ViewSplitBtn.classList.remove('active', 'btn-primary');
    v4ViewSplitBtn.classList.add('btn-secondary');
    fitV4ConnectedTreeToView();
  });

  v4ViewSplitBtn.addEventListener('click', () => {
    v4LayoutMode = "split";
    if (v4ConnectedContainer) v4ConnectedContainer.style.display = "none";
    if (v4SplitContainer) v4SplitContainer.style.display = "flex";
    v4ViewSplitBtn.classList.add('active', 'btn-primary');
    v4ViewSplitBtn.classList.remove('btn-secondary');
    v4ViewConnectedBtn.classList.remove('active', 'btn-primary');
    v4ViewConnectedBtn.classList.add('btn-secondary');
    fitV4TreesToView();
  });
}

// Zoom Buttons
if (treeZoomInBtn) {
  treeZoomInBtn.addEventListener('click', () => {
    if (isV4Mode) {
      if (v4LayoutMode === 'connected') {
        v4ConnScale = Math.min(2.5, v4ConnScale * 1.25);
        updateV4ConnTransform();
      } else {
        v4FwdScale = Math.min(2.5, v4FwdScale * 1.25);
        v4BwdScale = Math.min(2.5, v4BwdScale * 1.25);
        updateV4FwdTransform();
        updateV4BwdTransform();
      }
    } else {
      treeScale = Math.min(2.5, treeScale * 1.25);
      updateTreeTransform();
    }
  });
}

if (treeZoomOutBtn) {
  treeZoomOutBtn.addEventListener('click', () => {
    if (isV4Mode) {
      if (v4LayoutMode === 'connected') {
        v4ConnScale = Math.max(0.15, v4ConnScale * 0.8);
        updateV4ConnTransform();
      } else {
        v4FwdScale = Math.max(0.15, v4FwdScale * 0.8);
        v4BwdScale = Math.max(0.15, v4BwdScale * 0.8);
        updateV4FwdTransform();
        updateV4BwdTransform();
      }
    } else {
      treeScale = Math.max(0.15, treeScale * 0.8);
      updateTreeTransform();
    }
  });
}

if (treeZoomFitBtn) {
  treeZoomFitBtn.addEventListener('click', () => {
    if (isV4Mode) {
      if (v4LayoutMode === 'connected') {
        fitV4ConnectedTreeToView();
      } else {
        fitV4TreesToView();
      }
    } else {
      fitSearchTreeToView();
    }
  });
}

// Tree Filtering Controls
if (treeFilterAllBtn && treeFilterSolBtn) {
  treeFilterAllBtn.addEventListener('click', () => {
    treeFilterMode = "all";
    treeFilterAllBtn.classList.add('active', 'btn-primary');
    treeFilterAllBtn.classList.remove('btn-secondary');
    treeFilterSolBtn.classList.remove('active', 'btn-primary');
    treeFilterSolBtn.classList.add('btn-secondary');
    if (isV4Mode) {
      renderV4DualTrees();
    } else {
      renderSearchTreeSVG();
    }
    if (currentExplorationEvents && currentExplorationEvents[currentExplorationIndex]) {
      highlightTreeNodeForEvent(currentExplorationEvents[currentExplorationIndex]);
    }
  });

  treeFilterSolBtn.addEventListener('click', () => {
    treeFilterMode = "solution";
    treeFilterSolBtn.classList.add('active', 'btn-primary');
    treeFilterSolBtn.classList.remove('btn-secondary');
    treeFilterAllBtn.classList.remove('active', 'btn-primary');
    treeFilterAllBtn.classList.add('btn-secondary');
    if (isV4Mode) {
      renderV4DualTrees();
    } else {
      renderSearchTreeSVG();
    }
    if (currentExplorationEvents && currentExplorationEvents[currentExplorationIndex]) {
      highlightTreeNodeForEvent(currentExplorationEvents[currentExplorationIndex]);
    }
  });
}

// V4 Bridge Actions
if (v4FocusMeetingBtn) {
  v4FocusMeetingBtn.addEventListener('click', () => {
    if (v4LayoutMode === 'connected') {
      if (v4ConnFwdNodes && v4ConnectedContainer) {
        const meetingNode = v4ConnFwdNodes.querySelector('.tree-node.meeting-node');
        if (meetingNode) {
          const transformAttr = meetingNode.getAttribute('transform');
          const match = /translate\(([^,]+),\s*([^)]+)\)/.exec(transformAttr);
          if (match) {
            const nx = parseFloat(match[1]);
            const ny = parseFloat(match[2]);
            const vw = v4ConnectedContainer.clientWidth || 800;
            const vh = v4ConnectedContainer.clientHeight || 550;
            v4ConnPan.x = (vw / 2) - (nx * v4ConnScale);
            v4ConnPan.y = (vh / 2) - (ny * v4ConnScale);
            updateV4ConnTransform();
            return;
          }
        }
      }
    }

    if (v4FwdNodesLayer && v4FwdContainer) {
      const meetingNode = v4FwdNodesLayer.querySelector('.tree-node.meeting-node');
      if (meetingNode) {
        const transformAttr = meetingNode.getAttribute('transform');
        const match = /translate\(([^,]+),\s*([^)]+)\)/.exec(transformAttr);
        if (match) {
          const nx = parseFloat(match[1]);
          const ny = parseFloat(match[2]);
          const vw = v4FwdContainer.clientWidth || 400;
          const vh = v4FwdContainer.clientHeight || 450;
          v4FwdPan.x = (vw / 2) - (nx * v4FwdScale);
          v4FwdPan.y = (vh / 2) - (ny * v4FwdScale);
          updateV4FwdTransform();
        }
      }
    }

    if (v4BwdNodesLayer && v4BwdContainer) {
      const meetingNode = v4BwdNodesLayer.querySelector('.tree-node.meeting-node');
      if (meetingNode) {
        const transformAttr = meetingNode.getAttribute('transform');
        const match = /translate\(([^,]+),\s*([^)]+)\)/.exec(transformAttr);
        if (match) {
          const nx = parseFloat(match[1]);
          const ny = parseFloat(match[2]);
          const vw = v4BwdContainer.clientWidth || 400;
          const vh = v4BwdContainer.clientHeight || 450;
          v4BwdPan.x = (vw / 2) - (nx * v4BwdScale);
          v4BwdPan.y = (vh / 2) - (ny * v4BwdScale);
          updateV4BwdTransform();
        }
      }
    }
  });
}

if (v4ReplayCubeBtn) {
  v4ReplayCubeBtn.addEventListener('click', () => {
    const session = getActiveSession();
    if (!session || !session.solver_solution || session.solver_solution.length === 0) return;
    stopExplorationAutoPlay();
    session.current_step_index = 0;
    syncActiveSessionToUI();
    startAutoPlay();
  });
}

if (v4BridgeMinimizeBtn && v4BridgePanel) {
  v4BridgeMinimizeBtn.addEventListener('click', () => {
    v4BridgePanel.classList.toggle('collapsed');
    v4BridgeMinimizeBtn.textContent = v4BridgePanel.classList.contains('collapsed') ? '+ Max' : '− Min';
  });
}

// View Mode Toggle (Tree View vs Event Log Table)
if (viewTreeTabBtn && viewTableTabBtn) {
  viewTreeTabBtn.addEventListener('click', () => {
    viewTreeTabBtn.classList.add('btn-primary');
    viewTreeTabBtn.classList.remove('btn-secondary');
    viewTableTabBtn.classList.remove('btn-primary');
    viewTableTabBtn.classList.add('btn-secondary');

    if (treeViewport) treeViewport.style.display = "block";
    if (treeLegendBar) treeLegendBar.style.display = "flex";
    if (treeControlsGroup) treeControlsGroup.style.display = "flex";
    if (eventTableContainer) eventTableContainer.style.display = "none";

    if (isV4Mode) {
      if (v4LayoutMode === 'connected') {
        fitV4ConnectedTreeToView();
      } else {
        fitV4TreesToView();
      }
    } else {
      fitSearchTreeToView();
    }
  });

  viewTableTabBtn.addEventListener('click', () => {
    viewTableTabBtn.classList.add('btn-primary');
    viewTableTabBtn.classList.remove('btn-secondary');
    viewTreeTabBtn.classList.remove('btn-primary');
    viewTreeTabBtn.classList.add('btn-secondary');

    if (treeViewport) treeViewport.style.display = "none";
    if (treeLegendBar) treeLegendBar.style.display = "none";
    if (treeControlsGroup) treeControlsGroup.style.display = "none";
    if (eventTableContainer) eventTableContainer.style.display = "block";
  });
}

// ---------------------------------------------------------------------------
// Shared Scramble Management (Requirement 1 & 6)
// ---------------------------------------------------------------------------
depthInput.addEventListener('input', (e) => {
  depthDisplay.textContent = e.target.value;
});

newRandomScrambleBtn.addEventListener('click', async () => {
  if (cube3d.isAnimating) return;
  const depth = parseInt(depthInput.value, 10);
  newRandomScrambleBtn.disabled = true;

  try {
    const exp = await createSharedExperiment(null, depth);
    setActiveExperiment(exp);
  } catch (err) {
    alert(`Failed to create random scramble: ${err.message}`);
  } finally {
    newRandomScrambleBtn.disabled = false;
  }
});

applyCustomScrambleBtn.addEventListener('click', async () => {
  if (cube3d.isAnimating) return;
  const text = customScrambleInput.value.trim();
  if (!text) return;

  const tokens = text.split(/[\s,]+/).filter(Boolean);
  for (const t of tokens) {
    if (!ALL_MOVE_NAMES.includes(t)) {
      alert(`Invalid scramble move "${t}". Supported 12 moves: ${ALL_MOVE_NAMES.join(', ')}.`);
      return;
    }
  }

  applyCustomScrambleBtn.disabled = true;
  try {
    const exp = await createSharedExperiment(tokens);
    setActiveExperiment(exp);
    customScrambleInput.value = '';
  } catch (err) {
    alert(`Failed to set custom scramble: ${err.message}`);
  } finally {
    applyCustomScrambleBtn.disabled = false;
  }
});

resetExpBtn.addEventListener('click', async () => {
  if (cube3d.isAnimating) return;
  if (!confirm("Reset entire experiment? This creates a fresh clean experiment at the solved state.")) {
    return;
  }
  const exp = await createSharedExperiment([]);
  setActiveExperiment(exp);
});

function setActiveExperiment(exp) {
  activeExperiment = exp;

  expIdBadge.textContent = exp.id;
  sharedScrambleDisplay.textContent = exp.scramble_moves.length > 0 ? exp.scramble_moves.join(' ') : "(Solved State)";
  sharedInverseDisplay.textContent = exp.inverse_moves.length > 0 ? exp.inverse_moves.join(' ') : "(None)";

  syncActiveSessionToUI();
}

// ---------------------------------------------------------------------------
// Saved Experiments Archive Modal (Requirement 10)
// ---------------------------------------------------------------------------
expHistoryBtn.addEventListener('click', async () => {
  const exps = await listAllExperiments(20);
  if (exps.length === 0) {
    modalExpList.innerHTML = `<div style="color:var(--text-muted); padding:12px; text-align:center;">No saved experiments in SQLite yet.</div>`;
  } else {
    modalExpList.innerHTML = exps.map(e => `
      <div style="background:#1e293b; border:1px solid ${e.is_active ? 'var(--accent)' : 'var(--border)'}; border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-weight:700; font-family:monospace; color:${e.is_active ? 'var(--accent)' : 'var(--text-main)'};">
            ${e.id} ${e.is_active ? '<span style="font-size:0.75rem; background:#0369a140; padding:2px 6px; border-radius:4px; margin-left:6px;">ACTIVE</span>' : ''}
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">
            Scramble: <strong style="color:#e2e8f0;">${e.scramble_moves.length > 0 ? e.scramble_moves.join(' ') : 'Solved'}</strong>
            &bull; Solved: ${e.solved_count}/5 methods
          </div>
        </div>
        <button class="btn btn-primary" style="padding:4px 10px; font-size:0.8rem;" data-load-exp="${e.id}">
          Load
        </button>
      </div>
    `).join('');

    modalExpList.querySelectorAll('[data-load-exp]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.loadExp;
        try {
          const exp = await loadSavedExperiment(id);
          setActiveExperiment(exp);
          expModal.close();
        } catch (err) {
          alert(`Failed to load experiment: ${err.message}`);
        }
      });
    });
  }
  expModal.showModal();
});

closeModalBtn.addEventListener('click', () => {
  expModal.close();
});

// ---------------------------------------------------------------------------
// State Validation & Move Explanation
// ---------------------------------------------------------------------------
function validateStateWithPython(stepIdx) {
  const session = getActiveSession();
  if (!session || !session.intermediate_states || !session.intermediate_states[stepIdx]) {
    stateValidationBadge.textContent = "● State Synchronized";
    stateValidationBadge.style.color = "#10b981";
    return;
  }

  const expected = session.intermediate_states[stepIdx];
  const permMatch = JSON.stringify(session.current_perm) === JSON.stringify(expected.perm);
  const orientMatch = JSON.stringify(session.current_orient) === JSON.stringify(expected.orient);

  if (permMatch && orientMatch) {
    stateValidationBadge.textContent = `✔ Verified with Python Step ${stepIdx}`;
    stateValidationBadge.style.color = "#10b981";
  } else {
    stateValidationBadge.textContent = `⚠ State Mismatch at Step ${stepIdx}`;
    stateValidationBadge.style.color = "#ef4444";
  }
}

function updateExplanationBox(moveName) {
  const info = MOVE_EXPLANATIONS[moveName];
  if (!info) return;

  expMoveBadge.textContent = moveName;
  expMoveTitle.textContent = `${info.face} Face (${moveName})`;
  expMoveDir.textContent = info.direction;
  expMoveDesc.textContent = `${info.text} (relative to observer looking directly at the ${info.face} face).`;
}

// ---------------------------------------------------------------------------
// Educational Mode ("Explain Every Move")
// ---------------------------------------------------------------------------
eduModeToggle.addEventListener('change', () => {
  eduPanel.style.display = eduModeToggle.checked ? 'flex' : 'none';
  if (eduModeToggle.checked) {
    const session = getActiveSession();
    if (session) {
      updateEducationalPanel(null, null, { perm: session.current_perm, orient: session.current_orient });
    }
  }
});

function updateEducationalPanel(moveName, stateBefore, stateAfter) {
  if (!eduModeToggle.checked || !stateAfter) return;

  eduPermDisplay.textContent = `(${stateAfter.perm.join(', ')}, 7)`;
  eduOrientDisplay.textContent = `(${stateAfter.orient.join(', ')}, 0)`;

  const orientSum = stateAfter.orient.reduce((a, b) => a + b, 0);
  const invariantOk = orientSum % 3 === 0;

  if (moveName && MOVE_EXPLANATIONS[moveName]) {
    const info = MOVE_EXPLANATIONS[moveName];
    eduExplanationText.innerHTML = `
      <strong>Turn:</strong> <span style="color:var(--accent); font-weight:bold;">${moveName}</span> (${info.face} face, ${info.direction} 90°).<br>
      <strong>Orientation Invariant:</strong> Sum = ${orientSum} (mod 3 = ${orientSum % 3}) &mdash; <span style="color:${invariantOk ? '#10b981' : '#ef4444'}; font-weight:bold;">${invariantOk ? 'Valid' : 'Broken!'}</span>.<br>
      <strong>State-Space Effect:</strong> Permutes the 4 corners on the ${info.face} face and adjusts orientations according to the move tensor.
    `;
  } else {
    eduExplanationText.innerHTML = `
      Current permutation and orientation state vectors. DBL corner (slot 7) held permanently fixed.
      Orientation invariant: Sum = ${orientSum} mod 3 = <strong>${orientSum % 3}</strong> (${invariantOk ? 'Valid' : 'Invalid'}).
    `;
  }
}

// ---------------------------------------------------------------------------
// Keyboard Shortcuts
// ---------------------------------------------------------------------------
window.addEventListener('keydown', (e) => {
  if (document.activeElement === customScrambleInput) return;

  const key = e.key;
  if (key === 'u' || key === 'U') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "U'" : "U");
  } else if (key === 'r' || key === 'R') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "R'" : "R");
  } else if (key === 'f' || key === 'F') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "F'" : "F");
  } else if (key === 'd' || key === 'D') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "D'" : "D");
  } else if (key === 'l' || key === 'L') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "L'" : "L");
  } else if (key === 'b' || key === 'B') {
    e.preventDefault();
    executeManualMove(e.shiftKey ? "B'" : "B");
  } else if (key === ' ') {
    e.preventDefault();
    playBtn.click();
  } else if (key === 'ArrowRight') {
    e.preventDefault();
    nextStepBtn.click();
  } else if (key === 'ArrowLeft') {
    e.preventDefault();
    prevStepBtn.click();
  } else if ((key === 'z' || key === 'Z') && !e.metaKey && !e.ctrlKey) {
    undoBtn.click();
  } else if ((key === 'y' || key === 'Y') && !e.metaKey && !e.ctrlKey) {
    redoBtn.click();
  }
});

// ---------------------------------------------------------------------------
// 2D Net Display Update
// ---------------------------------------------------------------------------
function updateCube2DNet(state) {
  const stickers = stateToStickers(state);
  for (const face of ["U", "D", "F", "B", "R", "L"]) {
    const faceColors = stickers[face];
    for (let i = 0; i < 4; i++) {
      const el = document.getElementById(`s-${face}-${i}`);
      if (el) {
        el.style.backgroundColor = COLOR_HEX[faceColors[i]];
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Head-to-Head Comparison (Tab 2)
// ---------------------------------------------------------------------------
compareAllBtn.addEventListener('click', async () => {
  if (!isBackendConnected) {
    isBackendConnected = await checkBackendHealth();
    if (!isBackendConnected) {
      alert("Python backend is not running.\n\nPlease start: python3 backend/server.py 8000");
      return;
    }
  }

  if (!activeExperiment) return;

  compareAllBtn.disabled = true;
  compareAllBtn.textContent = "Python Running All 5 Solvers on Shared Scramble...";

  try {
    const res = await compareAllWithPython(activeExperiment.initial_perm, activeExperiment.initial_orient);
    const results = res.results || {};

    const algoMeta = {
      "v1": { name: "V1: Unpruned DFS", optimal: "No" },
      "v2": { name: "V2: Unidirectional BFS", optimal: "Yes" },
      "v3": { name: "V3: Move-Pruned BFS", optimal: "Yes" },
      "v4": { name: "V4: Bidirectional BFS", optimal: "Yes" },
      "v5": { name: "V5: IDA*", optimal: "Yes" },
    };

    const rows = [];
    for (const [key, meta] of Object.entries(algoMeta)) {
      const r = results[key] || {};
      rows.push(`
        <tr style="border-bottom:1px solid #334155;">
          <td style="padding:10px 14px; font-weight:600;">${meta.name}</td>
          <td style="padding:10px 14px; color:${meta.optimal === 'Yes' ? '#10b981' : '#f59e0b'}; font-weight:bold;">${meta.optimal}</td>
          <td style="padding:10px 14px; font-weight:bold;">${r.found ? r.solution_length : 'Timeout/Failed'}</td>
          <td style="padding:10px 14px;">${r.expanded_states ? r.expanded_states.toLocaleString() : '-'}</td>
          <td style="padding:10px 14px;">${r.elapsed_ms ? r.elapsed_ms.toFixed(2) + ' ms' : '-'}</td>
          <td style="padding:10px 14px;">${r.peak_memory_kb ? r.peak_memory_kb.toFixed(1) + ' KB' : '-'}</td>
        </tr>
      `);
    }

    compareTableBody.innerHTML = rows.join('');
  } catch (err) {
    compareTableBody.innerHTML = `<tr><td colspan="6" style="padding:16px; color:#ef4444;">Error connecting to Python: ${err.message}</td></tr>`;
  } finally {
    compareAllBtn.disabled = false;
    compareAllBtn.textContent = "Compare All on Current Scramble";
  }
});

// ---------------------------------------------------------------------------
// Persistent SQLite History (Tab 3)
// ---------------------------------------------------------------------------
async function loadHistoryFromSQLite() {
  const summary = await fetchHistorySummary();
  if (summary && historySummaryBadge) {
    historySummaryBadge.textContent =
      `Stored in SQLite: ${summary.total_solves_stored} Solves | ${summary.total_benchmarks_stored} Benchmarks | ${summary.total_verification_cases_stored} Tests`;
  }

  const solves = await fetchRecentSolves(25);
  if (historyTableBody) {
    if (solves.length === 0) {
      historyTableBody.innerHTML = `<tr><td colspan="6" style="padding:16px; text-align:center; color:var(--text-muted);">No records found in SQLite yet. Run solves or benchmarks to populate.</td></tr>`;
      return;
    }

    const rows = solves.map(s => {
      let solList = [];
      try { solList = JSON.parse(s.solution); } catch(e){}
      return `
        <tr style="border-bottom:1px solid #334155;">
          <td style="padding:8px 12px; font-size:0.8rem; color:var(--text-muted);">${s.timestamp.replace('T', ' ').substring(0, 19)}</td>
          <td style="padding:8px 12px; font-weight:600;">${s.algorithm.toUpperCase()}</td>
          <td style="padding:8px 12px; font-weight:bold;">${s.solution_length}</td>
          <td style="padding:8px 12px;">${s.expanded_states.toLocaleString()}</td>
          <td style="padding:8px 12px;">${s.elapsed_ms.toFixed(1)} ms</td>
          <td style="padding:8px 12px; font-family:monospace; font-size:0.85rem;">${solList.join(' ')}</td>
        </tr>
      `;
    });
    historyTableBody.innerHTML = rows.join('');
  }
}

// ---------------------------------------------------------------------------
// Check Python Backend & Initial Startup
// ---------------------------------------------------------------------------
async function updateBackendStatus() {
  isBackendConnected = await checkBackendHealth();
  if (isBackendConnected) {
    backendStatus.textContent = "● Python Backend Connected";
    backendStatus.style.color = "#10b981";
  } else {
    backendStatus.textContent = "⚠ Python Backend Offline (start: python3 backend/server.py 8000)";
    backendStatus.style.color = "#f59e0b";
  }
}

async function initializeApp() {
  await updateBackendStatus();
  setInterval(updateBackendStatus, 5000);

  try {
    const exp = await fetchActiveExperiment();
    setActiveExperiment(exp);
  } catch (err) {
    console.warn("Could not fetch active experiment, creating local fallback:", err);
    setActiveExperiment({
      id: "exp_local_init",
      scramble_moves: ["R", "U", "R'", "F"],
      inverse_moves: ["F'", "R", "U'", "R'"],
      initial_perm: [0, 5, 2, 3, 4, 1, 6],
      initial_orient: [0, 0, 0, 0, 0, 0, 0],
      sessions: {
        v1: { algorithm: "v1", current_perm: [0, 5, 2, 3, 4, 1, 6], current_orient: [0, 0, 0, 0, 0, 0, 0], user_moves: [], solver_solution: [], current_step_index: 0, status: "not_started" },
        v2: { algorithm: "v2", current_perm: [0, 5, 2, 3, 4, 1, 6], current_orient: [0, 0, 0, 0, 0, 0, 0], user_moves: [], solver_solution: [], current_step_index: 0, status: "not_started" },
        v3: { algorithm: "v3", current_perm: [0, 5, 2, 3, 4, 1, 6], current_orient: [0, 0, 0, 0, 0, 0, 0], user_moves: [], solver_solution: [], current_step_index: 0, status: "not_started" },
        v4: { algorithm: "v4", current_perm: [0, 5, 2, 3, 4, 1, 6], current_orient: [0, 0, 0, 0, 0, 0, 0], user_moves: [], solver_solution: [], current_step_index: 0, status: "not_started" },
        v5: { algorithm: "v5", current_perm: [0, 5, 2, 3, 4, 1, 6], current_orient: [0, 0, 0, 0, 0, 0, 0], user_moves: [], solver_solution: [], current_step_index: 0, status: "not_started" },
      }
    });
  }

  loadHistoryFromSQLite();
}

initializeApp();
