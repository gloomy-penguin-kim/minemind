# core/changes.py
from dataclasses import dataclass, field 
from typing import Tuple

Coord = Tuple[int, int]


@dataclass(frozen=True)
class ChangeSet:
    revealed: frozenset[Coord] = field(default_factory=set)
    flagged: frozenset[Coord] = field(default_factory=set)
    game_over: bool = False
    win: bool = False

    @property
    def empty(self) -> bool:
        return len(self.revealed) == 0 and len(self.flagged) == 0 and not self.game_over
        
    def __bool__(self) -> bool:
        # Always consider it a "valid result"
        return True

    def merged(self, other: "ChangeSet") -> "ChangeSet":
        return ChangeSet(
            revealed=self.revealed | other.revealed,
            flagged=self.flagged | other.flagged,
            game_over=other.game_over,
            win=other.win,
        )

@dataclass
class Delta:
    revealed_flips: list[tuple[int,int,bool]]  # (r,c,old_value)
    flagged_flips: list[tuple[int,int,bool]]
    remaining_safe_old: int
    game_over_old: bool
    win_old: bool