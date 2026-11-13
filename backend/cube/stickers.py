"""
24-Sticker Array Representation and Operations for 2x2 Pocket Cube
==================================================================
Used by Stage 1 (V1 Unpruned DFS) to demonstrate the naive, physical
sticker-based state representation as explicitly required by the assignment.

Face Order (6 faces x 4 stickers = 24 stickers):
  0: U (Up,    stickers 0..3)   - Color 0 (White)
  1: D (Down,  stickers 4..7)   - Color 1 (Yellow)
  2: F (Front, stickers 8..11)  - Color 2 (Green)
  3: B (Back,  stickers 12..15) - Color 3 (Blue)
  4: R (Right, stickers 16..19) - Color 4 (Red)
  5: L (Left,  stickers 20..23) - Color 5 (Orange)

Sticker positions on each face (viewed directly from outside):
  [0: TL] [1: TR]
  [2: BL] [3: BR]
"""

from __future__ import annotations
from typing import List, Tuple, Sequence, Dict

# Face indices
FACE_U, FACE_D, FACE_F, FACE_B, FACE_R, FACE_L = 0, 1, 2, 3, 4, 5

# Color indices and names
COLOR_WHITE, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_RED, COLOR_ORANGE = 0, 1, 2, 3, 4, 5
COLOR_NAMES = ["white", "yellow", "green", "blue", "red", "orange"]

# Solved 24-sticker configuration
SOLVED_STICKER_LIST: List[int] = [
    0, 0, 0, 0,  # U (White)
    1, 1, 1, 1,  # D (Yellow)
    2, 2, 2, 2,  # F (Green)
    3, 3, 3, 3,  # B (Blue)
    4, 4, 4, 4,  # R (Red)
    5, 5, 5, 5,  # L (Orange)
]
SOLVED_STICKERS: Tuple[int, ...] = tuple(SOLVED_STICKER_LIST)

# Move names for V1 (6 standard quarter-turns)
V1_MOVE_NAMES: Tuple[str, ...] = ("U", "U'", "R", "R'", "F", "F'")

# Exact 24-sticker permutation maps for each move.
# P[dst] = src, meaning new_stickers[dst] = old_stickers[src].
STICKER_MOVE_PERM: Dict[str, Tuple[int, ...]] = {
    "U":  (2, 0, 3, 1, 4, 5, 6, 7, 9, 12, 10, 11, 13, 8, 14, 15, 17, 20, 18, 19, 21, 16, 22, 23),
    "U'": (1, 3, 0, 2, 4, 5, 6, 7, 13, 8, 10, 11, 9, 12, 14, 15, 21, 16, 18, 19, 17, 20, 22, 23),
    "R":  (0, 16, 2, 11, 4, 19, 6, 12, 8, 18, 10, 7, 3, 13, 17, 15, 5, 9, 14, 1, 20, 21, 22, 23),
    "R'": (0, 19, 2, 12, 4, 16, 6, 11, 8, 17, 10, 3, 7, 13, 18, 15, 1, 14, 9, 5, 20, 21, 22, 23),
    "F":  (0, 1, 10, 21, 18, 9, 6, 7, 23, 2, 5, 16, 12, 13, 14, 15, 8, 17, 3, 19, 20, 4, 22, 11),
    "F'": (0, 1, 9, 18, 21, 10, 6, 7, 16, 5, 2, 23, 12, 13, 14, 15, 11, 17, 4, 19, 20, 3, 22, 8),
}

MOVE_INVERSES: Dict[str, str] = {
    "U": "U'", "U'": "U",
    "R": "R'", "R'": "R",
    "F": "F'", "F'": "F",
}


def apply_sticker_move(stickers: Sequence[int], move: str) -> List[int]:
    """
    Apply a quarter-turn move directly to a 24-sticker array.
    Does NOT use compact cubie tuples or external move functions.
    """
    perm = STICKER_MOVE_PERM[move]
    return [stickers[perm[i]] for i in range(24)]


def apply_sticker_moves(stickers: Sequence[int], moves: Sequence[str]) -> List[int]:
    """Apply a sequence of moves to a 24-sticker array."""
    curr = list(stickers)
    for m in moves:
        curr = apply_sticker_move(curr, m)
    return curr


def is_sticker_solved(stickers: Sequence[int]) -> bool:
    """
    Check if the 24-sticker array is solved.
    The cube is solved if each of the 6 faces has all 4 stickers of the same colour,
    matching the solved orientation.
    """
    # Direct check against solved sticker array
    for i in range(24):
        if stickers[i] != SOLVED_STICKER_LIST[i]:
            return False
    return True


def make_solved_stickers() -> List[int]:
    """Return a fresh mutable 24-element list of solved stickers."""
    return list(SOLVED_STICKER_LIST)


def copy_stickers(stickers: Sequence[int]) -> List[int]:
    """Return a deep copy of a 24-element sticker array."""
    return list(stickers)


# ---------------------------------------------------------------------------
# Boundary converters (Used only when bridging between representations
# at API boundaries, NEVER inside V1's recursive DFS search)
# ---------------------------------------------------------------------------

def state_to_sticker_array(state: Tuple) -> List[int]:
    """Convert a compact (perm, orient) state to a 24-element sticker list."""
    from .state import state_to_sticker_grid
    grid = state_to_sticker_grid(state)
    return [grid[face][pos] for face in range(6) for pos in range(4)]


def sticker_array_to_state(stickers: Sequence[int]):
    """Convert a 24-element sticker list to a compact (perm, orient) state."""
    from .state import sticker_grid_to_state
    grid = [list(stickers[face * 4 : (face + 1) * 4]) for face in range(6)]
    return sticker_grid_to_state(grid)
