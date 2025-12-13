# first-click-safe mine placement, neighbor counts
 
from typing import Tuple 
from core.rng import RNG 

def generate_board(
    rows: int,
    cols: int,
    num_mines: int,
    seed: int,
    first_click: Tuple[int, int],
) : 
    """
    this generates a random board with the number of rows, cols, mines, seed,
    and first click data.  that is all used as a hash in RNG() 
    """
    r0, c0 = first_click

    # generate the random rng
    rng = RNG(seed, rows, cols, num_mines, r0, c0)
  
    # the initial click area must be free of mines 
    forbidden = set()
    forbidden.add((r0, c0))
    for nr, nc in _neighbors(rows, cols, r0, c0):
        forbidden.add((nr, nc))

    # gather candidates (everything else) 
    candidates = [
        (r, c) for r in range(rows) for c in range(cols)
        if (r, c) not in forbidden
    ]

    if num_mines > len(candidates):
        raise ValueError("Too many mines for given board size and safe zone")

    # "randomly" choose mine locations using seeded RNG 
    # this shuffle is nessary apparently to get the same board every time 
    rng.shuffle(candidates)
    mine_cells = set(candidates[:num_mines])
 
    is_mine = [[False] * cols for _ in range(rows)]
    for r, c in mine_cells:
        is_mine[r][c] = True
 
    adj = _generate_adj_array(rows, cols, is_mine) 

    return is_mine, adj 


def _generate_adj_array(rows, cols, is_mine): 
    adj = [[0] * cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            if is_mine[r][c]:
                adj[r][c] = -1  # mark mines as -1
            else:
                count = 0
                for nr, nc in _neighbors(rows, cols, r, c):
                    if is_mine[nr][nc]:
                        count += 1
                adj[r][c] = count
    return adj 


def _neighbors(rows:int, cols:int, r: int, c: int):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc