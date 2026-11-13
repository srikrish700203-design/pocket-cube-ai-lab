"""
Pocket Cube Move Tables
========================

Moves: U, U', R, R', F, F'

Each move is defined by:
  1. corner_perm_effect: how the 8 corner positions permute
     (as a full 8-element tuple; index 7 = DBL is never moved)
  2. corner_orient_delta: orientation change (+1 or +2 mod 3) for each
     of the 8 corners after the move; 0 means no change.

Convention for orientation:
  - Orientation 0: the U/D sticker of this corner faces U or D.
  - Each CW quarter-turn of R or F twists corners.
  - U-face moves do not change corner orientations.

Derivation method:
  For each move, we track exactly which 4 corners cycle and how they twist.

  R-move (clockwise, right face):
    Corners involved: UFR(1), UBR(2), DBR(6), DFR(5)
    Cycle: 1→2→6→5→1  (the piece at slot 1 goes to slot 2, etc.)
    Twist deltas: UFR→+2, UBR→+1, DBR→+2, DFR→+1
    (R twists the right-face corners; alternating +2,+1 around the cycle)

  U-move (clockwise, upper face):
    Corners involved: UFL(0), UFR(1), UBR(2), UBL(3)
    Cycle: 0→1→2→3→0
    Twist deltas: none (U-face moves preserve orientation)

  F-move (clockwise, front face):
    Corners involved: UFL(0), UFR(1), DFR(5), DFL(4)
    Cycle: 0→1→5→4→0
    Twist deltas: UFL→+1, UFR→+2, DFR→+1, DFL→+2
    (F twists the front-face corners)

Verification (built into this module's tests):
  - move ∘ inverse(move) = identity  for all moves
  - move^4 = identity  for all moves
  - Orientation sum invariant preserved after every move
  - DBL corner (index 7) never permuted
"""

from __future__ import annotations
from typing import Tuple, Dict
from .state import State, Perm, Orient, SOLVED_STATE, make_state, is_valid_state

# ---------------------------------------------------------------------------
# Move representation
# ---------------------------------------------------------------------------

# A move is defined by its effect on all 8 corner slots (including fixed DBL=7).
# perm_effect[i] = j means "after this move, the piece that was in slot j is now in slot i"
# (i.e., the corner at position j moves to position i)
# This is a *destination* array: new_positions[i] = old_positions[perm_effect[i]]
# We store moves as WHAT COMES TO POSITION i FROM position j.

# More precisely, we store it as a *source* permutation:
#   after the move, slot i contains the piece that was in MOVE_PERM[i].
# For slots not involved in a move, MOVE_PERM[i] = i.

# Orientation deltas: orient_delta[i] = amount added to orientation of
# the piece that LANDS in slot i (after permuting). Values in {0, 1, 2}.

# ---------------------------------------------------------------------------
# U move (clockwise 90° looking from above)
# Cycle of slots: 0(UFL)→3(UBL)→2(UBR)→1(UFR)→0
# Meaning: slot 0 gets what was in slot 1, slot 1 gets slot 2, etc.
# After move: slot0←slot1, slot1←slot2, slot2←slot3, slot3←slot0
# ---------------------------------------------------------------------------
_U_PERM:   Tuple[int, ...] = (1, 2, 3, 0, 4, 5, 6, 7)   # slot i ← from slot _U_PERM[i]
_U_ORIENT: Tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0)    # U moves don't twist corners

# ---------------------------------------------------------------------------
# U' move (counter-clockwise)
# Inverse of U: slot0←slot3, slot1←slot0, slot2←slot1, slot3←slot2
# ---------------------------------------------------------------------------
_Ui_PERM:   Tuple[int, ...] = (3, 0, 1, 2, 4, 5, 6, 7)
_Ui_ORIENT: Tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0)

