#solver.py – orchestrates:
#   for each component: apply deterministic rules
#   if small enough (k ≤ k_max): run exact enumeration & probabilities
#   hint, step, auto, etc.

# exact enumeration, probabilities, auto/step/hint 

# https://medium.com/@gaffney.tj/intro-to-early-game-minesweeper-probability-8af482104b94 

from __future__ import annotations

from datetime import datetime
from heapq import heappop, heappush
from typing import Dict, List, Tuple, Any

from analysis.frontier.frontier import build_frontier
from analysis.probability.enumeration import ProbabilityEngine 
from analysis.probability.guess import best_guess
from analysis.rules.rules import apply_rules
from analysis.queries.chords import find_chords 
from core.changes import Action, ChangeSet
from core.lru import LRUCache
from core.signatures import Signature, component_signature
from analysis.rules.move import MoveKind, Move
from core.utility import get_indicies_from_bitmask 
from core.config import config 

import logging
import copy

logger = logging.getLogger(__name__) 


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
 
        self.refresh_frontier()   


    # these handle when the board is modified and becomes dirty  
    def refresh_frontier(self):
        """call this for ditry birds"""  
        self.frontier_components = build_frontier(self.board)  


    def open(self, r, c): 
        """
        cli command for open 
        """
        return self.board.apply(Action.OPEN, r, c)  


    def flag(self, r, c):
        """
        cli command for flag... toggle  
        """
        return self.board.apply(Action.FLAG, r, c)
    

    def chord(self, r, c): 
        """
        cli command for chord 
        """
        return self.board.chord(r,c) 
    

    def chords(self) -> list[tuple[int,int]]: 
        return find_chords(self.board)
    
 
    def step(self, guess=False):
        """
        Perform a single logical step.
        If guess=True and no deterministic move exists, make one guess.
        """ 
        comps = build_frontier(self.board)
        move  = apply_rules(comps, self.board, stop_after_one=True)

        if move:
            return self.board.apply(move.action, move.r, move.c)
        
        if guess:
            g = best_guess(self.board, comps)
            if g:
                return self.board.apply(g.action, g.r, g.c)
            
        return None


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
        comps = build_frontier(self.board)
        move  = apply_rules(comps, self.board, stop_after_one=True)
         
        if move:
            return move 
        
        if guess:
            g = best_guess(self.board, comps)
            if g:
                return g 
            
        return None 


    def auto(self, guess: bool=False, limit: int | None = None):
        """
        auto [--guess] [--limit N]
        - run deterministic steps + exact enumeration
        - if guess=True and no certain moves: pick lowest-risk guess
        - stop after limit moves if provided
        """ 

        if not self.verify_board(): 
            return None 
        
        logger.debug("guess = %s, limit = %s", guess, limit)

        all_moves = []
        effected_cells = []  
 
        while True: 
            if limit is not None and len(all_moves) >= limit:
                break
 
            if not self.verify_board(): 
                break 

            # Rebuild frontier for current board
            self.refresh_frontier()              
            moved = False

            # 1) Deterministic moves (Singles, Subset, etc) on all components
            for comp in self.frontier_components: 

                if limit is not None and len(all_moves) >= limit:
                    break

                # apply_rules returns list[(r, c, kind, reason)]
                moves = apply_rules(self.frontier_components, 
                                    self.board, 
                                    stop_after_one=False)

                if not moves:
                    continue

                # Respect the limit: trim moves if needed
                if limit is not None:
                    remaining_steps = limit - len(all_moves)
                    if len(moves) > remaining_steps:
                        moves = moves[:remaining_steps] 

                if moves:   
                    for move in moves:
                        return self.board.apply(move.action, move.r, move.c) 
                    self.refresh_frontier()        

            # If we made at least one deterministic move, loop around again
            if moved:
                continue

            if not guess:
                # guessing not allowed 
                break

            # 2) Guessing mode: use probabilities to pick lowest-risk unknown 
            guesses, guess_effected_cells = self._heap(apply=True) 

            if len(guesses) == 0: 
                break

            all_moves.extend(guesses)   
            effected_cells.extend(guess_effected_cells) 
 
            if not self.verify_board(): 
                break 

        if len(effected_cells) > 0:      
            l = max(1, len(all_moves))  
            self.verify_and_history(moves=effected_cells, 
                                    note=f"AUTO for {l} moves\n",
                                    count=l) 
        return all_moves
                      

    def prob(self) -> Tuple[Dict[Tuple[int, int], float], List[Tuple[float, int, float, float, Tuple[int, int]]]]:
        self.refresh_frontier() 
        return self.prob_engine.compute_probabilities(self.board, self.frontier_components)

 
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

        conflicts = apply_rules(self.frontier_components, 
                                self.board, 
                                stop_after_one=False, 
                                conflicts_only=True) 
  
        return conflicts


    def _apply_moves(self, moves: List[Move]): 
        logger.debug("_apply_moves %s", moves) 
        effected_cells = [] 
        applied_moves = [] 
        for move in moves:
            ec = self._apply_move(move)  
            if len(ec) > 0: 
                effected_cells.extend(ec) 
                applied_moves.append(move) 
        return applied_moves, effected_cells 


    def _apply_move(self, move: Move): 
        return self.board.apply(move.action, move.r, move.c)
    
  
    def verify_board(self): 
        if self.board.win or self.board.game_over:  
            return False 
        if not self.board.mines_placed:
            return False 
        return True 
     
    
    def test_invariantes_of_the_mines(self, mine_probability, mines_in_component, r, c, k): 
        if config.invariants:  
            if self.board.revealed[r][c] or self.board.flagged[r][c]:
                raise AssertionError(f"probability assigned to revealed or flagged location for r={r},c={c},p={mine_probability}\n")
            if mine_probability == 0.0 and self.board.is_mine[r][c]:
                raise AssertionError(f"conflict in probability found at cell r={r},c={c},p={mine_probability}\n")
            if mine_probability == 1.0 and not self.board.is_mine[r][c]:
                raise AssertionError(f"conflict in probability found at cell r={r},c={c},p={mine_probability}\n") 
            if mines_in_component == 0 and mine_probability > 0.0:
                raise AssertionError(f"zero mines in component, greather than 0 mine prob: r={r},c={c},p={mine_probability}")
            if mines_in_component == k and mine_probability < 1.0:
                raise AssertionError(f"all mines in component, less than 1 mine prob: r={r},c={c},p={mine_probability}")
            if not(0.0 <= mine_probability <= 1.0):
                raise AssertionError(f"mine probablity out of range (0.0..1.0): r={r},c={c},p={mine_probability}")
 
