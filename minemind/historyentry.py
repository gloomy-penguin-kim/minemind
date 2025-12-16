from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from datetime import datetime

from analysis.rules.move import Move

Coord = Tuple[int, int]

# @dataclass
# class HistoryEntry:
#     move: "Move"
#     move_index_before: int

#     # only store cells that changed and their old values
#     revealed_prev: Dict[Coord, bool] = field(default_factory=dict)
#     flagged_prev: Dict[Coord, bool] = field(default_factory=dict)

#     # board-level fields that can change
#     remaining_safe_before: int = 0
#     game_over_before: bool = False
#     win_before: bool = False

#     # optional metadata
#     ts: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#     note: str = ""
 
from dataclasses import dataclass, field
from typing import Tuple

from analysis.rules.move import Move
from core.changes import ChangeSet


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    moves: tuple[Move, ...]          # batch (len 1 for normal actions)
    changes: ChangeSet              # combined changeset for the whole batch
    move_count_before: int
    note: str = ""