# ---------------------------------------------------------------------------
# R move (clockwise 90° looking from the right)
# Cycle of slots: 1(UFR)→2(UBR)→6(DBR)→5(DFR)→1
# After move: slot1←slot5, slot2←slot1, slot5←slot6, slot6←slot2
# Twist deltas (for piece landing in that slot):
#   slot1 gets +2, slot2 gets +1, slot5 gets +1, slot6 gets +2
# ---------------------------------------------------------------------------
_R_PERM:   Tuple[int, ...] = (0, 5, 1, 3, 4, 6, 2, 7)
_R_ORIENT: Tuple[int, ...] = (0, 1, 2, 0, 0, 2, 1, 0)

# ---------------------------------------------------------------------------
# R' move (counter-clockwise)
# Inverse cycle: slot1←slot2, slot2←slot6, slot5←slot1, slot6←slot5
# Twist deltas according to specification: (+1, +2, +1, +2) on (1, 2, 6, 5)
# ---------------------------------------------------------------------------
_Ri_PERM:   Tuple[int, ...] = (0, 2, 6, 3, 4, 1, 5, 7)
_Ri_ORIENT: Tuple[int, ...] = (0, 1, 2, 0, 0, 2, 1, 0)

# ---------------------------------------------------------------------------
# F move (clockwise 90° looking from the front)
# Cycle of slots: 0(UFL)→1(UFR)→5(DFR)→4(DFL)→0
# After move: slot0←slot4, slot1←slot0, slot4←slot5, slot5←slot1
# Twist deltas: (+1, +2, +1, +2) on (0, 1, 5, 4)
#   slot0 gets +1, slot1 gets +2, slot4 gets +2, slot5 gets +1
# ---------------------------------------------------------------------------
_F_PERM:   Tuple[int, ...] = (4, 0, 2, 3, 5, 1, 6, 7)
_F_ORIENT: Tuple[int, ...] = (1, 2, 0, 0, 2, 1, 0, 0)

# ---------------------------------------------------------------------------
# F' move (counter-clockwise)
# Inverse cycle: slot0←slot1, slot1←slot5, slot4←slot0, slot5←slot4
# Twist deltas according to specification: (+1, +2, +1, +2) on (0, 1, 5, 4)
#   slot0 gets +1, slot1 gets +2, slot4 gets +2, slot5 gets +1
# ---------------------------------------------------------------------------
_Fi_PERM:   Tuple[int, ...] = (1, 5, 2, 3, 0, 4, 6, 7)
_Fi_ORIENT: Tuple[int, ...] = (1, 2, 0, 0, 2, 1, 0, 0)

# ---------------------------------------------------------------------------
# D move (clockwise 90° looking from the bottom)
# ---------------------------------------------------------------------------
_D_PERM:   Tuple[int, ...] = (0, 1, 2, 3, 7, 4, 5, 6)
_D_ORIENT: Tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0)
_Di_PERM:  Tuple[int, ...] = (0, 1, 2, 3, 5, 6, 7, 4)
_Di_ORIENT:Tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0)

# ---------------------------------------------------------------------------
# L move (clockwise 90° looking from the left)
# ---------------------------------------------------------------------------
_L_PERM:   Tuple[int, ...] = (3, 1, 2, 7, 0, 5, 6, 4)
_L_ORIENT: Tuple[int, ...] = (2, 0, 0, 1, 1, 0, 0, 2)
_Li_PERM:  Tuple[int, ...] = (4, 1, 2, 0, 7, 5, 6, 3)
_Li_ORIENT:Tuple[int, ...] = (2, 0, 0, 1, 1, 0, 0, 2)

# ---------------------------------------------------------------------------
# B move (clockwise 90° looking from the back)
# ---------------------------------------------------------------------------
_B_PERM:   Tuple[int, ...] = (0, 1, 6, 2, 4, 5, 7, 3)
_B_ORIENT: Tuple[int, ...] = (0, 0, 1, 2, 0, 0, 2, 1)
_Bi_PERM:  Tuple[int, ...] = (0, 1, 3, 7, 4, 5, 2, 6)
_Bi_ORIENT:Tuple[int, ...] = (0, 0, 1, 2, 0, 0, 2, 1)

