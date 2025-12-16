 
from __future__ import annotations
 
from dataclasses import dataclass, field
from typing import Any, Tuple, Optional
from core.constants import Action, KIND_NAMES

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 


@dataclass(frozen=True, slots=True)
class Move:
    r: int
    c: int

    # What Board will do
    action: Action

    # What CLI will *say* this move is (origin/label)
    kind: Optional[Action] = Action.OPEN 

    # Human explanations
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    # Optional ranking (probability, etc.)
    score: Optional[float] = None

    # value to set falg 
    val: Optional[Any] = None

    def __str__(self) -> str:
        action = KIND_NAMES.get(self.action, "unknown")
        kind   = KIND_NAMES.get(self.kind, "unknown")
        t = f"- {kind}" if self.kind else ""  
        colon = ":" if len(self.reasons) > 0 else "" 
        return f"{action}: r={self.r},c={self.c} {t}{colon}"

    def __repr__(self) -> str:
        name = KIND_NAMES.get(self.kind, "unknown")
        extra = f", reasons={list(self.reasons)!r}" if self.reasons else ""
        return f"Move({name}, r={self.r},c={self.c}{extra})"
 

class MoveList:
    def __init__(self, one=False):
        self.moves = {}
        self.conflicts = dict() 
        self.one = one

    def add_move(self, move: Move):
        if self.one and len(self.moves) > 0:
            return
        rc = (move.r, move.c)
        if rc in self.moves:
            existing = self.moves[rc]
            if existing.action != move.action:
                if rc not in self.conflicts: 
                    self.conflicts[rc] = [] 
                if existing.reasons[0] not in self.conflicts[rc]:
                    self.conflicts[rc].append(existing.reasons[0])
                if move.reasons[0] not in self.conflicts[rc]:
                    self.conflicts[rc].append(move.reasons[0]) 
                del self.moves[rc] 
        else:
            self.moves[rc] = move

    def get_arrays(self): 
        return list(self.moves.values()), self.conflicts.items() 

    def __len__(self):
        return len(self.moves)
