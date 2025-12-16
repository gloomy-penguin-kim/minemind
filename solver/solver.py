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
from analysis.probability.auto import guess_moves_for_auto
from analysis.probability.enumeration import ProbabilityEngine, build_guess_heap  
from analysis.probability.guess import GuessItem, guessitem_to_move, pop_candidates, select_hint_guess_list
from analysis.rules.rules import apply_rules
from analysis.queries.chords import find_chords 
from core.changes import ChangeSet
from core.constants import Action 
from core.lru import LRUCache
from core.signatures import Signature, component_signature
from analysis.rules.move import Move
from core.utility import get_indicies_from_bitmask 
from core.config import config 

import logging 

from core_bkup.move import MINE, SAFE
 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


    def set_max_k(self, k:int):
        self.prob_engine.max_k = k 


    def get_max_k(self):
        return self.prob_engine.max_k


    # these handle when the board is modified and becomes dirty  
    def refresh_frontier(self):
        """call this for ditry birds"""  
        self.frontier_components = build_frontier(self.board)  


    def open(self, r, c): 
        """
        cli command for open 
        """ 
        print("solver")
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
    
 
    def step(self, guess=False, force=False):
        """
        Perform a single logical step.
        If guess=True and no deterministic move exists, make one guess.
        """ 
        comps = build_frontier(self.board)
        move, conflicts  = apply_rules(comps, self.board, stop_after_one=True)

        if move:
            return move, self.board.apply(move.action, move.r, move.c)
        
        if guess:
            all_probs, _ = self.prob() 
            moves, det = guess_moves_for_auto(all_probs, self.board.rows, self.board.cols) 
            
            if moves:
                move = moves[0] if len(moves) > 0 else moves
                return move, self.board.apply(move.action, move.r, move.c)
            
        return None, ChangeSet() 


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
        move, _ = apply_rules(comps, self.board, stop_after_one=True)
         
        if move:
            return [move]
        
        if guess:
            all_probs, _ = self.prob()  # keep using your existing prob()
            moves,det = guess_moves_for_auto(all_probs, self.board.rows, self.board.cols) 
            return moves 
            
        return []     


    def auto(self, guess: bool=False, limit: int | None = None, force: bool=False):
        """
        auto [--guess] [--limit N]
        - run deterministic steps + exact enumeration
        - if guess=True and no certain moves: pick lowest-risk guess
        - stop after limit moves if provided
        """ 

        if not self.verify_board(): 
            return [], ChangeSet()
        
        logger.debug("guess = %s, limit = %s", guess, limit)
 

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

            logger.debug("moves: %s, %s", limit, moves)
            # stop if there are rule conflicts 
            if moves:    

                for move in moves:
                    
                    if not can_continue(): break  

                    flag = True if move.action == Action.FLAG else None 
                    cs = self.board.apply(move.action, move.r, move.c, flag)  
                    
                    if not cs.empty:  
                        modified = True 
                        all_cs = all_cs.merged(cs) 
                        all_moves.append(move)  

            if modified: continue 

            if not can_continue(): break 
 
            if not guess: break

            # 2) Guessing mode: use probabilities to pick lowest-risk unknown 
            all_probs, _ = self.prob() 
            moves, det = guess_moves_for_auto(all_probs, self.board.rows, self.board.cols) 

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


    def _heap(self, apply: bool = True):
        all_probs, _ = self.prob()     # or engine.compute_probabilities(...)
        if not all_probs:
            return [], []

        heap = build_guess_heap(all_probs, self.board.rows, self.board.cols)

        skip = lambda r, c: self.board.revealed[r][c] or self.board.flagged[r][c]

        # If apply=True: we only need ONE candidate (best-rated).
        # If apply=False: return candidates until we find the first "safe" (<50% mine)
        candidates = pop_candidates(
            heap,
            skip=skip,
            stop_after_safe=(not apply),
            limit=(1 if apply else None),
        )

        moves = [] 

        for item in candidates:
            mine_probability_percent = item.p_mine * 100.0

            if item.p_mine < 0.5:
                mv = Move(item.r, item.c, SAFE, [f"GUESS - mine probability: {mine_probability_percent:6.2f}%"])
            else:
                mv = Move(item.r, item.c, MINE, [f"GUESS - mine probability: {mine_probability_percent:6.2f}%"])

            if apply:
                ec = self._apply_move(mv)
                if ec: 
                    moves.append(mv) 
            else:
                moves.append(mv)

        return moves
    

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
        applied_moves = [] 
        applied_cs = ChangeSet() 
        for move in moves:
            cs = self._apply_move(move)  
            if not cs.empty: 
                applied_cs = applied_cs.merged(cs) 
                applied_moves.append(move) 
                if applied_cs.win or applied_cs.game_over: 
                    break 
        logger.debug("applied_moves %s",applied_moves)
        logger.debug("applied_cs %s",applied_cs)
        return applied_moves, applied_cs


    def _apply_move(self, move: Move): 
        return self.board.apply(move.action, move.r, move.c, move.val)
    
  
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
 
