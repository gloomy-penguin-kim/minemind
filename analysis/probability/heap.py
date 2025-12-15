from __future__ import annotations
from dataclasses import dataclass
from heapq import heappush, heappop
from typing import Callable, Dict, Iterable, List, Tuple, Optional


@dataclass(frozen=True, order=True)
class GuessItem:
    rating: float
    p_mine: float
    centerness: float
    r: int
    c: int

def build_guess_heap(all_probs: Dict[Tuple[int, int], float], rows: int, cols: int) -> List[GuessItem]:
    heap: List[GuessItem] = []
    for (r, c), p in all_probs.items():
        dr = r - (rows - 1) / 2.0
        dc = c - (cols - 1) / 2.0
        centerness = dr * dr + dc * dc
        rating = 1 - p if p > 0.5 else p
        heappush(heap, GuessItem(rating=rating, p_mine=p, centerness=centerness, r=r, c=c))
    return heap


def pop_candidates(
    heap: List[GuessItem],
    *,
    skip: Callable[[int, int], bool],
    stop_after_safe: bool,
    limit: Optional[int] = None,
) -> List[GuessItem]:
    """
    Pop guess candidates from heap.
    - skip(r,c) lets caller filter revealed/flagged/out-of-bounds/etc
    - if stop_after_safe=True: stop once we popped the first p_mine < 0.5 candidate
    - limit: max returned items
    """
    out: List[GuessItem] = []
    
    limit = max(5,len(heap)//4) if limit is None else limit 

    while heap and (limit is None or len(out) < limit):
        item = heappop(heap)
        if skip(item.r, item.c):
            continue
        out.append(item)
        if stop_after_safe and item.p_mine < 0.5:
            break
    return out