# ---------------------------------------------------------------------------
# Move registry
# ---------------------------------------------------------------------------

MOVE_NAMES = ["U", "U'", "R", "R'", "F", "F'"]
ALL_MOVE_NAMES = ["U", "U'", "R", "R'", "F", "F'", "D", "D'", "L", "L'", "B", "B'"]

# (perm_effect_8, orient_delta_8)
MOVES: Dict[str, Tuple[Tuple[int,...], Tuple[int,...]]] = {
    "U":  (_U_PERM,  _U_ORIENT),
    "U'": (_Ui_PERM, _Ui_ORIENT),
    "R":  (_R_PERM,  _R_ORIENT),
    "R'": (_Ri_PERM, _Ri_ORIENT),
    "F":  (_F_PERM,  _F_ORIENT),
    "F'": (_Fi_PERM, _Fi_ORIENT),
    "D":  (_D_PERM,  _D_ORIENT),
    "D'": (_Di_PERM, _Di_ORIENT),
    "L":  (_L_PERM,  _L_ORIENT),
    "L'": (_Li_PERM, _Li_ORIENT),
    "B":  (_B_PERM,  _B_ORIENT),
    "B'": (_Bi_PERM, _Bi_ORIENT),
}

INVERSE_MOVE: Dict[str, str] = {
    "U":  "U'", "U'": "U",
    "R":  "R'", "R'": "R",
    "F":  "F'", "F'": "F",
    "D":  "D'", "D'": "D",
    "L":  "L'", "L'": "L",
    "B":  "B'", "B'": "B",
}

# For move-pruned BFS: same face
SAME_FACE: Dict[str, str] = {
    "U":  "U'", "U'": "U",
    "R":  "R'", "R'": "R",
    "F":  "F'", "F'": "F",
    "D":  "D'", "D'": "D",
    "L":  "L'", "L'": "L",
    "B":  "B'", "B'": "B",
}


# ---------------------------------------------------------------------------
# Precomputed 24 whole-cube rotation symmetries
# (Used to normalize D, L, B moves so piece 7 is at slot 7 with twist 0)
# ---------------------------------------------------------------------------

def _apply_raw(p: Tuple[int,...], o: Tuple[int,...], m: str) -> Tuple[Tuple[int,...], Tuple[int,...]]:
    pe, oe = MOVES[m]
    np = tuple(p[pe[i]] for i in range(8))
    no = tuple((o[pe[i]] + oe[i]) % 3 for i in range(8))
    return np, no

def _precompute_rotations():
    rot_x = lambda p, o: _apply_raw(*_apply_raw(p, o, "R"), "L'")
    rot_y = lambda p, o: _apply_raw(*_apply_raw(p, o, "U"), "D'")
    rot_z = lambda p, o: _apply_raw(*_apply_raw(p, o, "F"), "B'")

    solved_8 = (tuple(range(8)), (0,)*8)
    visited = {solved_8: []}
    from collections import deque
    q = deque([solved_8])
    gens = [rot_x, rot_y, rot_z]
    while q:
        cp, co = q.popleft()
        path = visited[(cp, co)]
        for fn in gens:
            nxt = fn(cp, co)
            if nxt not in visited:
                visited[nxt] = path + [fn]
                q.append(nxt)
    return list(visited.values())

_ROTATION_PATHS = _precompute_rotations()


def normalize_state_8(p: Tuple[int,...], o: Tuple[int,...]) -> Tuple[Tuple[int,...], Tuple[int,...]]:
    """Rotate the 8-corner cube so piece 7 is placed at slot 7 with twist 0."""
    if p[7] == 7 and o[7] == 0:
        return p, o
    for path in _ROTATION_PATHS:
        cp, co = p, o
        for fn in path:
            cp, co = fn(cp, co)
        if cp[7] == 7 and co[7] == 0:
            return cp, co
    return p, o


