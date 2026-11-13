"""
Pocket Cube (2×2) State Representation
=======================================

A state is represented as a pair (perm, orient) where:
  - perm  : tuple of 7 ints — the corner at each of the 7 movable slots
  - orient: tuple of 7 ints — the orientation (0, 1, 2) of each corner

Corner indices (slots):
  0 = UFL  (Upper-Front-Left)
  1 = UFR  (Upper-Front-Right)
  2 = UBR  (Upper-Back-Right)
  3 = UBL  (Upper-Back-Left)
  4 = DFL  (Down-Front-Left)
  5 = DFR  (Down-Front-Right)
  6 = DBR  (Down-Back-Right)
  7 = DBL  (Down-Back-Left)  ← FIXED reference corner, not stored

Orientation convention:
  A corner has orientation 0 if it is "correctly twisted" in its slot,
  meaning the U/D-colored sticker faces the U or D face.
  Orientation 1 means rotated 120° clockwise (from above).
  Orientation 2 means rotated 240° clockwise (from above).

Invariant:
  sum(orient[i] for all 8 corners) ≡ 0  (mod 3)
  Since the DBL corner is fixed and always has orientation 0,
  sum(orient[0:7]) ≡ 0  (mod 3).

Solved state:
  perm   = (0, 1, 2, 3, 4, 5, 6)
  orient = (0, 0, 0, 0, 0, 0, 0)
"""

from __future__ import annotations
from typing import Tuple

# Type alias for a cube state
Perm   = Tuple[int, ...]   # length 7
Orient = Tuple[int, ...]   # length 7
State  = Tuple[Perm, Orient]

SOLVED_PERM:   Perm   = (0, 1, 2, 3, 4, 5, 6)
SOLVED_ORIENT: Orient = (0, 0, 0, 0, 0, 0, 0)
SOLVED_STATE:  State  = (SOLVED_PERM, SOLVED_ORIENT)

# Human-readable corner names (indices 0-6; index 7 = DBL is fixed)
CORNER_NAMES = ["UFL", "UFR", "UBR", "UBL", "DFL", "DFR", "DBR", "DBL"]


# ---------------------------------------------------------------------------
# State construction helpers
# ---------------------------------------------------------------------------

def make_state(perm: Perm, orient: Orient) -> State:
    """Create a canonical state tuple, ensuring all values are native ints."""
    return (tuple(int(x) for x in perm), tuple(int(x) for x in orient))


def solved_state() -> State:
    """Return the solved state."""
    return (SOLVED_PERM, SOLVED_ORIENT)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def is_valid_perm(perm: Perm) -> bool:
    """Check that perm is a valid permutation of {0,1,2,3,4,5,6}."""
    return len(perm) == 7 and sorted(perm) == list(range(7))


def is_valid_orient(orient: Orient) -> bool:
    """Check that every orientation value is in {0, 1, 2}."""
    return len(orient) == 7 and all(o in (0, 1, 2) for o in orient)


def is_valid_orient_sum(orient: Orient) -> bool:
    """
    Check the orientation sum invariant.

    The sum of all 8 corner orientations must be ≡ 0 (mod 3).
    The DBL corner is always orientation 0, so we just check
    sum(orient[0:7]) ≡ 0 (mod 3).
    """
    return sum(orient) % 3 == 0


def is_valid_state(state: State) -> bool:
    """Full validation of a state."""
    perm, orient = state
    return (
        is_valid_perm(perm)
        and is_valid_orient(orient)
        and is_valid_orient_sum(orient)
    )


# ---------------------------------------------------------------------------
# State hashing and equality
# ---------------------------------------------------------------------------

def state_hash(state: State) -> int:
    """Hash a state for use in sets and dicts."""
    return hash(state)


def states_equal(a: State, b: State) -> bool:
    """Test state equality."""
    return a == b


def is_solved(state: State) -> bool:
    """Test whether a state is the solved state."""
    return state == SOLVED_STATE


