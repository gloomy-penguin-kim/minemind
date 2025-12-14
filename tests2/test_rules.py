import unittest 

from core.board import Board
from core.frontier import Component, Constraint
from core.move import Move 


import unittest

from core.rules import (
    SAFE,
    MINE,
    MoveList,
    _apply_singles,
    _apply_subset,
    apply_rules,
)
from core.utility import get_indicies_from_bitmask

 

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
        return move1.r == move2.r and move1.c == move2.c and move1.kind == move2.kind #and move1.reason == move2.reason 

    def test_singles_marks_scope_safe_when_remaining_zero(self):
        # 2x2 board -> gids: (0,0)=0, (0,1)=1, (1,0)=2, (1,1)=3
        board = Board(rows=2, cols=2, num_mines=1)

        # local indices 0,1,2,3 map directly to gids 0,1,2,3
        comp = Component(
            k=0,  # dummy number
            local_to_global=[0, 1, 2, 3],
            constraints=[
                # scope = {1,2} -> mask 0b0110
                Constraint(mask_local=(1 << 1) | (1 << 2), 
                           mask_global=(1 << 55) | (1 << 56), 
                           remaining=0),
            ],
        )
        
        moves, _= apply_rules(comp, board, stop_after_one=False)  

        moves = sorted(moves, key=lambda x: (x.r, x.c, x.kind))

        # Expect cells with local indices 1 and 2: gids 1 and 2 -> (r,c) 
        m1 = Move(0, 1, SAFE)
        m2 = Move(1, 0, SAFE) 
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0]))
        self.assertTrue(self.compare_move_r_c_kind(m2, moves[1]))
 

    def test_get_indices_from_mask(self):
        # mask: bits at indices 1, 2, 4 set
        mask = (1 << 1) | (1 << 2) | (1 << 4)
        indices = get_indicies_from_bitmask(mask)

        self.assertEqual(sorted(indices), [1, 2, 4])  


    def test_apply_singles_marks_scope_safe_when_remaining_zero(self):
        """
        remaining == 0 
        all cells in scope become SAFE.
        """ 
        board = DummyBoard(rows=2, cols=2)

        comp = Component(
            k=4, 
            local_to_global=[0, 1, 2, 3],
            constraints=[
                # scope = {local 1, 2}  
                Constraint(mask_local=(1 << 1) | (1 << 2), 
                           mask_global=(1 << 16) | (1 << 17),
                           remaining=0),
            ],
        )
 
        moves = MoveList() 
        _apply_singles(comp, board, moves, stop_after_one=False)

        moves,_ = moves.get_arrays()

        moves = sorted(moves, key=lambda x: (x.r, x.c, x.kind))

        self.assertTrue(len(moves) > 0 ) 

        m1 = Move(0, 1, SAFE)
        m2 = Move(1, 0, SAFE) 
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0]))
        self.assertTrue(self.compare_move_r_c_kind(m2, moves[1]))


    def test_apply_singles_marks_scope_mine_when_remaining_equals_scope_size(self):
        """
        remaining == |scope|  
        all cells in scope become MINES.
        """ 
        board = DummyBoard(rows=2, cols=2)

        comp = Component(
            k=4, 
            local_to_global=[0, 1, 2, 3],
            constraints=[
                # scope = {local 1, 2} 
                Constraint(mask_local=(1 << 0) | (1 << 3), 
                           mask_global=(1 << 16) | (1 << 17),
                           remaining=2),
            ],
        ) 

        moves = MoveList(one=False) 
        _apply_singles(comp, board, moves, stop_after_one=False)

        moves,_ = moves.get_arrays()

        self.assertTrue(len(moves)>0) 

        moves = sorted(moves, key=lambda x: (x.r, x.c, x.kind))

        # local 0 -> gid 0 -> (0,0)
        # local 3 -> gid 3 -> (1,1) 
        m1 = Move(0, 0, MINE)
        m2 = Move(1, 1, MINE) 
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0]))
        self.assertTrue(self.compare_move_r_c_kind(m2, moves[1]))


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
        m1 = Move(1, 0, SAFE) 
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
        m1 = Move(1, 0, MINE)  
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0])) 

 
if __name__ == "__main__":
    unittest.main()
