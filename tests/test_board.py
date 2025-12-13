import unittest

from core.generator import *  # update this import

import random
import json 

from core.board import Board 
from minemind.game import Game 

class TestBoard(unittest.TestCase):

    #     0  1  2  3  4  5  6  7  8
    #  0 *  3  *  1     1  1  1    
    #  1 *  5  2  1     1  *  1    
    #  2 *  *  2        1  1  1    
    #  3 3  *  2              1  1 
    #  4 1  1  1              2  * 
    #  5                      2  * 
    #  6          1  1  1     1  1 
    #  7          1  *  1          
    #  8          1  1  1        

    def test_initial_state(self):
        b = Board(rows=3, cols=3, num_mines=1, seed=42)
        self.assertFalse(b.mines_placed)
        self.assertFalse(b.game_over)
        self.assertFalse(b.win)
        self.assertEqual(b._remaining_safe, 3 * 3 - 1)
        # all cells unrevealed / unflagged
        for r in range(b.rows):
            for c in range(b.cols):
                self.assertFalse(b.revealed[r][c])
                self.assertFalse(b.flagged[r][c])


    def test_9x9_10_mines_click_3_3_board_0_seed(self):  
        rows, cols, num_mines = 9, 9, 10
        seed = 0  
 
        board = Board(rows, cols, num_mines, seed) 
        board.reveal_cell(3,3) 

        with open("./tests/test_board.json", 'r') as f: 
            obj = json.load(f) 
 
        self.assertEqual(board.is_mine, obj["is_mine"])
        self.assertEqual(board.adj, obj["adj"])


    def test_random_boards_property(self):  
        for _ in range(200): 
            rows, cols, num_mines = 9, 9, 10
            seed = random.randint(0,10000)
    
            board = Board(rows, cols, num_mines, seed) 
            board.reveal_cell(random.randint(0,8),random.randint(0,8)) 

            for i in range(rows): 
                for j in range(cols): 
                    if board.adj[i][j] > 0:
                        mines = 0 
                        for (nr, nc) in board.neighbors(i,j): 
                            if board.is_mine[nr][nc]: 
                                mines += 1  
                        self.assertEqual(mines, board.adj[i][j]) 


    def test_reveal_safe(self): 
        for _ in range(200): 
            rows, cols, num_mines = 9, 9, 10
            seed = random.randint(0,10000)

            board = Board(rows, cols, num_mines, seed) 
            board.reveal_cell(3, 3) 

            for i in range(rows): 
                for j in range(cols): 
                    if not board.is_mine[i][j]:
                        board.reveal_cell(i,j)
                        self.assertTrue(board.revealed[i][j])
                        self.assertFalse(board.is_mine[i][j])
                        self.assertFalse(board.flagged[i][j])


    def test_reveal_mine(self):  
        rows, cols, num_mines = 9, 9, 10
        seed = random.randint(0,10000)

        board = Board(rows, cols, num_mines, seed) 
        board.reveal_cell(3, 3)

        row, col = 0, 0
        for i in range(rows): 
            for j in range(cols): 
                if board.is_mine[i][j]:
                    row, col = i, j 
                    board.reveal_cell(i,j) 
                    break

        self.assertFalse(board.revealed[row][col]) 
        self.assertTrue(board.is_mine[row][col]) 
        self.assertTrue(board.game_over)  
        self.assertFalse(board.win)  


    def test_reveal_flag(self):      
        rows, cols, num_mines = 9, 9, 10
        seed = random.randint(0,10000)

        board = Board(rows, cols, num_mines, seed) 
        board.reveal_cell(3, 3)

        for i in range(rows): 
            for j in range(cols):  
                if board.is_mine[i][j]:
                    board.toggle_flag(i,j)
                    self.assertFalse(board.revealed[i][j]) 
                    self.assertTrue(board.flagged[i][j])
                    board.set_flag(i,j,True)
                    self.assertFalse(board.revealed[i][j]) 
                    self.assertTrue(board.flagged[i][j])
                    break 

        self.assertFalse(board.game_over)  
        self.assertFalse(board.win)  


    def test_flood_reveal_zero_region(self):   
        b = Board(rows=9, cols=9, num_mines=0, seed=0)

        b.reveal_cell(1, 1)
 
        for r in range(9):
            for c in range(9):
                self.assertTrue(b.revealed[r][c])
 
        self.assertTrue(b.game_over)
        self.assertTrue(b.win)
        self.assertEqual(b._remaining_safe, 0)


    def test_chord_good(self):        
        for _ in range(200): 
            rows, cols, num_mines = 9, 9, 10
            seed = random.randint(0,10000)

            board = Board(rows, cols, num_mines, seed) 
            board.reveal_cell(3, 3)

            # find all the chords in the board
            for i in range(rows): 
                for j in range(cols): 
                    if board.adj[i][j] > 0:
                        # neighbor count cannot equal number (need unknown neighbors)
                        neighbors = list(board.neighbors(i,j) )
                        if len(neighbors) > board.adj[i][j]: 
                            # reveal this spot 
                            board.reveal_cell(i,j)
                            # flag all the mines 
                            for (nr,nc) in neighbors:
                                if board.is_mine[nr][nc]: 
                                    board.set_flag(nr,nc,True)
                            # chord this cell 
                            board.chord(i,j) 
                            # verify all neighbors are now known 
                            if not board.game_over:
                                for (nr,nc) in board.neighbors(i,j):  
                                    self.assertTrue(board.revealed[nr][nc] or board.flagged[nr][nc]) 


    def test_chord_bad(self):   
        b = Board(rows=9, cols=9, num_mines=10, seed=0)
  
        b.reveal_cell(3, 3)
        b.reveal_cell(0, 1) 

        b.chord(0, 1) 

        self.assertFalse(b.revealed[0][0]) 
 
        self.assertFalse(b.revealed[0][0]) 
        self.assertFalse(b.revealed[1][0]) 
        self.assertFalse(b.revealed[1][1]) 
        self.assertFalse(b.revealed[0][2]) 


if __name__ == "__main__":
    unittest.main()
