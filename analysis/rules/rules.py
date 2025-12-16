# rules.py – Singles + Subset + Scope equality/complements using bitmasks over local unknowns.

# core/rules.py
from __future__ import annotations 
from typing import List, Tuple  
from analysis.frontier.component import Component 
from analysis.rules.equivalence import _apply_equivalence
from analysis.rules.move import Move, MoveList
from analysis.rules.singles import _apply_singles
from analysis.rules.subsets import _apply_subset
from core.constants import Action 

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

def apply_rules(
    comps: List[Component],
    board,
    stop_after_one: bool = False
) -> List[Tuple[int, int, str, str]]:
    """
    find all the rules that apply to this component
    """ 
    moves = MoveList(stop_after_one)  
    rules: List[Move] = [] 
    conflicts: List[tuple[int,int]] = [] 

    for comp in comps: 
        _apply_singles(comp, board, moves, stop_after_one)

        if len(moves) > 1 and not stop_after_one:
            _apply_subset(comp, board, moves, stop_after_one)  

            if len(moves) > 1 and not stop_after_one: 
                _apply_equivalence(comp, board, moves, stop_after_one)
                
        m, c = moves.get_arrays() 
        rules += m
        conflicts += c  

    for rule in rules: 
        assert not(rule.action == Action.OPEN and board.is_mine[rule.r][rule.c] and (rule.r, rule.c) not in conflicts) 
        assert not(rule.action == Action.FLAG and not board.is_mine[rule.r][rule.c] and (rule.r, rule.c) not in conflicts) 
        
    if stop_after_one:
        return rules[0] if len(rules) > 0 else [], conflicts   

    return rules, conflicts 
