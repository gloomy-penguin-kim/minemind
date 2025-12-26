from __future__ import annotations

from dataclasses import dataclass
from heapq import heappush
from typing import Dict, List, Tuple, Callable
 
from core.config import Config
from core.lru import LRUCache
from core.signatures import component_signature


from core.constants import CellType

@dataclass(frozen=True)
class ProbResult:
    solutions: int
    mine_counts: tuple[int, ...]


def enumerate_component(comp) -> ProbResult:
    k = comp.k
    constraints = comp.constraints

    base_remaining = [c.remaining for c in constraints]
    base_unknown = [c.mask_local.bit_count() for c in constraints]

    mine_counts = [0] * k
    total = 0
    assignment = [CellType.UNKNOWN] * k

    def dfs(pos: int, remaining: List[int], unknown: List[int]) -> None:
        nonlocal total, mine_counts

        if pos == k:
            if all(r == 0 for r in remaining):
                total += 1
                for i, v in enumerate(assignment):
                    if v == CellType.MINE:
                        mine_counts[i] += 1
            return

        for val in (CellType.SAFE, CellType.MINE):
            assignment[pos] = val

            rem2 = remaining[:]
            un2 = unknown[:]
            impossible = False

            for cid, cons in enumerate(constraints):
                if (cons.mask_local >> pos) & 1:
                    un2[cid] -= 1
                    if val == CellType.MINE:
                        rem2[cid] -= 1

                    if rem2[cid] < 0 or rem2[cid] > un2[cid]:
                        impossible = True
                        break
                    if un2[cid] == 0 and rem2[cid] != 0:
                        impossible = True
                        break

            if not impossible:
                dfs(pos + 1, rem2, un2)

            assignment[pos] = CellType.UNKNOWN

    dfs(0, base_remaining, base_unknown)
    return ProbResult(total, tuple(mine_counts))


def probs_for_component(
    comp,
    res: ProbResult,
    cols,
    skip_pred: Callable[[int, int], bool],
    board=None
) -> Dict[Tuple[int, int], float]:
    if res.solutions == 0:
        return {}

    out: Dict[Tuple[int, int], float] = {}
    for i, gid in enumerate(comp.local_to_global):
        r, c = divmod(gid, cols)
        if skip_pred(r, c):
            continue
        out[(r, c)] = res.mine_counts[i] / res.solutions

        test_invariantes_of_the_mines(board, out[(r,c)], r, c, comp)
    return out


def test_invariantes_of_the_mines(board, p, r, c, comp): 
    config = Config() 
    if config.invariants and board:  
        mines_in_comp = board.test_get_remaining_mines_per_component(comp.local_to_global)
        if board.revealed[r][c] or board.flagged[r][c]:
            raise AssertionError(f"probability assigned to revealed or flagged location for r={r},c={c},p={p}\n")
        if p == 0.0 and board.is_mine[r][c]:
            raise AssertionError(f"conflict in probability found at cell r={r},c={c},p={p}\n")
        if p == 1.0 and not board.is_mine[r][c]:
            raise AssertionError(f"conflict in probability found at cell r={r},c={c},p={p}\n") 
        if mines_in_comp == 0 and p > 0.0:
            raise AssertionError(f"zero mines in component, greather than 0 mine prob: r={r},c={c},p={p}")
        if mines_in_comp == comp.k and p < 1.0:
            raise AssertionError(f"all mines in component, less than 1 mine prob: r={r},c={c},p={p}")
        if not(0.0 <= p <= 1.0):
            raise AssertionError(f"mine probablity out of range (0.0..1.0): r={r},c={c},p={p}")


def build_guess_heap(all_probs: Dict[Tuple[int, int], float], rows: int, cols: int):
    heap = []
    for (r, c), p in all_probs.items():
        dr = r - (rows - 1) / 2.0
        dc = c - (cols - 1) / 2.0
        centerness = dr * dr + dc * dc
        rating = 1 - p if p > 0.5 else p
        heappush(heap, (rating, p, centerness, (r, c)))
    return heap


class ProbabilityEngine:
    def __init__(self, max_k: int = 60, cache_size: int = 1024):
        self.max_k = max_k
        self.cache = LRUCache(cache_size)

    def get_component_result(self, comp) -> ProbResult | None:
        if comp.k > self.max_k:
            return None

        sig = component_signature(comp)
        cached = self.cache.get(sig)
        if cached is not None:
            return cached

        res = enumerate_component(comp)
        self.cache.put(sig, res)
        return res

    def compute_probabilities(self, board, components):
        skip = lambda r, c: board.revealed[r][c] or board.flagged[r][c]

        all_probs: Dict[Tuple[int, int], float] = {}
        for comp in components:
            res = self.get_component_result(comp)
            if res is None:
                continue
            all_probs.update(probs_for_component(comp, res, board.cols, skip, board))

        return all_probs 
