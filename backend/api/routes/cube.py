"""
Cube state API routes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from cube.state import (
    SOLVED_STATE, make_state, is_valid_state, is_solved,
    state_to_sticker_grid, describe_state, COLOR_HEX, FACE_NAMES
)
from cube.moves import apply_move, apply_moves, MOVE_NAMES, get_successors

router = APIRouter()


class StateModel(BaseModel):
    perm: List[int]
    orient: List[int]


class MoveRequest(BaseModel):
    perm: List[int]
    orient: List[int]
    move: str


class MoveSequenceRequest(BaseModel):
    perm: List[int]
    orient: List[int]
    moves: List[str]


def state_to_response(state):
    perm, orient = state
    grid = state_to_sticker_grid(state)
    return {
        "perm":        list(perm),
        "orient":      list(orient),
        "is_solved":   is_solved(state),
        "is_valid":    is_valid_state(state),
        "sticker_grid": grid,
        "sticker_colors": [
            [COLOR_HEX[c] for c in face]
            for face in grid
        ],
        "face_names":  FACE_NAMES,
    }


@router.get("/solved")
def get_solved_state():
    """Return the solved state."""
    return state_to_response(SOLVED_STATE)


@router.post("/apply-move")
def apply_single_move(req: MoveRequest):
    """Apply a single move to a state."""
    if req.move not in MOVE_NAMES:
        raise HTTPException(400, f"Invalid move '{req.move}'. Valid: {MOVE_NAMES}")
    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        raise HTTPException(400, "Invalid cube state")
    new_state = apply_move(state, req.move)
    return state_to_response(new_state)


@router.post("/apply-moves")
def apply_move_sequence(req: MoveSequenceRequest):
    """Apply a sequence of moves to a state."""
    for m in req.moves:
        if m not in MOVE_NAMES:
            raise HTTPException(400, f"Invalid move '{m}'. Valid: {MOVE_NAMES}")
    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        raise HTTPException(400, "Invalid cube state")
    new_state = apply_moves(state, req.moves)
    return state_to_response(new_state)


@router.post("/validate")
def validate_state(req: StateModel):
    """Validate a cube state."""
    state = make_state(tuple(req.perm), tuple(req.orient))
    return {
        "is_valid": is_valid_state(state),
        "is_solved": is_solved(state),
        "describe": describe_state(state),
    }


@router.post("/successors")
def get_state_successors(req: StateModel):
    """Return all successor states from a given state."""
    state = make_state(tuple(req.perm), tuple(req.orient))
    if not is_valid_state(state):
        raise HTTPException(400, "Invalid cube state")
    succs = get_successors(state)
    return {
        "successors": [
            {"move": m, **state_to_response(s)}
            for m, s in succs
        ]
    }


@router.get("/scramble/{n}")
def get_random_scramble(n: int = 10, seed: int = None):
    """Generate a random scramble of n moves."""
    import random
    if seed is not None:
        random.seed(seed)
    moves = []
    last = None
    from cube.moves import _same_face
    for _ in range(n):
        choices = [m for m in MOVE_NAMES if last is None or not _same_face(m, last)]
        m = random.choice(choices)
        moves.append(m)
        last = m
    state = apply_moves(SOLVED_STATE, moves)
    return {
        "scramble_moves": moves,
        **state_to_response(state)
    }
