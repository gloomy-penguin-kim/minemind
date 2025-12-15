from core.generator import * 
from core.board import Board 


def test_first_click_places_mines_and_is_safe():
    b = Board(rows=9, cols=9, num_mines=10, seed=0)
    assert not b.mines_placed
    cs = b.reveal_cell(3, 3)

    assert b.mines_placed
    assert b.revealed[3][3] is True
    assert b.is_mine[3][3] is False
    assert (3, 3) in cs.revealed
    assert not cs.flagged


def test_reveal_already_revealed_is_noop():
    b = Board(9, 9, 10, seed=0)
    b.reveal_cell(3, 3)
    before = b.count_revealed_cells()
    cs = b.reveal_cell(3, 3)

    assert cs.revealed == set()
    assert cs.flagged == set()
    assert b.count_revealed_cells() == before


def test_reveal_flagged_is_noop():
    b = Board(9, 9, 10, seed=0)
    b.reveal_cell(3, 3)
    b.flagged[0][0] = True  # or b.apply(Action.FLAG,0,0) later
    cs = b.reveal_cell(0, 0)

    assert cs.revealed == set()


def test_mine_click_sets_game_over():
    b = Board(2, 2, 1, seed=0)
    b.mines_placed = True
    b.is_mine = [[True, False],
                [False, False]]
    b.adj = [[-1, 1],
            [1, 1]]

    cs = b.reveal_cell(0, 0)

    b.render_board() 

    assert (0, 0) in cs.revealed
    assert cs.game_over is True
    assert cs.win is False
    assert b.win is False
    
    assert b.game_over is True


def test_flood_reveal_zero_region():
    b = Board(3, 3, 0, seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,0],
            [0,0,0],
            [0,0,0]]
    b._remaining_safe = 9

    cs = b.reveal_cell(1, 1)
    assert len(cs.revealed) == 9
    assert b.count_revealed_cells() == 9
    assert b.game_over is True
    assert b.win is True


def test_win_autoflags_remaining_unrevealed():
    b = Board(2, 2, 1, seed=0)
    b.mines_placed = True
    b.is_mine = [[True, False],
                [False, False]]
    b.adj = [[0,1],
            [1,1]]
    b._remaining_safe = 3

    # reveal all safes
    b.reveal_cell(0, 1)
    b.reveal_cell(1, 0)
    cs = b.reveal_cell(1, 1)

    assert b.win is True
    assert b.game_over is True
    # the only unrevealed is the mine, should be flagged
    assert b.flagged[0][0] is True
    assert (0,0) in cs.flagged


def test_toggle_flag_on_revealed_is_noop():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0]*3 for _ in range(3)]
    b._remaining_safe = 9

    b.revealed[1][1] = True
    cs = b.toggle_flag(1,1)

    assert cs.flagged == set()
    assert b.flagged[1][1] is False


def test_toggle_flag_flips():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0]*3 for _ in range(3)]
    b._remaining_safe = 9

    cs1 = b.toggle_flag(2,2)
    assert b.flagged[2][2] is True
    assert cs1.flagged == {(2,2)}

    cs2 = b.toggle_flag(2,2)
    assert b.flagged[2][2] is False
    assert cs2.flagged == {(2,2)}


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


def test_flood_reveal_only_zero_region():
    b = Board(3,3,0,seed=0)
    b.mines_placed = True
    b.is_mine = [[False]*3 for _ in range(3)]
    b.adj = [[0,0,1],
            [0,1,1],
            [1,1,1]]
    b._remaining_safe = 9

    revealed = b._flood_reveal(0,0)

    assert (0,0) in revealed
    assert (1,0) in revealed
    assert (0,1) in revealed
    assert (2,2) not in revealed
