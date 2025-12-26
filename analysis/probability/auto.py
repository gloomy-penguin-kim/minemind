

from dataclasses import dataclass 
from analysis.rules.move import Move
from core.constants import Action  

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

SAFE_T = 0.05
MINE_T = 0.95

@dataclass(frozen=True, order=True)
class GuessItem:
    rating: float
    p_mine: float
    centrality: float
    r: int
    c: int 

def guess_moves_for_autobot(all_probs: dict[tuple[int,int], float], rows: int, cols: int) -> tuple[list[Move], bool]:
    """
    Returns (moves).
    - If there are sure moves: returns ALL sure-safe opens (and optionally sure-mine flags)
    - Else: returns ONE safest open
    """ 

    items: list[GuessItem] = []
    for (r,c), p in all_probs.items(): 
        dr = r - (rows - 1) / 2.0
        dc = c - (cols - 1) / 2.0
        centrality = dr*dr + dc*dc
        rating = min(p, 1.0 - p)
        items.append(GuessItem(rating=rating, p_mine=p, centrality=centrality, r=r, c=c))

    if not items:
        return [], True

    # sort by safest click (p asc), then tie-breakers
    items.sort(key=lambda g: (g.p_mine, g.rating, g.centrality))

    sure_safe = [g for g in items if g.p_mine <= SAFE_T]
    sure_mine = [g for g in items if g.p_mine >= MINE_T]  # optional

    logger.debug("sure_safe: %s", sure_safe)
    logger.debug("sure_mine: %s", sure_mine)

    moves: list[Move] = []

    # 1) Apply all sure-safe opens
    for g in sure_safe:
        moves.append(Move(
            r=g.r, c=g.c,
            action=Action.OPEN,
            kind=Action.GUESS,
            reasons=(f"GUESS - mine probability: {g.p_mine*100.0:6.2f}% (near-certain safe)",),
            score=g.p_mine
        ))

    # 2) Optional: apply sure-mine flags (if you want)
    # If you want to follow “safest click” strictly, comment this block out.
    for g in sure_mine:
        moves.append(Move(
            r=g.r, c=g.c,
            action=Action.FLAG,
            val=True, 
            kind=Action.GUESS,
            reasons=(f"GUESS - mine probability: {g.p_mine*100.0:6.2f}% (near-certain mine)",),
            score=g.p_mine
        ))

    if len(moves) > 0:
        return moves, True

    # 3) Otherwise do ONE safest click
    g0 = items[0]
    action = Action.FLAG if g0.p_mine > 0.5 else Action.OPEN 
    val = True if g0.p_mine > 0.5 else False 
    return [Move(
        r=g0.r, c=g0.c,
        action=action,
        kind=Action.GUESS,
        reasons=(f"GUESS - mine probability: {g0.p_mine*100.0:6.2f}% (best available)",),
        score=g0.p_mine,
        val=val
    )], False