# ---------------------------------------------------------------------------
# Sticker grid representation
# ---------------------------------------------------------------------------
# We use a 6-face, 4-sticker-per-face layout:
#   Face order: U, D, F, B, R, L
#   Sticker order within each face (looking at the face from outside):
#     [0] [1]
#     [2] [3]
#
# The 8 corners each contribute 3 stickers.  We define which (face, slot)
# corresponds to which corner index and which of its three sticker colours.
#
# Corner sticker mapping:
#   Each corner has 3 stickers in the order (U/D-face, F/B-face, R/L-face).
#
# Corner colour assignment in solved state:
#   The colour of a sticker = face colour of the face it sits on when solved.
#   Face colours: U=White(0), D=Yellow(1), F=Green(2), B=Blue(3), R=Red(4), L=Orange(5)
#
# Corner solved colours (3 stickers in order U/D, F/B, R/L):
#   UFL(0): White, Green,  Orange  (U, F, L)
#   UFR(1): White, Green,  Red     (U, F, R)
#   UBR(2): White, Blue,   Red     (U, B, R)
#   UBL(3): White, Blue,   Orange  (U, B, L)
#   DFL(4): Yellow,Green,  Orange  (D, F, L)
#   DFR(5): Yellow,Green,  Red     (D, F, R)
#   DBR(6): Yellow,Blue,   Red     (D, B, R)
#   DBL(7): Yellow,Blue,   Orange  (D, B, L)  ← fixed

FACE_U, FACE_D, FACE_F, FACE_B, FACE_R, FACE_L = 0, 1, 2, 3, 4, 5
COLOR_WHITE, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_RED, COLOR_ORANGE = 0,1,2,3,4,5

FACE_NAMES   = ["U", "D", "F", "B", "R", "L"]
COLOR_NAMES  = ["white", "yellow", "green", "blue", "red", "orange"]
COLOR_HEX    = ["#FFFFFF", "#FFD700", "#00C853", "#1565C0", "#E53935", "#FF6D00"]

# Solved corner colours: corner_index → (ud_color, fb_color, rl_color)
CORNER_SOLVED_COLORS = [
    (COLOR_WHITE,  COLOR_GREEN,  COLOR_ORANGE),  # 0 UFL
    (COLOR_WHITE,  COLOR_GREEN,  COLOR_RED),     # 1 UFR
    (COLOR_WHITE,  COLOR_BLUE,   COLOR_RED),     # 2 UBR
    (COLOR_WHITE,  COLOR_BLUE,   COLOR_ORANGE),  # 3 UBL
    (COLOR_YELLOW, COLOR_GREEN,  COLOR_ORANGE),  # 4 DFL
    (COLOR_YELLOW, COLOR_GREEN,  COLOR_RED),     # 5 DFR
    (COLOR_YELLOW, COLOR_BLUE,   COLOR_RED),     # 6 DBR
    (COLOR_YELLOW, COLOR_BLUE,   COLOR_ORANGE),  # 7 DBL (fixed)
]

# For each corner slot (0-6), and the fixed slot (7=DBL), define which
# (face_index, sticker_slot) each of the 3 stickers maps to.
# Sticker slot within a face:  TL=0, TR=1, BL=2, BR=3
#   U face viewed from above:  TL=UBL, TR=UBR, BL=UFL, BR=UFR
#   D face viewed from below:  TL=DFL, TR=DFR, BL=DBL, BR=DBR
#   F face viewed from front:  TL=UFL, TR=UFR, BL=DFL, BR=DFR
#   B face viewed from back:   TL=UBR, TR=UBL, BL=DBR, BR=DBL
#   R face viewed from right:  TL=UFR, TR=UBR, BL=DFR, BR=DBR
#   L face viewed from left:   TL=UBL, TR=UFL, BL=DBL, BR=DFL

# slot_on_face[slot_index] = (face, sticker_in_face)
# corner_sticker_positions[corner_slot] = [(face,pos) for ud,fb,rl]
CORNER_STICKER_POSITIONS = [
    # 0 UFL  ud=(U,BL=2), fb=(F,TL=0), rl=(L,TR=1)
    [(FACE_U, 2), (FACE_F, 0), (FACE_L, 1)],
    # 1 UFR  ud=(U,BR=3), fb=(F,TR=1), rl=(R,TL=0)
    [(FACE_U, 3), (FACE_F, 1), (FACE_R, 0)],
    # 2 UBR  ud=(U,TR=1), fb=(B,TL=0), rl=(R,TR=1)
    [(FACE_U, 1), (FACE_B, 0), (FACE_R, 1)],
    # 3 UBL  ud=(U,TL=0), fb=(B,TR=1), rl=(L,TL=0)
    [(FACE_U, 0), (FACE_B, 1), (FACE_L, 0)],
    # 4 DFL  ud=(D,TL=0), fb=(F,BL=2), rl=(L,BR=3)
    [(FACE_D, 0), (FACE_F, 2), (FACE_L, 3)],
    # 5 DFR  ud=(D,TR=1), fb=(F,BR=3), rl=(R,BL=2)
    [(FACE_D, 1), (FACE_F, 3), (FACE_R, 2)],
    # 6 DBR  ud=(D,BR=3), fb=(B,BL=2), rl=(R,BR=3)
    [(FACE_D, 3), (FACE_B, 2), (FACE_R, 3)],
    # 7 DBL  ud=(D,BL=2), fb=(B,BR=3), rl=(L,BL=2)  ← fixed
    [(FACE_D, 2), (FACE_B, 3), (FACE_L, 2)],
]


