# from __future__ import annotations
# from dataclasses import dataclass
# from heapq import heappush, heappop
# from typing import Callable, Dict, Iterable, List, Tuple, Optional

# from dataclasses import dataclass
# from typing import Dict, Tuple, List

# @dataclass(frozen=True, order=True)
# class GuessItem:
#     rating: float
#     p_mine: float
#     centrality: float
#     r: int
#     c: int 

# def build_guess_items(all_probs: Dict[Tuple[int,int], float], rows: int, cols: int) -> List[GuessItem]:
#     items: List[GuessItem] = []
#     for (r, c), p in all_probs.items():
#         dr = r - (rows - 1) / 2.0
#         dc = c - (cols - 1) / 2.0
#         centrality = dr*dr + dc*dc

#         rating = min(p, 1.0 - p)   # closer to 0/1 => smaller rating => “more certain”
#         items.append(GuessItem(rating=rating, p_mine=p, centrality=centrality, r=r, c=c))
#     return items


# def pop_candidates(
#     heap: List[GuessItem],
#     *,
#     skip: Callable[[int, int], bool],
#     stop_after_safe: bool,
#     limit: Optional[int] = None,
# ) -> List[GuessItem]:
#     """
#     Pop guess candidates from heap.
#     - skip(r,c) lets caller filter revealed/flagged/out-of-bounds/etc
#     - if stop_after_safe=True: stop once we popped the first p_mine < 0.5 candidate
#     - limit: max returned items
#     """
#     out: List[GuessItem] = []

#     while heap and (limit is None or len(out) < limit):
#         item = heappop(heap)
#         if skip(item.r, item.c):
#             continue
#         out.append(item)
#         if stop_after_safe and item.p_mine < 0.5:
#             break
#     return out


# SAFE_T = 0.05
# MINE_T = 0.95

# def rank_guess_items(items: List[GuessItem]) -> List[GuessItem]:
#     def bucket(g: GuessItem) -> int:
#         if g.p_mine <= SAFE_T or g.p_mine >= MINE_T:
#             return 0  # near-certain
#         return 1      # uncertain

#     # sort keys:
#     # (bucket, for uncertain: p_mine asc => safest click, then rating, then centrality)
#     return sorted(items, key=lambda g: (bucket(g), g.p_mine, g.rating, g.centrality))


# def select_hint_guess_list(ranked: List[GuessItem]) -> List[GuessItem]:
#     out: List[GuessItem] = []

#     # 1) include all near-certain
#     for g in ranked:
#         if g.p_mine <= SAFE_T or g.p_mine >= MINE_T:
#             out.append(g)

#     # 2) then include more until we include a SAFE click (< 0.5)
#     if any(g.p_mine < 0.5 for g in out):
#         return out  # already have a safe click in near-certain list

#     for g in ranked:
#         if g in out:
#             continue
#         out.append(g)
#         if g.p_mine < 0.5:
#             break

#     return out

# from analysis.rules.move import Move
# from core.constants import Action  # whatever your enum is
# from typing import Tuple
# from core.constants import Action 


# def guessitem_to_move(g: GuessItem) -> Move:
#     safety = (1.0 - g.p_mine) * 100.0
#     action = Action.FLAG if g.p_mine > 0.5 else Action.OPEN 
#     flag = True if g.p_mine > 0.5 else None
#     return Move(
#         r=g.r,
#         c=g.c,
#         action=action,           
#         kind=Action.GUESS,
#         reasons=(f"GUESS - mine probability: {g.p_mine*100.0:6.2f}% (safety {safety:6.2f}%)",),
#         score=g.p_mine,
#         val=flag
#     )

# def best_guess_moves_for_hint(self, all_probs):
#     items = build_guess_items(all_probs, self.board.rows, self.board.cols)
#     ranked = rank_guess_items(items)
#     chosen = select_hint_guess_list(ranked)
#     return [guessitem_to_move(g) for g in chosen]
