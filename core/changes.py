# core/changes.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Set, Tuple

Coord = Tuple[int, int]

class Action(Enum):
    OPEN = auto()
    FLAG = auto()
    CHORD = auto()

@dataclass
class ChangeSet:
    revealed: Set[Coord] = field(default_factory=set)
    flagged: Set[Coord] = field(default_factory=set)
    game_over: bool = False
    win: bool = False
    note: str = ""

@dataclass
class Delta:
    revealed_flips: list[tuple[int,int,bool]]  # (r,c,old_value)
    flagged_flips: list[tuple[int,int,bool]]
    remaining_safe_old: int
    game_over_old: bool
    win_old: bool