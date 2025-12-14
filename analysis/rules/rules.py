# rules.py – Singles + Subset + Scope equality/complements using bitmasks over local unknowns.

# core/rules.py
from __future__ import annotations 
from typing import List, Tuple  
from analysis.frontier.component import Component 
from analysis.rules.move import MoveList
from analysis.rules.singles import _apply_singles
from analysis.rules.subsets import _apply_subset

import logging 
logger = logging.getLogger(__name__)


def apply_rules(
    comps: List[Component],
    board,
    stop_after_one: bool = False,
    conflicts_only: bool = False 
) -> List[Tuple[int, int, str, str]]:
    """
    find all the rules that apply to this component
    """ 
    moves = MoveList(stop_after_one)  

    for comp in comps: 
        _apply_singles(comp, board, moves, stop_after_one)
        if len(moves) > 1 and not stop_after_one:
            _apply_subset(comp, board, moves, stop_after_one)  
        rules, conflicts = moves.get_arrays() 

    if stop_after_one:
        return rules[0] if len(rules) > 0 else []  
    return moves if not conflicts_only else conflicts 
