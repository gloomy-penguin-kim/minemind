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

    b.is_mine[0][0] = True
    b.is_mine[0][1] = True   

    solver = Solver(b)
    query  = solver.chords()  

    assert len(query.revealed) == 1 
    assert (1,1) in query

def test_chord_find_chords():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,1],
             [0,2,1],
             [0,0,0]]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    b.revealed[1][2] = True

    b.flagged[0][0] = True
    b.flagged[0][1] = True   

    b.is_mine[0][0] = True
    b.is_mine[0][1] = True   

    solver = Solver(b)
    query  = solver.chords()  
    
    assert len(query) == 2 
    assert (1,1) in query
    assert (1,2) in query
 


def test_chord_requires_exact_flag_count():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,0],
            [0,2,0],
            [0,0,0]]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    b.flagged[0][0] = True  # only 1 flag, need 2

    cs = b.chord(1,1)
    assert cs.revealed == set()


def test_chord_opens_unknown_neighbors_when_flags_match():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,0],
            [0,2,0],
            [0,0,0]]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    b.flagged[0][0] = True
    b.flagged[0][1] = True  # now flagged==2

    # pretend all other neighbors are safe (they are)
    cs = b.chord(1,1)
    # it should have revealed at least one neighbor (exact count depends on reveal_cell flood rules)
    assert len(cs.revealed) > 0
