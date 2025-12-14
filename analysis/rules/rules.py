# rules.py – Singles + Subset + Scope equality/complements using bitmasks over local unknowns.

# core/rules.py
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Tuple
from core.frontier import Component
from core.utility import get_indicies_from_bitmask
from core.config import config 
from core.move import Move 

from core.move import UNKNOWN, SAFE, MINE

import logging 
logger = logging.getLogger(__name__)

 
class MoveList:
    def __init__(self, one=False): 
        self.moves = {}  
        self.conflicts: List[tuple] = [] 
        self.one = one 
    def add_move(self, move: Move): 
        if not isinstance(move, Move): 
            raise Exception(move)
            return 
        if self.one and len(self.moves) > 0: return 
        rc = move.r, move.c
        if (rc) in self.moves.keys(): 
            move_existing = self.moves[rc]
            if move_existing.kind != move.kind: 
                self.conflicts.append(rc)
        else: 
            self.moves[rc] = move 
    def get_arrays(self):  
        m = [] 
        for k in self.moves:  
            m.append(self.moves[k]) 
        return m, self.conflicts[:]
    def __len__(self): 
        return len(self.moves) 


# this is for rule number 1 
def _apply_singles(
        comp: Component, 
        board,  
        moves: MoveList,
        stop_after_one:bool=False): 
    """
    # # Singles
    # for (cells, remaining) in constraints:
    #     if remaining == 0:
    #         mark all cells as SAFE
    #     elif remaining == len(cells):
    #         mark all cells as MINE 
    """ 
    cols = board.cols

    for cons in comp.constraints:
        mask_local = cons.mask_local
        if mask_local == 0:
            continue

        scope_size = mask_local.bit_count() 
        remaining = cons.remaining

        # Rule: remaining == 0, then all unknowns in scope are SAFE.
        if remaining == 0:
            for local_idx in get_indicies_from_bitmask(mask_local):
                gid = comp.local_to_global[local_idx]
                r, c = divmod(gid, cols) 
                # moves.append((r, c, SAFE, "Singles: remaining==0 are SAFE"))
                move = Move(r=r, c=c, kind=SAFE, reason=["Singles: remaining == 0 are SAFE"])
                moves.add_move(move)
                if stop_after_one: return 

        # Rule: remaining == the size of the scope, then all unknowns in scope are MINES.
        elif remaining == scope_size:
            for local_idx in get_indicies_from_bitmask(mask_local):
                gid = comp.local_to_global[local_idx]
                r, c = divmod(gid, cols) 
                # moves.append((r, c, MINE, "Singles: remaining==|scope| are MINES"))
                s = [f"Singles: remaining==|scope| are MINES",
                    f"gid={gid}",
                    f"local_mask={bin(mask_local)}",
                    f"bit_count={mask_local.bit_count()}",
                    f"remaining={remaining}"]
                
                move = Move(r=r, c=c, kind=MINE, reason=s) 
                moves.add_move(move)
                if stop_after_one: return 

    return moves 


def _apply_subset(
        comp: Component, 
        board, 
        moves,
        stop_after_one: bool
        ):
    """
    # for each pair (A, a), (B, b):
    #     if A ⊂ B:
    #         diff = B - A
    #         if a == b:
    #             mark diff as SAFE
    #         elif b - a == len(diff):
    #             mark diff as MINE

    #     if B ⊂ A:
    #         diff = A - B
    #         if a == b:
    #             mark diff as SAFE
    #         elif a - b == len(diff):
    #             mark diff as MINE
    """ 
    constraints = comp.constraints 
    n = len(constraints)  

    for i in range(n):
        mask_a = constraints[i].mask_local
        rem_a = constraints[i].remaining
        if mask_a == 0:
            continue

        for j in range(i + 1, n):
            mask_b = constraints[j].mask_local
            rem_b = constraints[j].remaining
            if mask_b == 0:
                continue

            # First: A subset B?
            # for each pair (A, a), (B, b):
            #     if A ⊂ B:
            #         diff = B - A
            #         if a == b:
            #             mark diff as SAFE
            #         elif b - a == len(diff):
            #             mark diff as MINE 
            if mask_a & mask_b == mask_a and mask_a != mask_b:


                # mask b and the inverted mask a is our differnce
                diff = mask_b & ~mask_a

                # get the bit_count of the difference 
                diff_size = diff.bit_count() 

                # if all in B\A are SAFE
                if rem_a == rem_b:
                    s = [f"Subset: A⊆B, a==b -> B\\A SAFE" ,
                         f"{bin(constraints[i].mask_local)} is a subset of",
                         f"{bin(constraints[j].mask_local)}"]
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=SAFE, 
                        reason=s
                    )
                    if stop_after_one and len(moves) > 1:
                        return moves 
                
                # All in B\A are MINES
                elif rem_b - rem_a == diff_size: 
                    
                    s = [f"Subset: A⊆B, b-a==|B\\A| -> B\\A MINES",
                         f"{bin(constraints[i].mask_local)} is a subset of",
                         f"{bin(constraints[j].mask_local)}"]
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MINE, 
                        reason=s
                    ) 
                    if stop_after_one and len(moves) > 1:
                        return moves

            # Second: B subset A?
            #     if B ⊂ A:
            #         diff = A - B
            #         if a == b:
            #             mark diff as SAFE
            #         elif a - b == len(diff):
            #             mark diff as MINE 
            if mask_a & mask_b == mask_b and mask_a != mask_b:
                diff = mask_a & ~mask_b
                diff_size = diff.bit_count() 
                if rem_a == rem_b:
                    s = [f"Subset: B⊆A, a==b -> A\\B SAFE",
                        f"{bin(constraints[j].mask_local)} is a subset of",
                        f"{bin(constraints[i].mask_local)}"]
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=SAFE, 
                        reason=s
                    )
                    if stop_after_one and len(moves) > 1:
                        return moves
                elif rem_a - rem_b == diff_size:
                    s = [f"Subset: B⊆A, a-b==|A\\B| -> A\\B MINES",
                        f"{bin(constraints[j].mask_local)} is a subset of",
                        f"{bin(constraints[i].mask_local)}"]
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MINE, 
                        reason=s
                    )
                    if stop_after_one and len(moves) > 1:
                        return moves

    return moves


def _process_moves_for_this_mask(
    local_to_global: List[int], 
    board, 
    moves: MoveList, 
    mask: int,
    kind: int,
    reason: List[str]
):  
    cols = board.cols 
    
    # get the global id's out of the bitmask w/ comp.global_to_local
    for local_idx in get_indicies_from_bitmask(mask):
        gid = local_to_global[local_idx]
        r, c = divmod(gid, cols)

        # important because if we only get to look at one move 
        # then it shouldn't be lacking if a cell got modified
        # (shouldn't happen but would be sad if it did)
        if board.revealed[r][c] or board.flagged[r][c]:
            continue  
        
        move = Move(r, c, kind, reason)
        moves.add_move(move)  

    return moves   


def apply_rules(
    comp: Component,
    board,
    stop_after_one: bool = False
) -> List[Tuple[int, int, str, str]]:
    """
    find all the rules that apply to this component
    """ 
    moves = MoveList(stop_after_one)  
 
    _apply_singles(comp, board, moves, stop_after_one)
    
    if len(moves) > 1 and not stop_after_one:
        _apply_subset(comp, board, moves, stop_after_one)  
 
    return moves.get_arrays() 
