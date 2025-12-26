#solver.py – orchestrates:
#   for each component: apply deterministic rules
#   if small enough (k ≤ k_max): run exact enumeration & probabilities
#   hint, step, auto, etc.

# exact enumeration, probabilities, auto/step/hint 

# https://medium.com/@gaffney.tj/intro-to-early-game-minesweeper-probability-8af482104b94 

from __future__ import annotations

from typing import Dict, List, Tuple

from analysis.frontier.frontier import build_frontier
from analysis.probability.auto import guess_moves_for_autobot
from analysis.probability.enumeration import ProbabilityEngine, build_guess_heap
from analysis.rules.rules import apply_rules
from analysis.queries.chords import find_chords 
from core.changes import ChangeSet
from core.constants import Action 
from core.lru import LRUCache 
from analysis.rules.move import Move 
from core.config import config 

import logging  
 
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# Input: Board, build_frontier, rules, signatures, lru
# Output: actions on Board (open/flag), explanations, probabilities, summaries
# Owns: cache, frontier state, solver parameters
# Exposes: hint, step, auto, prob, frontier_summary

class Solver:
    """
    Wraps a Board and provides:
    """
    def __init__(self, board, max_k: int = 60, cache_size: int = 1024):
        self.board = board

        self.max_k = max_k
        
        self.sig_cache = LRUCache(cache_size)

        self.frontier_components = None  # cached frontier 

        self.prob_engine = ProbabilityEngine(max_k=self.max_k, cache_size=cache_size)

        self.history = [] 

        self.moves = 0 

        self.frontier_dirty = True 
        self.refresh_frontier()   


    def set_max_k(self, k:int):
        self.prob_engine.max_k = k 


    def get_max_k(self):
        return self.prob_engine.max_k


    # these handle when the board is modified and becomes dirty  
    def refresh_frontier(self):
        """call this for ditry birds"""  
        if self.frontier_dirty:   
            self.frontier_components = build_frontier(self.board)  
            self.frontier_dirty = False 


    def open(self, r, c): 
        """
        cli command for open 
        """  
        return self._apply(Action.OPEN, r, c)  


    def flag(self, r, c):
        """
        cli command for flag... toggle  
        """
        return self._apply(Action.FLAG, r, c)
    

    def chord(self, r, c): 
        """
        cli command for chord 
        """
        return self._apply(Action.CHORD, r, c) 
    

    def chords(self) -> list[tuple[int,int]]: 
        return find_chords(self.board)
    
 
    def step(self, guess=False, force=False):
        """
        Perform a single logical step.
        If guess=True and no deterministic move exists, make one guess.
        """  
        self.refresh_frontier()
        move, conflicts = apply_rules(self.frontier_components, 
                                      self.board)

        if conflicts: 
            return None, ChangeSet(), conflicts 

        if move:
            return move, self._apply(move.action, move.r, move.c), []
        
        if guess:
            self.refresh_frontier()
            all_probs, _ = self.prob() 
            moves, det = guess_moves_for_autobot(all_probs, self.board.rows, self.board.cols) 
            
            if moves:
                if det or force: 
                    move = moves[0] if len(moves) > 0 else moves
                    return move, self._apply(move.action, move.r, move.c), []
            
        return None, ChangeSet(), []


    def verify(self):
        """
        cli command verify... to verify existing flags if they are mines or not 
        """  
        return self.board.verify_all_existing_flags_found()  
    

    def hint(self, guess=False):
        """
        Return a suggested move without applying it.
        Prefer deterministic rules; fall back to probability-based guess.
        """
        self.refresh_frontier()      
        move, conflicts = apply_rules(self.frontier_components, self.board)
         
        if move:
            return [move[0]], conflicts
        
        if guess:
            self.refresh_frontier()      
            all_probs, _ = self.prob()  # keep using your existing prob()
            moves, det = guess_moves_for_autobot(all_probs, self.board.rows, self.board.cols) 
            if det: 
                return moves, conflicts 
            
        return [], conflicts


    def auto(self, guess: bool=False, limit: int | None = None, force: bool=False):
        """
        auto [--guess] [--limit N]
        - run deterministic steps + exact enumeration
        - if guess=True and no certain moves: pick lowest-risk guess
        - stop after limit moves if provided
        """ 

        if not self.verify_board(): 
            return [], ChangeSet() 
 

        all_moves: List[Move] = [] 
        all_cs = ChangeSet() 
        conflicts = [] 

        def can_continue() -> bool:
            if self.board.game_over:
                return False
            if limit is not None and len(all_moves) >= limit:
                return False
            return True 
        
 
        while can_continue():   
            
            modified = False 

            self.refresh_frontier()      
 
            moves,conflicts = apply_rules(self.frontier_components, 
                                            self.board, 
                                            stop_after_one=False)  
            if len(conflicts) > 0:  
                return [], ChangeSet(), conflicts 

            # Respect the limit: trim moves if needed
            if limit is not None:
                remaining_steps = limit - len(all_moves)
                if len(moves) > remaining_steps:
                    moves = moves[:remaining_steps] 
 
            # stop if there are rule conflicts 
            if moves:    
                applied_moves, applied_cs = self._apply_moves(moves)  
                all_cs = all_cs.merged(applied_cs) 
                all_moves += applied_moves  
                modified = True 

            if modified: continue 

            if not can_continue(): break 
 
            if not guess: break

            # 2) Guessing mode: use probabilities to pick lowest-risk unknown 
            all_probs, _ = self.prob() 
            moves, det = guess_moves_for_autobot(all_probs, self.board.rows, self.board.cols) 

            if limit is not None:
                remaining_steps = limit - len(all_moves)
                if len(moves) > remaining_steps:
                    moves = moves[:remaining_steps] 

            if det or force: 
                applied_moves, applied_cs = self._apply_moves(moves) 
                if not applied_cs.empty: 
                    modified = True 
                    all_moves += applied_moves
                    all_cs = all_cs.merged(applied_cs)

            if not modified: 
                break 
            
        return all_moves, all_cs, conflicts  


    def prob(self) -> Tuple[Dict[Tuple[int, int], float], List[Tuple[float, int, float, float, Tuple[int, int]]]]:
        self.refresh_frontier() 
        all_probs = self.prob_engine.compute_probabilities(self.board, self.frontier_components)
        heap = build_guess_heap(all_probs, self.board.rows, self.board.cols)
        return all_probs, heap 
        
 
    def count(self): 
        """
        cli command to count number of flags, revealed, unknown
        """
        if not self.verify_board(): 
            return 
        flags = self.board.count_flags_on_board()
        unknowns = self.board.count_unkown_cells()
        revealed = self.board.count_revealed_cells()
        return flags, unknowns, revealed
    

    def frontier_summary(self) -> List[Tuple[int, int, int]]:
        """Return a summary of frontier components as (idx, k, m)."""
        self.refresh_frontier()
        comps = self.frontier_components or []

        summary: List[Tuple[int, int, int]] = []
        for i, comp in enumerate(comps):
            k = comp.k
            m = len(comp.constraints)
            summary.append((i, k, m))
        return summary


    def conflicts(self):
        """
        Return a suggested move without applying it.
        Prefer deterministic rules; fall back to probability-based guess.
        """
        if not self.verify_board():
            return None 
        
        self.refresh_frontier() 

        _, conflicts = apply_rules(self.frontier_components, 
                                self.board, 
                                stop_after_one=False) 
  
        return conflicts


    def _apply_moves(self, moves: List[Move]):  
        applied_moves = [] 
        applied_cs = ChangeSet() 
        self.frontier_dirty = True 
        for move in moves:
            cs = self.board.apply(move.action, move.r, move.c, move.val)  
            if not cs.empty: 
                applied_cs = applied_cs.merged(cs) 
                applied_moves.append(move) 
                if applied_cs.win or applied_cs.game_over: 
                    break  
        self.refresh_frontier() 
        return applied_moves, applied_cs 


    def _apply(self, action:Action, r:int, c:int, val:bool|None=None):  
        self.frontier_dirty = True 
        cs = self.board.apply(action, r, c, val)
        self.refresh_frontier() 
        return cs 
    
  
    def verify_board(self): 
        if self.board.win or self.board.game_over:  
            return False 
        if not self.board.mines_placed:
            return False 
        return True 
     
    
   