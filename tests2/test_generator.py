import unittest

from core.generator import generate_board

import random
import json 


class TestGenerater(unittest.TestCase):

    def test_same_seed_same_first_click_same_board(self):
        rows, cols, num_mines = 9, 9, 10
        seed = 42
        first_click = (3, 3)

        is_mine1, adj1 = generate_board(rows, cols, num_mines, seed, first_click)
        is_mine2, adj2 = generate_board(rows, cols, num_mines, seed, first_click)

        # Boards should be exactly the same
        self.assertEqual(is_mine1, is_mine2)
        self.assertEqual(adj1, adj2)

    def test_different_seed_changes_layout_seed(self):
        rows, cols, num_mines = 9, 9, 10
        first_click = (3, 3)

        is_mine1, adj1 = generate_board(rows, cols, num_mines, seed=1, first_click=first_click)
        is_mine2, adj2 = generate_board(rows, cols, num_mines, seed=2, first_click=first_click)

        self.assertNotEqual(is_mine1, is_mine2) 

    def test_different_seed_changes_layout_first_click(self):
        rows, cols, num_mines = 9, 9, 10
        seed = 42

        first_click = (3, 3)
        second_click = (3, 4)

        is_mine1, adj1 = generate_board(rows, cols, num_mines, seed=seed, first_click=first_click)
        is_mine2, adj2 = generate_board(rows, cols, num_mines, seed=seed, first_click=second_click)

        self.assertNotEqual(is_mine1, is_mine2) 

    
    def test_first_click_region_is_safe_200(self): 
        for _ in range(200):  
            rows, cols = random.randint(9, 30), random.randint(9,16)
            num_mines = int((rows * cols) * 0.15)
            seed = 42

            first_click = (random.randint(0,rows-1), random.randint(0,cols-1))

            is_mine, adj = generate_board(rows, cols, num_mines, seed, first_click)

            r0, c0 = first_click

            # helper for neighbors
            def neighbors(r, c):
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            yield nr, nc

            # The first-click and all its neighbors must NOT be mines
            safe_cells = [(r0, c0)] + list(neighbors(r0, c0))
            for r, c in safe_cells:
                self.assertFalse(
                    is_mine[r][c],
                    msg=f"Cell {(r, c)} should be safe around first click {first_click}",
            )


    def test_mine_count_is_correct(self):
        rows, cols, num_mines = 9, 9, 10
        seed = 123
        first_click = (0, 0)

        is_mine, adj = generate_board(rows, cols, num_mines, seed, first_click)

        # Count total mines
        count = sum(1 for r in range(rows) for c in range(cols) if is_mine[r][c])
        self.assertEqual(count, num_mines)


    def test_9x9_10_mines_click_3_3_board_no_seed(self):
        #     0  1  2  3  4  5  6  7  8
        #  0  *  3  *  1     1  1  1    
        #  1  *  5  2  1     1  *  1    
        #  2  *  *  2        1  1  1    
        #  3  3  *  2              1  1 
        #  4  1  1  1              2  * 
        #  5                       2  * 
        #  6           1  1  1     1  1 
        #  7           1  *  1          
        #  8           1  1  1        
 
        rows, cols, num_mines = 9, 9, 10
        seed = 0 
        first_click = (3, 3)  

        is_mine, adj = generate_board(
            rows=rows,
            cols=cols,
            num_mines=num_mines,
            seed=seed,
            first_click=first_click,
        )

        with open("./tests/test_board.json", 'r') as f: 
            obj = json.load(f) 
 
        self.assertEqual(is_mine, obj["is_mine"])
        self.assertEqual(adj, obj["adj"])


if __name__ == "__main__":
    unittest.main()
