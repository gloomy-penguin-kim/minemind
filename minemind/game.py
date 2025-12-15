from typing import List
from analysis.rules.move import Move
from core.board import Board
from core.changes import Action, ChangeSet
from minemind.historyentry import HistoryEntry
from solver.solver import Solver
from minemind.timer import Timer
from minemind.render import render_board, render_prob_heatmap, render_frontier 


class Game:


    def __init__(self): 
        self.board = None
        self.solver = None 
        self.timer = None   
        self.max_k = 30   
        self.moves = 0 
        self.history: List[HistoryEntry] = [] 

    def apply_move(self, move: Move):
        cs = self.board.apply(move.action, move.r, move.c)
        print("here",cs) 
        self.moves += 1
        print("here",cs) 
        self.history.push(move, cs)
        return cs
     
    def open(self, r: int, c: int): 
        if self.board.game_over: return False 
        return self.apply_action(Action.OPEN, r, c, note=f"OPEN {r},{c}")

    def flag(self, r: int, c: int):
        if not self.validate_board(): return False 
        return self.apply_action(Action.FLAG, r, c, note=f"FLAG {r},{c}")

    def chord(self, r: int, c: int):
        if not self.validate_board(): return False 
        return self.apply_action(Action.CHORD, r, c, note=f"CHORD {r},{c}")
    
    def chords(self): 
        if not self.validate_board(): return False 
        return self.solver.chords() 
    
    def verify(self): 
        if not self.validate_board(): return False 
        return self.solver.verify()  
    
    def hint(self): 
        if not self.validate_board(): return False 
        return self.solver.hint() 
    
    def step(self, guess=False): 
        if not self.validate_board(): return False 
        return self.solver.step(guess=guess) 
    
    def auto(self, guess=False, limit=None): 
        if not self.validate_board(): return False 
        return self.solver.auto(guess=guess, limit=limit) 

    def apply_action(self, action: Action, r: int, c: int, note: str = ""):
        move = Move(r=r, c=c, action=action, kind=None, reasons=())  # kind optional
        cs = self.board.apply(action, r, c)

        self.history.append(HistoryEntry(move=move, 
                                         changes=cs, 
                                         move_count_before=self.moves, 
                                         note=note))
        self.moves += 1
        return cs




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
        self.moves = 0


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
        # if self.is_winner(): 
        #     return False 
        return True
    

    def verify_coords(self, x, y):  
        if not self.has_curr_game():
            return False 
        # if self.is_winner(): 
        #     return False  
        if x >= 0 and y >= 0 and x < self.board.rows and y < self.board.cols:
            return True 
        print (f"coordinates are out of range: rows=0..{self.board.rows-1}, cols=0..{self.board.cols-1}\n")
        return False 
    

    def is_winner(self, game_over, winner): 
        if game_over: 
            self.timer.stop() 
            winlose = "won!" if winner else "lost."
            print(f"current game is over. you {winlose}\n")
            face = "d-(^_^)z" if winner else "(╯°□°)╯︵ ┻━┻" 
            print(face)
            print()
            print(f"total moves: {self.solver.moves}")
            print(f"elapsed time: {self.timer.get_elapsed_seconds_hms()}\n")
            if winner: 
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
        render_board(self.board, self.timer, reveal, self.moves)


    def render_prob_heatmap(self, probs): 
        render_prob_heatmap(self.board, probs)  
    

    def render_frontier(self, global_or_local="global"):
        render_frontier(self.solver.frontier_components, 
                        self.board, 
                        global_or_local)
        
        
    def apply_move(self, move: Move):
        cs = self.board.apply(move.action, move.r, move.c)

        entry = HistoryEntry(
            move=move,
            changes=cs,
            move_count_before=self.moves,
        )

        self.history.append(entry)
        self.moves += 1

    

    def undo(self):
        if len(self.history) <= 1:
            return "cannot undo before the first move\n"

        entry = self.history.pop()

        # revert board state
        self.board.undo(entry.changes)

        # restore move count
        self.moves = entry.move_count_before

        # clear terminal state
        self.board.game_over = False
        self.board.win = False

        return True