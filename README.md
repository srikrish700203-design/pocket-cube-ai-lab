# Pocket Cube (2×2) State-Space Search AI Lab
### Academic Implementation & Empirical Evaluation (Problem 2)

---

## 1. Executive Summary & Architecture

This repository contains an academic AI and state-space search system for the **2×2×2 Pocket Rubik's Cube** ($|V| = 3,674,160$ reachable states). 

### Core Architectural Principle
**Python is the single source of truth** for all mathematical logic, state encoding, transition tables, search algorithms, empirical benchmarks, and data measurements.
- The Python implementation is **completely self-contained and independently runnable** without the frontend.
- All algorithms (V1 to V5), heuristics, tests, benchmarks, and SQLite logging execute strictly in Python.
- The web frontend (`frontend/`) acts strictly as a **presentation layer**, sending requests to the Python FastAPI backend (`backend/api/`) and rendering authentic Python-computed metrics, real search event traces, and animated solution paths.

---

## 2. Mathematical State Representation

### 2.1 Compact Cubie Tuple: `s = (perm, orient)`
Holding the **Down-Back-Left (DBL)** corner cubie (index 7) permanently fixed in its home slot eliminates whole-cube rotations and reduces the required face turns exclusively to quarter-turns of the three remaining faces: **Up ($U$)**, **Right ($R$)**, and **Front ($F$)**.

Every reachable state is uniquely encoded as a pair of length-7 immutable integer tuples:
$$s = (\text{perm}, \text{orient})$$
- **Permutation Tuple**: $\text{perm} = (\pi_0, \pi_1, \dots, \pi_6)$ where $\pi_i \in \{0, \dots, 6\}$ denotes the physical cubie occupying slot $i$.
  - Slots: $0=\text{UFL}, 1=\text{UFR}, 2=\text{UBR}, 3=\text{UBL}, 4=\text{DFL}, 5=\text{DFR}, 6=\text{DBR}$.
  - Solved: $\text{perm}_0 = (0, 1, 2, 3, 4, 5, 6)$.
- **Orientation Tuple**: $\text{orient} = (o_0, o_1, \dots, o_6)$ where $o_i \in \{0, 1, 2\}$ denotes the clockwise twist of the piece relative to the U/D reference faces ($0 = \text{correct}$, $1 = +120^\circ$, $2 = +240^\circ$).
  - Solved: $\text{orient}_0 = (0, 0, 0, 0, 0, 0, 0)$.

### 2.2 Orientation Sum Invariant
$$\sum_{i=0}^6 o_i \equiv 0 \pmod 3$$
- $U$ and $U'$ moves do not alter orientation ($\Delta = 0$).
- $R, R', F, F'$ add $(+1, +2, +1, +2) \pmod 3$ to four corner cubies, contributing $\Delta_{\text{sum}} = 6 \equiv 0 \pmod 3$.
- Any state violating this invariant (e.g. a physically popped and twisted corner) resides in a disconnected orbit and can never be solved.

### 2.3 Sticker Grid Representation & 2-Way Decoding
- `state_to_sticker_grid(state)`: Encodes state into a 24-element color array (6 faces $\times$ 4 stickers: $U, D, F, B, R, L$).
- `sticker_grid_to_state(grid)`: Decodes the 24-sticker array back into the canonical $(\text{perm}, \text{orient})$ tuple.

---

## 3. The 5-Stage Algorithmic Evolution Ladder

