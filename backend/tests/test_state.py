"""
Unit tests for cube state representation.
Tests cover: solved state, validation, orientation sum invariant,
hashing, equality, and sticker grid conversion.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from cube.state import (
    SOLVED_STATE, SOLVED_PERM, SOLVED_ORIENT,
    make_state, solved_state, is_valid_state, is_solved,
    is_valid_perm, is_valid_orient, is_valid_orient_sum,
    state_hash, states_equal, state_to_sticker_grid, describe_state,
    COLOR_WHITE, COLOR_YELLOW, COLOR_GREEN, COLOR_BLUE, COLOR_RED, COLOR_ORANGE,
    FACE_U, FACE_D, FACE_F, FACE_B, FACE_R, FACE_L
)


class TestSolvedState:
    def test_solved_state_perm(self):
        s = solved_state()
        assert s[0] == (0, 1, 2, 3, 4, 5, 6)

    def test_solved_state_orient(self):
        s = solved_state()
        assert s[1] == (0, 0, 0, 0, 0, 0, 0)

    def test_is_solved(self):
        assert is_solved(SOLVED_STATE)

    def test_is_valid(self):
        assert is_valid_state(SOLVED_STATE)

    def test_orientation_sum_zero(self):
        _, orient = SOLVED_STATE
        assert sum(orient) % 3 == 0


class TestValidation:
    def test_valid_perm(self):
        assert is_valid_perm((0, 1, 2, 3, 4, 5, 6))

    def test_invalid_perm_duplicate(self):
        assert not is_valid_perm((0, 1, 2, 3, 4, 5, 5))  # duplicate

    def test_invalid_perm_wrong_range(self):
        assert not is_valid_perm((0, 1, 2, 3, 4, 5, 7))  # 7 not valid

    def test_invalid_perm_too_short(self):
        assert not is_valid_perm((0, 1, 2))

    def test_valid_orient(self):
        assert is_valid_orient((0, 1, 2, 0, 1, 2, 0))

    def test_invalid_orient_out_of_range(self):
        assert not is_valid_orient((0, 1, 2, 3, 0, 0, 0))  # 3 is invalid

    def test_valid_orient_sum(self):
        assert is_valid_orient_sum((0, 0, 0, 0, 0, 0, 0))
        assert is_valid_orient_sum((1, 1, 1, 0, 0, 0, 0))
        assert is_valid_orient_sum((2, 2, 2, 0, 0, 0, 0))

    def test_invalid_orient_sum(self):
        assert not is_valid_orient_sum((1, 0, 0, 0, 0, 0, 0))  # sum=1
        assert not is_valid_orient_sum((0, 1, 0, 0, 0, 0, 0))  # sum=1

    def test_invalid_state_bad_orient_sum(self):
        bad = make_state((0,1,2,3,4,5,6), (1,0,0,0,0,0,0))
        assert not is_valid_state(bad)


class TestHashingAndEquality:
    def test_hash_deterministic(self):
        s = SOLVED_STATE
        assert state_hash(s) == state_hash(s)

    def test_equal_states_same_hash(self):
        s1 = make_state((0,1,2,3,4,5,6),(0,0,0,0,0,0,0))
        s2 = make_state((0,1,2,3,4,5,6),(0,0,0,0,0,0,0))
        assert states_equal(s1, s2)
        assert state_hash(s1) == state_hash(s2)

    def test_different_states_not_equal(self):
        s1 = SOLVED_STATE
        s2 = make_state((1,0,2,3,4,5,6),(0,0,0,0,0,0,0))
        assert not states_equal(s1, s2)

    def test_state_usable_as_dict_key(self):
        d = {SOLVED_STATE: "solved"}
        assert d[SOLVED_STATE] == "solved"

    def test_state_usable_in_set(self):
        s = {SOLVED_STATE}
        assert SOLVED_STATE in s


class TestStickerGrid:
    def test_solved_state_u_face_all_white(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_WHITE for c in grid[FACE_U])

    def test_solved_state_d_face_all_yellow(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_YELLOW for c in grid[FACE_D])

    def test_solved_state_f_face_all_green(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_GREEN for c in grid[FACE_F])

    def test_solved_state_b_face_all_blue(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_BLUE for c in grid[FACE_B])

    def test_solved_state_r_face_all_red(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_RED for c in grid[FACE_R])

    def test_solved_state_l_face_all_orange(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert all(c == COLOR_ORANGE for c in grid[FACE_L])

    def test_grid_has_6_faces(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        assert len(grid) == 6

    def test_grid_each_face_has_4_stickers(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        for face in grid:
            assert len(face) == 4

    def test_grid_no_none_values(self):
        grid = state_to_sticker_grid(SOLVED_STATE)
        for face in grid:
            assert None not in face

    def test_grid_total_sticker_counts(self):
        """Each colour should appear exactly 4 times."""
        from collections import Counter
        grid = state_to_sticker_grid(SOLVED_STATE)
        flat = [s for face in grid for s in face]
        counts = Counter(flat)
        for colour in range(6):
            assert counts[colour] == 4, f"Colour {colour} appears {counts[colour]} times"
