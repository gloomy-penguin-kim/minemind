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
        
        moves,_ = apply_rules([comp], board, stop_after_one=False)   
        moves = sorted(moves, key=lambda x: (x.r, x.c, x.kind)) 

        print(moves) 
        # Expect cells with local indices 1 and 2: gids 1 and 2 -> (r,c) 
        m1 = Move(r=0, c=1, action=Action.OPEN)
        m2 = Move(r=1, c=0, action=Action.OPEN)
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0]))
        self.assertTrue(self.compare_move_r_c_kind(m2, moves[1]))
 

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

        m1 = Move(0, 1, Action.OPEN)
        m2 = Move(1, 0, Action.OPEN) 
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
        m1 = Move(0, 0, Action.FLAG)
        m2 = Move(1, 1, Action.FLAG) 
        self.assertTrue(self.compare_move_r_c_kind(m1, moves[0]))
        self.assertTrue(self.compare_move_r_c_kind(m2, moves[1]))

 