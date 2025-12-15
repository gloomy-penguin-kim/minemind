
# this is for rule number 1 
from analysis.rules.move import Action, Move, MoveList, MoveKind
from core.utility import get_indicies_from_bitmask
from core_bkup.frontier import Component 


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
                move = Move(r=r, 
                            c=c, 
                            action=Action.OPEN, 
                            kind=MoveKind.SAFE, 
                            reason=("Singles: remaining == 0 are SAFE"), 
                            score=None)
                moves.add_move(move)
                if stop_after_one: return 

        # Rule: remaining == the size of the scope, then all unknowns in scope are MINES.
        elif remaining == scope_size:
            for local_idx in get_indicies_from_bitmask(mask_local):
                gid = comp.local_to_global[local_idx]
                r, c = divmod(gid, cols) 
                # moves.append((r, c, MINE, "Singles: remaining==|scope| are MINES"))
                s = (f"Singles: remaining==|scope| are MINES",
                    f"gid={gid}",
                    f"local_mask={bin(mask_local)}",
                    f"bit_count={mask_local.bit_count()}",
                    f"remaining={remaining}")
                move = Move(r=r, 
                            c=c, 
                            action=Action.FLAG,
                            kind=MoveKind.MINE, 
                            reason=s, 
                            score=None) 
                moves.add_move(move)
                if stop_after_one: return 

    return moves 