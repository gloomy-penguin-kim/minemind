from core.board import Board
from solver.solver import Solver
from minemind.timer import Timer
from minemind.render import render_board, render_prob_heatmap, render_frontier 


class Game:


    def __init__(self): 
        self.board = None
        self.solver = None 
        self.timer = None   
        self.max_k = 30   

    def set_k_max(self, k) -> None: 
        self.max_k = k 
        if self.solver: 
            self.solver.max_k = k


    def new(self, rows, cols, mines, seed=None):
        self.board = Board(rows=rows, 
                           cols=cols, 
                           num_mines=mines, 
                           seed=seed)
        self.solver = Solver(self.board,  
                             max_k=self.max_k)
        self.timer = None


    def start_timer(self): 
        self.timer = Timer() 
        self.timer.start() 


    def resume_timer(self): 
        self.timer.resume() 


    def validate_board(self):
        if not self.has_curr_game():
            return False 
        if not self.board.mines_placed:
            print("please place first move with `open X Y`\n")
            return False
        if self.is_winner(): 
            return False 
        return True
    

    def verify_coords(self, x, y):  
        if not self.has_curr_game():
            return False 
        if self.is_winner(): 
            return False  
        if x >= 0 and y >= 0 and x < self.board.rows and y < self.board.cols:
            return True 
        print (f"coordinates are out of range: rows=0..{self.board.rows-1}, cols=0..{self.board.cols-1}\n")
        return False 
    

    def is_winner(self): 
        if self.board.game_over: 
            self.timer.stop() 
            face = "d-(^_^)z" if self.board.win else "(╯°□°)╯︵ ┻━┻" 
            winlose = "won!" if self.board.win else "lost."
            print(f"current game is over. you {winlose}\n")
            print(face)
            print()
            print(f"total moves: {self.solver.moves}")
            print(f"elapsed time: {self.timer.get_elapsed_seconds_hms()}\n")
            if self.board.win:
                print("use 'new ...' or 'load ...' to start a new game.\n")
            else:
                print("suggestion: use the `undo` command\n")
            return True  
        return False
    

    def has_curr_game(self): 
        if self.board is None:
            print("No game. Use 'new ...' or 'load ...' first.\n")
            return False  
        return True 
    

    def render_board(self, reveal=False): 
        render_board(self.board, self.timer, reveal, self.solver.moves)


    def render_prob_heatmap(self, probs): 
        render_prob_heatmap(self.board, probs)  
    

    def render_frontier(self, global_or_local="global"):
        render_frontier(self.solver.frontier_components, 
                        self.board, 
                        global_or_local)