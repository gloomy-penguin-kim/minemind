import pytest

from analysis.rules.move import MoveList
from analysis.rules.equivalence import _apply_equivalence  # <- adjust import path
from analysis.frontier.component import Component, Constraint  # <- adjust if needed
from core.constants import Action


class DummyBoard:
    def __init__(self, rows=3, cols=3):
        self.rows = rows
        self.cols = cols
        self.revealed = [[False] * cols for _ in range(rows)]
        self.flagged = [[False] * cols for _ in range(rows)]


def test_apply_equivalence_subset_equal_remaining_marks_diff_safe_open():
    """
    A ⊂ B and rem(A)==rem(B) => B\\A are SAFE (Action.OPEN)
    Example:
      A = {0} rem=0
      B = {0,1} rem=0
      => diff = {1} should be OPEN at local index 1
    """
    board = DummyBoard(rows=3, cols=3)

    # local_to_global maps local indices -> global gid
    # gid = r*cols + c; choose:
    # local 0 -> gid 0 => (0,0)
    # local 1 -> gid 1 => (0,1)
    comp = Component(
        k=2,
        local_to_global=[0, 1],
        constraints=[
            Constraint(mask_local=0b01, mask_global=0b01, remaining=0),  # A={0}
            Constraint(mask_local=0b11, mask_global=0b11, remaining=0),  # B={0,1}
        ],
    )

    moves = MoveList(one=False)
    _apply_equivalence(comp, board, moves, stop_after_one=False)

    arr, conflicts = moves.get_arrays()
    assert conflicts == []

    # Expect exactly one move: OPEN (0,1)
    assert len(arr) == 1
    m = arr[0]
    assert (m.r, m.c) == (0, 1)
    assert m.action == Action.OPEN
    # for OPEN moves, your _process_moves_for_this_mask sets val=None
    assert m.val is None

    # sanity: reasons include "Equivalence"
    assert any("Equivalence" in line for line in m.reasons)


def test_apply_equivalence_skips_already_revealed_or_flagged_cells():
    """
    If the diff cell is already revealed/flagged, _process_moves_for_this_mask should skip it.
    """
    board = DummyBoard(rows=3, cols=3)
    board.revealed[0][1] = True  # diff target will be (0,1)

    comp = Component(
        k=2,
        local_to_global=[0, 1],
        constraints=[
            Constraint(mask_local=0b01, mask_global=0b01, remaining=0),
            Constraint(mask_local=0b11, mask_global=0b11, remaining=0),
        ],
    )

    moves = MoveList(one=False)
    _apply_equivalence(comp, board, moves, stop_after_one=False)

    arr, conflicts = moves.get_arrays()
    assert conflicts == []
    assert arr == []


def test_apply_equivalence_no_moves_when_remaining_not_equal():
    """
    A ⊂ B but rem(A)!=rem(B) => equivalence rule should NOT fire.
    """
    board = DummyBoard(rows=3, cols=3)

    comp = Component(
        k=2,
        local_to_global=[0, 1],
        constraints=[
            Constraint(mask_local=0b01, mask_global=0b01, remaining=0),  # A rem=0
            Constraint(mask_local=0b11, mask_global=0b11, remaining=1),  # B rem=1 (diff)
        ],
    )

    moves = MoveList(one=False)
    _apply_equivalence(comp, board, moves, stop_after_one=False)

    arr, conflicts = moves.get_arrays()
    assert conflicts == []
    assert arr == []


def test_apply_equivalence_stop_after_one_returns_after_first_add():
    """
    stop_after_one=True should exit immediately after it adds at least one move.
    """
    board = DummyBoard(rows=3, cols=3)

    # Make it so there are *two* equivalence opportunities, but we expect it to stop at first.
    # k=3 local indices: 0,1,2  -> gids 0,1,2 => (0,0), (0,1), (0,2)
    # constraints:
    #   A={0} rem=0
    #   B={0,1} rem=0  => adds OPEN at local 1
    #   C={0,2} rem=0  => would also add OPEN at local 2 (if it continued)
    comp = Component(
        k=3,
        local_to_global=[0, 1, 2],
        constraints=[
            Constraint(mask_local=0b001, mask_global=0b001, remaining=0),  # A
            Constraint(mask_local=0b011, mask_global=0b011, remaining=0),  # B (diff -> 1)
            Constraint(mask_local=0b101, mask_global=0b101, remaining=0),  # C (diff -> 2)
        ],
    )

    moves = MoveList(one=False)
    _apply_equivalence(comp, board, moves, stop_after_one=True)

    arr, conflicts = moves.get_arrays()
    assert conflicts == []
    assert len(arr) == 1
    assert (arr[0].r, arr[0].c) in {(0, 1), (0, 2)}  # whichever it hits first
    assert arr[0].action == Action.OPEN
