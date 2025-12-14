# core/rng.py
import random
from typing import Sequence, TypeVar, List

T = TypeVar("T")


class RNG: 

    def __init__(self, seed: int, rows, cols, mines, row, col):
        self.hash = hash((seed, rows, cols, mines, row, col))
        self._rng = random.Random(self.hash)

    def shuffle(self, seq: List[T]) -> None: 
        self._rng.shuffle(seq)

    def randint(self, a: int, b: int) -> int: 
        return self._rng.randint(a, b) 
 
