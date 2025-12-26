# save/load JSON snapshot 
import os 
import json 
import hashlib 
from datetime import datetime 

from core.board import Board 
from solver.solver import Solver 
from minemind.timer import Timer 

def save_snapshot(g, filename): 
    dirname = os.path.dirname(filename) 
    if dirname:  
        if not os.path.isdir(dirname): 
            print(f"directory not found: '{dirname}\n'")
            return False 
    sha256 = hashlib.sha256()
    with open(filename, 'w') as f:
        json_str = json.dumps(_board_to_object(g)) + "\n" 
        sha256.update(json_str.encode('utf-8'))
        f.write(json_str)  
        f.write(sha256.hexdigest())
    return True 
 

def load_snapshot(g, filename):      
    if not os.path.isfile(filename): 
        print(f"file not found: '{filename}'\n")
        return  
    sha256 = hashlib.sha256()
    with open(filename, 'r') as f:
        first_line = f.readline().encode('utf-8') 
        second_line = f.readline() 
        sha256.update(first_line)
        if second_line == sha256.hexdigest():  
            _load_from_json(g,first_line)  
            g.render_board()  
            return 
        else:
            print("file was corrupted; checksum did not match.\n") 
            return 
    print("file import failed\n") 


def _load_from_json(g, json_str: str):  
    obj = json.loads(json_str)
    g.board = _create_board_from_object(obj) 

    g.solver = Solver(g.board) 
    g.moves = obj["moves"]

    created_dt = datetime.fromtimestamp(obj['timer']['created_dt'])
    saved_dt = datetime.fromtimestamp(obj['timer']['elapsed_seconds'])
    elapsed_seconds = obj['timer']['elapsed_seconds']
    g.timer = Timer(created_dt, saved_dt, elapsed_seconds)
    g.timer.resume() 
 
     
def _create_board_from_object(obj): 
    rows = obj['rows']
    cols = obj['cols']
    num_mines = obj['num_mines']
    seed = obj['seed']

    board = Board(rows, cols, num_mines, seed)

    board.is_mine = obj['is_mine']
    board.adj = obj['adj']
    board.revealed = obj['revealed']
    board.flagged = obj['flagged']

    board.mines_placed = obj['mines_placed']
    board.game_over = obj['game_over']
    board.win = obj['win']
 
    board.moves = obj['moves']

    board._remaining_safe = board.rows * board.cols - board.num_mines
    return board


def _board_to_object(g):
    board = g.board  
    timer = g.timer 
    return {
        "rows": board.rows, 
        "cols": board.cols,
        "num_mines": board.num_mines,
        "seed": board.seed, 
        "is_mine": board.is_mine,
        "adj": board.adj,
        "revealed": board.revealed,
        "flagged": board.flagged,
        "mines_placed": board.mines_placed, 
        "game_over": board.game_over, 
        "win": board.win,  
        "moves": g.moves,
        "timer": { 
            "created_dt": timer.created_dt.timestamp(),
            "elapsed_seconds": timer.get_elapsed_seconds(), 
            "saved_dt": datetime.now().timestamp()  
        }
    } 