def apply_move(state: State, move_name: str) -> State:
    """
    Apply any of the 12 moves (U, U', R, R', F, F', D, D', L, L', B, B').
    If move is U, R, F, DBL is preserved directly.
    If move is D, L, B, the state is normalized to the canonical DBL-fixed frame.
    """
    if move_name not in MOVES:
        raise ValueError(f"Unknown move: {move_name!r}. Valid: {ALL_MOVE_NAMES}")

    perm_8, orient_delta_8 = MOVES[move_name]
    old_perm, old_orient = state

    full_perm   = old_perm   + (7,) if len(old_perm) == 7 else old_perm
    full_orient = old_orient + (0,) if len(old_orient) == 7 else old_orient

    new_perm   = tuple(full_perm[perm_8[i]]   for i in range(8))
    new_orient = tuple((full_orient[perm_8[i]] + orient_delta_8[i]) % 3 for i in range(8))

    if new_perm[7] == 7 and new_orient[7] == 0:
        return make_state(new_perm[:7], new_orient[:7])

    norm_perm, norm_orient = normalize_state_8(new_perm, new_orient)
    return make_state(norm_perm[:7], norm_orient[:7])


def apply_moves(state: State, move_sequence: list[str]) -> State:
    """Apply a sequence of moves to a state."""
    for m in move_sequence:
        state = apply_move(state, m)
    return state


def invert_sequence(move_sequence: list[str]) -> list[str]:
    """Return the inverse of a move sequence (reversed, each move inverted)."""
    return [INVERSE_MOVE[m] for m in reversed(move_sequence)]


def get_successors(state: State) -> list[tuple[str, State]]:
    """Return all (move_name, successor_state) pairs from a given state."""
    return [(m, apply_move(state, m)) for m in MOVE_NAMES]


def is_move_pruned(move: str, last_move: str | None, run_length: int = 1) -> bool:
    """
    Quarter-Turn Metric (QTM) canonical move pruning rules:
    1. Immediate inverse: M followed by M' (or M' followed by M) = I.
       Always strictly suboptimal (cancels to identity). PRUNED.
    2. Same-direction half-turn: M followed by M is permitted when run_length == 1
       (represents a 180° half-turn, necessary under QTM where no single-move
       half-turn exists).
    3. Three-turn limit: M M M = M' (3 quarter turns in the same direction can
       always be replaced by 1 turn in the opposite direction).
       Therefore, when run_length >= 2, any move on the same face is PRUNED.
    """
    if last_move is None:
        return False
    if move[0] != last_move[0]:
        return False
    # Same face
    is_prime_last = "'" in last_move
    is_prime_curr = "'" in move
    if is_prime_last != is_prime_curr:
        # Immediate inverse (e.g. R followed by R', or R R followed by R')
        return True
    if run_length >= 2:
        # 3rd consecutive turn in same direction (e.g. R R R)
        return True
    return False


def get_successors_pruned(
    state: State, last_move: str | None, run_length: int = 1
) -> list[tuple[str, State]]:
    """
    Return successors with sound QTM move-sequence pruning for V3 BFS.

    - If last_move is None: returns all 6 moves.
    - If run_length == 1: drops immediate inverse (5 moves returned).
    - If run_length >= 2: drops all moves on the same face (4 moves returned).
    """
    result = []
    for move_name in MOVE_NAMES:
        if is_move_pruned(move_name, last_move, run_length):
            continue
        result.append((move_name, apply_move(state, move_name)))
    return result


def _same_face(m1: str, m2: str) -> bool:
    """Return True if two moves are on the same face."""
    face1 = m1.replace("'", "")
    face2 = m2.replace("'", "")
    return face1 == face2