| Version | Search Strategy & Data Structures | Branching | Time Complexity | Peak Memory (Space) | Optimality ($d^*$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **V1** | **Naive 24-Sticker Array + Unpruned DFS**<br>Pure 24-sticker colour array recursion; NO visited set, NO depth cap. Explores raw cycles ($R \to R' \dots$). | $b = 6$ | $O(b^D)$ (infinite / cyclic) | $O(D)$ call stack depth | **No** (can loop indefinitely, times out) |
| **V2** | **Compact Cubie Tuple + Unidirectional BFS**<br>FIFO queue (`collections.deque`) + Visited Hash Map (`dict`). | $b = 6$ | $O(b^d)$ | $O(b^d)$ queue/hash table | **Yes** (guaranteed shortest path) |
| **V3** | **Move-Pruned BFS**<br>FIFO queue + same-face consecutive turn pruning. | $b_{\text{eff}} \approx 4$ | $O(b \cdot b_{\text{eff}}^{d-1})$ | $O(b \cdot b_{\text{eff}}^{d-1})$ | **Yes** (sound pruning preserves shortest path) |
| **V4** | **Bidirectional BFS (Meet-in-the-Middle)**<br>Two synchronized FIFO queues ($Q_F, Q_B$) + Two Hash Tables. | $b_{\text{eff}} \approx 4$ | $O(2 \cdot b_{\text{eff}}^{d/2})$ | $O(2 \cdot b_{\text{eff}}^{d/2})$ | **Yes** (full level sync + stitched inverse path) |
| **V5** | **Iterative Deepening A\* (IDA\*)**<br>DFS with $f(s) = g(s) + h(s)$ cost thresholds. | $b \le 6$ | $O(b^d)$ | **$O(d)$ stack depth** (~2.9 KB) | **Yes** (admissible $h(s) \le h^*(s)$) |

### Prescribed Corner Heuristic (V5)
$$h(s) = \left\lceil \frac{\text{misplaced\_or\_twisted\_corners}(s)}{4} \right\rceil$$
Because any legal quarter-turn affects at most 4 corners, at most 4 misplaced or twisted corners can be corrected in a single move. Hence $h(s)$ is strictly admissible ($h(s) \le h^*(s)$).

---

## 4. Theoretical Analysis & Handout Solutions

### Q1. Hand-Worked Tuple Trace: $s_0 \xrightarrow{R} s_1 \xrightarrow{U} s_2 \xrightarrow{R'} s_3$
- **$s_0$ (Solved)**: $\text{perm} = (0, 1, 2, 3, 4, 5, 6)$, $\text{orient} = (0, 0, 0, 0, 0, 0, 0)$
- **$s_1$ (After $R$)**: $\text{perm} = (0, 5, 1, 3, 4, 6, 2)$, $\text{orient} = (0, 1, 2, 0, 0, 2, 1)$ ($\sum o_i = 6 \equiv 0 \pmod 3$)
- **$s_2$ (After $U$)**: $\text{perm} = (5, 1, 3, 0, 4, 6, 2)$, $\text{orient} = (1, 2, 0, 0, 0, 2, 1)$ ($\sum o_i = 6 \equiv 0 \pmod 3$)
- **$s_3$ (After $R'$)**: $\text{perm} = (5, 3, 2, 0, 4, 1, 6)$, $\text{orient} = (1, 1, 0, 0, 0, 1, 0)$ ($\sum o_i = 3 \equiv 0 \pmod 3$)

### Q2. Orientation Invariant Proof & Impossible Scrambles
- Every move alters the orientation sum by $0$ ($U, U'$) or $+6$ ($R, R', F, F'$).
- Since $\sum o_i \pmod 3$ is invariant, physically popping and re-twisting a single corner yields $\sum o_i \equiv 1 \pmod 3$, which can never be transitioned into $s_0$ ($\sum o_i \equiv 0 \pmod 3$). BFS will explore all 3.67M reachable states in its component and terminate without finding a path.

### Q3. Quantifying Frontier Collapse ($d = 12$)
- **Stage 2 (Unpruned BFS, $b=6$)**: $N_2 = 6^{12} = \mathbf{2,176,782,336}$
- **Stage 3 (Face-Pruned BFS, $b_{\text{eff}}=4$)**: $N_3 = 6 \cdot 4^{11} = \mathbf{25,165,824}$ ($\mathbf{86.5\times}$ speedup)
- **Stage 4 (Bidirectional BFS, $d/2=6$)**: $N_4 = 2 \cdot (6 \cdot 4^5) = \mathbf{12,288}$ ($\mathbf{177,147\times}$ speedup vs. Stage 2)

### Q4. Bidirectional Path Stitching & Move Inversion
The backward frontier records the forward transition $s_{\text{parent}} \xrightarrow{m} s_{\text{child}}$. To form the path from meeting state $s^*$ back to $s_{\text{goal}}$, we must reverse the chronological sequence and invert each move direction:
$$(m_1, m_2, \dots, m_k) \implies (m_k^{-1}, \dots, m_1^{-1})$$

---

## 5. Persistent SQLite Architecture

All experimental data is permanently logged to an SQLite database: `backend/pocket_cube.db`.

### Database Schema
1. `benchmarks`: Stores depth, algorithm, scramble, expanded nodes, generated nodes, peak memory (KB), wall-clock time (ms), and solution paths.
2. `verification_tests`: Stores 20-case randomized verification runs, optimal lengths $d^*$, and comparative timings.
3. `solve_history`: Stores all interactive solves executed through CLI or API.

---

## 6. How to Run (Independent Python Deliverable)

### 6.1 Run Automated Tests (87 Tests)
```bash
python3 backend/cli.py test
# Or directly:
python3 backend/run_tests.py
```

### 6.2 Run 20-Case Randomized Verification Suite
```bash
python3 backend/cli.py verify
```

### 6.3 Run Multi-Depth Empirical Benchmark
```bash
python3 backend/cli.py benchmark --depths 2,4,6,8,10,11
```

### 6.4 Solve Custom Scrambles
```bash
python3 backend/cli.py solve --algo v4 --scramble "R U R' F"
```

### 6.5 Head-to-Head Algorithm Comparison
```bash
python3 backend/cli.py compare --scramble "R U R' F U'"
```

### 6.6 Inspect Persistent SQLite History
```bash
python3 backend/cli.py history
```

### 6.7 Start Python Backend Server
```bash
# Option A: Zero-dependency standalone Python server (recommended, no extra packages needed):
python3 backend/server.py

# Option B: FastAPI server via Uvicorn (if fastapi & uvicorn are installed):
cd backend && uvicorn api.main:app --port 8000 --reload
```
The server serves both the REST API at `http://127.0.0.1:8000/api/` and the interactive 3D web application at `http://127.0.0.1:8000/`.

---

## 7. Interactive 3D Pocket Cube & Step-by-Step AI Solver

The web interface provides an authentic, physics-based 3D simulation powered by Three.js and OrbitControls:
- **Realistic 3D Pocket Cube**: 8 physical cubies with dark gaps, standard Rubik's stickers (White, Yellow, Green, Blue, Red, Orange), perspective lighting, and smooth shadows.
- **Full Camera Orbit & Zoom**: Left-click & drag to orbit around the cube to inspect all 6 faces; scroll wheel to zoom; click **🎥 Reset Camera** to snap back.
- **Physical 90° Face-Turn Animations**: Groups the 4 cubies belonging to any face and physically rotates them along their face normal (supports all 12 turns: $U, U', R, R', F, F', D, D', L, L', B, B'$).
- **Step-by-Step AI Solving Animation**:
  - Displays the complete Python-generated solution path with highlighted active move, dimmed completed moves, and visible upcoming turns.
  - Interactive controls: **Play / Pause**, **⏮ Prev Step**, **⏭ Next Step**, **↺ Restart**.
  - Configurable animation speeds: $0.25\times, 0.5\times, 1\times, 1.5\times, 2\times$.
  - In-flight state validation against Python pre-computed intermediate states.
- **Move Notation & Explanation Box**: Details the active move name, face, direction (looking directly at face), and mechanical description.
- **Educational Mode ("Explain Every Move")**: Pauses at each step and exposes the underlying state-space representation (permutation vector, orientation vector, $\sum o_i \equiv 0 \pmod 3$ invariant check, and Python state synchronization).
- **Manual Manipulation**: 12 quarter-turn buttons, custom move sequence input (e.g. `R U R' F`), Undo/Redo stack, random scrambler (depth 1–11), and keyboard shortcuts ($U, R, F, D, L, B$, Space, Arrows, $Z, Y$).
- **Head-to-Head Comparison & SQLite History**: Compare V1–V5 concurrently on any scramble, inspect permanent SQLite benchmark logs, and view empirical SVG performance plots.
