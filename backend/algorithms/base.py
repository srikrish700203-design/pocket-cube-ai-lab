"""
Base types and utilities shared across all search algorithms.
"""
from __future__ import annotations
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import List, Optional
from cube.state import State, SOLVED_STATE, is_solved
from cube.moves import MOVE_NAMES, apply_move, invert_sequence

@dataclass
class SearchResult:
    """Standardised result returned by every algorithm."""
    algorithm:         str
    found:             bool
    solution:          List[str]           # move sequence from start to goal
    solution_length:   int
    expanded_states:   int                 # states popped from frontier
    generated_states:  int                 # successor states created
    visited_states:    int                 # unique states put in visited set
    max_frontier_size: int
    peak_memory_kb:    float               # peak tracked memory in KB
    elapsed_ms:        float               # wall-clock time in milliseconds
    max_depth:         int                 # max depth reached
    extra:             dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "algorithm":         self.algorithm,
            "found":             self.found,
            "solution":          self.solution,
            "solution_length":   self.solution_length,
            "expanded_states":   self.expanded_states,
            "generated_states":  self.generated_states,
            "visited_states":    self.visited_states,
            "max_frontier_size": self.max_frontier_size,
            "peak_memory_kb":    self.peak_memory_kb,
            "elapsed_ms":        self.elapsed_ms,
            "max_depth":         self.max_depth,
            "extra":             self.extra,
        }


class SearchTimeout(Exception):
    pass


class MemoryLimit(Exception):
    pass


def reconstruct_path(parent: dict, start: State, goal: State) -> List[str]:
    """Reconstruct a move sequence from start to goal using the parent map."""
    path = []
    state = goal
    while state != start:
        move, prev = parent[state]
        path.append(move)
        state = prev
    path.reverse()
    return path
