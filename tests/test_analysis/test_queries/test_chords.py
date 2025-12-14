from core.board import Board
from solver.solver import Solver 

def test_chord_find_chords():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,0],
             [0,2,0],
             [0,0,0]]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    b.flagged[0][0] = True
    b.flagged[0][1] = True   

    solver = Solver(b)
    query  = solver.chords()  

    assert len(query.revealed) == 1 
    assert (1,1) in query

def test_chord_find_chords():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,0],
             [0,2,1],
             [0,0,0]]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    b.flagged[0][0] = True
    b.flagged[0][1] = True   

    solver = Solver(b)
    query  = solver.chords()  
    
    assert len(query.revealed) == 2 
    assert (1,1) in query
    assert (1,2) in query