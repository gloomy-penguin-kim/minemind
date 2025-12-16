import unittest 

from core.board import Board
from analysis.frontier.component import Component
from analysis.frontier.constraint import Constraint 
from analysis.rules.move import Move, MoveList
 

from analysis.rules.singles import _apply_singles
from analysis.rules.subsets import _apply_subset
from analysis.rules.equivalence import _apply_equivalence 
from analysis.rules.rules import apply_rules 
from core.constants import Action 

 

class DummyBoard:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.revealed = [[False for _ in range(cols)] for _ in range(rows)]
        self.flagged = [[False for _ in range(cols)] for _ in range(rows)]



class TestRules(unittest.TestCase):

    def compare_move_r_c_kind(self, move1, move2): 
        self.assertTrue(isinstance(move1, Move))
        self.assertTrue(isinstance(move2, Move))
        return move1.r == move2.r and move1.c == move2.c and move1.action == move2.action #and move1.reason == move2.reason 
 
 
    def test_apply_subset_A_subset_B_same_remaining_marks_difference_safe(self):
        """
        A ⊂ B and a == b (is a subset of)
        all cells in B\\A are SAFE.
        """
        
        board = DummyBoard(rows=2, cols=2)

        comp = Component(
            k=4, 
            local_to_global=[0, 1, 2, 3],
            constraints=[
                # scope = {local 1, 2} 
                Constraint(mask_local=(1 << 0) | (1 << 1), 
                           mask_global=(1 << 16) | (1 << 17),
                           remaining=2),
                Constraint(mask_local=(1 << 0) | (1 << 1) | (1 << 2), 
                           mask_global=(1 << 16) | (1 << 17) | (1 << 18),
                           remaining=2),
            ],
        )  
 
        moves = MoveList(one=False) 
        _apply_subset(comp, board, moves, stop_after_one=False)
        moves,_ = moves.get_arrays() 
 
        self.assertTrue(len(moves)>0)

        # B\A = {local 2} -> localid 2 -> (1,0) 
        m1 = Move(1, 0, Action.OPEN) 
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0])) 


    def test_apply_subset_A_subset_B_same_remaining_marks_difference_mine(self):
        """
        A ⊂ B and a == b (is a subset of)
        all cells in B\\A are MINES
        """
        board = DummyBoard(rows=2, cols=2)

        comp = Component(
            k=4, 
            local_to_global=[0, 1, 2, 3],
            constraints=[
                # scope = {local 1, 2} 
                Constraint(mask_local=(1 << 0) | (1 << 1), 
                           mask_global=(1 << 16) | (1 << 17),
                           remaining=1),
                Constraint(mask_local=(1 << 0) | (1 << 1) | (1 << 2), 
                           mask_global=(1 << 16) | (1 << 17) | (1 << 18),
                           remaining=2),
            ],
        )  
 
        moves = MoveList(one=False) 
        _apply_subset(comp, board, moves, stop_after_one=False)
        moves,_ = moves.get_arrays() 

        self.assertTrue(len(moves)>0)

        # B\A = {local 2} -> localid 2 -> (1,0)
        m1 = Move(1, 0, Action.FLAG)  
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0])) 
