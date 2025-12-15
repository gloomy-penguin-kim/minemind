

from typing import List
from analysis.rules.move import Move, MoveKind, MoveList
from core.changes import Action
from core.utility import get_indicies_from_bitmask
from analysis.frontier.component import Component



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
                    s = (f"Subset: A⊆B, a==b -> B\\A SAFE" ,
                         f"{bin(constraints[i].mask_local)} is a subset of",
                         f"{bin(constraints[j].mask_local)}")
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MoveKind.SAFE, 
                        reason=s
                    )
                    if stop_after_one and len(moves) > 1:
                        return moves 
                
                # All in B\A are MINES
                elif rem_b - rem_a == diff_size: 
                    
                    s = (f"Subset: A⊆B, b-a==|B\\A| -> B\\A MINES",
                         f"{bin(constraints[i].mask_local)} is a subset of",
                         f"{bin(constraints[j].mask_local)}")
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MoveKind.MINE, 
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
                    s = (f"Subset: B⊆A, a==b -> A\\B SAFE",
                        f"{bin(constraints[j].mask_local)} is a subset of",
                        f"{bin(constraints[i].mask_local)}")
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MoveKind.SAFE, 
                        reason=s
                    )
                    if stop_after_one and len(moves) > 1:
                        return moves
                elif rem_a - rem_b == diff_size:
                    s = (f"Subset: B⊆A, a-b==|A\\B| -> A\\B MINES",
                        f"{bin(constraints[j].mask_local)} is a subset of",
                        f"{bin(constraints[i].mask_local)}")
                    _process_moves_for_this_mask(
                        board=board, 
                        moves=moves, 
                        local_to_global=comp.local_to_global, 
                        mask=diff, 
                        kind=MoveKind.MINE, 
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
        
        a = Action.OPEN if kind == MoveKind.OPEN else Action.FLAG 
        
        move = Move(r, c, 
                    action=a, 
                    kind=kind, 
                    reason=reason, 
                    score=None)
        moves.add_move(move)  

    return moves   
