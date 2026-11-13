# Experiment 1 — Verification Suite Report

**Reproducible Random Seed**: `42`  
**Total Test Cases**: 120 (20 trials for each depth $d \in \{1, 2, 3, 4, 5, 6\}$)  
**Independent Ground Truth Reference**: Decoupled Unpruned Breadth-First Search (`reference_unpruned_bfs`)

## Summary Results

| Metric | V2 Unidirectional BFS | V3 Move-Pruned BFS | V4 Bidirectional BFS | V5 IDA* |
| :--- | :---: | :---: | :---: | :---: |
| **Cases Solved** | **120/120** (100%) | **120/120** (100%) | **120/120** (100%) | **120/120** (100%) |
| **Valid Replays** | **120/120** (100%) | **120/120** (100%) | **120/120** (100%) | **120/120** (100%) |
| **Optimality Match vs Ground Truth** | **120/120** | **120/120** | **120/120** | **120/120** |

**Total Exact 4-Way Optimality Agreement**: **120 / 120** (100.0%)  
**Failures**: 0

## Mean Optimal Depth vs Scramble Depth

| Scramble Depth ($d$) | Number of Trials | Mean Optimal Depth ($d^*$) | Difference ($d - d^*$) | Explanation |
| :---: | :---: | :---: | :---: | :--- |
| **1** | 20 | 1 | 0.000 | 1 quarter turn is strictly irreducible. |
| **2** | 20 | 2 | 0.000 | 2 quarter turns on non-same faces never cancel. |
| **3** | 20 | 3 | 0 | Occasional 3-turn sequences reach shorter cycle states. |
| **4** | 20 | 4 | 0 | Permutation commutators can create shortcuts of length 2 or 3. |
| **5** | 20 | 5 | 0 | State-space cycles mean scramble length $\ge$ shortest path length. |
| **6** | 20 | 6 | 0 | Multiple paths exist in Cayley graph; BFS finds strictly shortest. |

All 120 solutions independently transform the starting state into the exact goal state `((0,1,2,3,4,5,6), (0,0,0,0,0,0,0))`.