def state_to_sticker_grid(state: State) -> list[list[int]]:
    """
    Convert a cube state to a 6×4 sticker grid.

    Returns a list of 6 faces, each a list of 4 sticker colours.
    Face order: U, D, F, B, R, L
    Sticker order per face: [TL, TR, BL, BR]
    """
    grid = [[None] * 4 for _ in range(6)]
    perm, orient = state

    # Process the 7 movable corner slots
    for slot in range(7):
        piece = perm[slot]        # which physical corner is in this slot
        o = orient[slot]          # orientation of that piece in this slot

        # The 3 solved colours of the piece: (ud, fb, rl)
        base_colors = CORNER_SOLVED_COLORS[piece]

        # Apply orientation twist:
        # o=0 → no twist:    stickers go (ud, fb, rl)
        # o=1 → 1 CW twist:  stickers cycle to (rl, ud, fb)
        # o=2 → 2 CW twists: stickers cycle to (fb, rl, ud)
        twisted = (
            base_colors[o % 3],
            base_colors[(o + 1) % 3],
            base_colors[(o + 2) % 3],
        )

        # Place the stickers at the positions defined for this slot
        positions = CORNER_STICKER_POSITIONS[slot]
        for sticker_idx, (face, pos) in enumerate(positions):
            grid[face][pos] = twisted[sticker_idx]

    # Fixed DBL corner (slot 7, piece 7, orient 0)
    base_colors = CORNER_SOLVED_COLORS[7]
    positions = CORNER_STICKER_POSITIONS[7]
    for sticker_idx, (face, pos) in enumerate(positions):
        grid[face][pos] = base_colors[sticker_idx]

    return grid


# Mapping from the unordered 3-color set of a corner to its physical piece index
COLOR_SET_TO_PIECE = {
    frozenset(colors): piece for piece, colors in enumerate(CORNER_SOLVED_COLORS)
}


def sticker_grid_to_state(grid: list[list[int]]) -> State:
    """
    Decode a 6×4 sticker grid back to the canonical (perm, orient) state tuple.
    Inverts state_to_sticker_grid.
    """
    perm = []
    orient = []
    for slot in range(7):
        positions = CORNER_STICKER_POSITIONS[slot]
        actual_colors = tuple(grid[face][pos] for face, pos in positions)
        piece = COLOR_SET_TO_PIECE[frozenset(actual_colors)]
        perm.append(piece)
        base = CORNER_SOLVED_COLORS[piece]
        # Match twist in {0, 1, 2}
        twist = 0
        for t in (0, 1, 2):
            if (base[t % 3], base[(t + 1) % 3], base[(t + 2) % 3]) == actual_colors:
                twist = t
                break
        orient.append(twist)
    return make_state(tuple(perm), tuple(orient))


def describe_state(state: State) -> dict:
    """Return a human-readable description of a state."""
    perm, orient = state
    grid = state_to_sticker_grid(state)
    return {
        "perm": list(perm),
        "orient": list(orient),
        "is_solved": is_solved(state),
        "is_valid": is_valid_state(state),
        "orient_sum_mod3": sum(orient) % 3,
        "sticker_grid": grid,
        "corners": [
            {
                "slot": i,
                "slot_name": CORNER_NAMES[i],
                "piece": perm[i],
                "piece_name": CORNER_NAMES[perm[i]],
                "orientation": orient[i],
            }
            for i in range(7)
        ],
        "fixed_corner": {
            "slot": 7,
            "slot_name": "DBL",
            "piece": 7,
            "piece_name": "DBL",
            "orientation": 0,
        }
    }
