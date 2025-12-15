 
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Tuple, Optional

from core.changes import Action


class MoveKind(IntEnum):
    UNKNOWN = -1 
    SAFE  = 0
    MINE  = 1
    OPEN  = 2
    CHORD = 3
    FLAG  = 4
    STEP  = 5
    AUTO  = 6
    GUESS = 7


KIND_NAMES = {
    MoveKind.SAFE:  "safe",
    MoveKind.MINE:  "mine",
    MoveKind.OPEN:  "open",
    MoveKind.FLAG:  "flag",
    MoveKind.STEP:  "step",
    MoveKind.AUTO:  "auto",
    MoveKind.CHORD: "chord",
    MoveKind.GUESS: "guess",
}


@dataclass(frozen=True, slots=True)
class Move:
    r: int
    c: int

    # What Board will do
    action: Action

    # What CLI will *say* this move is (origin/label)
    kind: MoveKind = MoveKind.STEP

    # Human explanations
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    # Optional ranking (probability, etc.)
    score: Optional[float] = None

    def __str__(self) -> str:
        name = KIND_NAMES.get(self.kind, "unknown")
        return f"{name}: r={self.r},c={self.c}"

    def __repr__(self) -> str:
        name = KIND_NAMES.get(self.kind, "unknown")
        extra = f", reasons={list(self.reasons)!r}" if self.reasons else ""
        return f"Move({name}, r={self.r},c={self.c}{extra})"

    def var(self):
        # keep your old call sites working
        # note: "reason" used to be a single string; now it's tuple[str,...]
        reason = self.reasons[0] if self.reasons else None
        return self.r, self.c, int(self.kind), reason


class MoveList:
    def __init__(self, one=False):
        self.moves = {}
        self.conflicts = []
        self.one = one

    def add_move(self, move: Move):
        if self.one and len(self.moves) > 0:
            return
        rc = (move.r, move.c)
        if rc in self.moves:
            existing = self.moves[rc]
            if existing.kind != move.kind:
                self.conflicts.append(rc)
        else:
            self.moves[rc] = move

    def get_arrays(self):
        return list(self.moves.values()), self.conflicts[:]

    def __len__(self):
        return len(self.moves)


# UNKNOWN = -1 
# SAFE = 0 
# MINE = 1   
# OPEN = 2
# CHORD = 3 
# FLAG = 4 
# STEP = 5 
# AUTO = 6
# GUESS = 7


# KIND_NAMES = {
#     SAFE:  "safe",
#     MINE:  "mine",
#     OPEN:  "open",
#     FLAG:  "flag",
#     STEP:  "step",
#     AUTO:  "auto",
#     CHORD: "chord",
#     GUESS: "guess",
# }

# @dataclass(frozen=True)
# class Move:
#     r: int
#     c: int
#     action: Action
#     reasons: tuple[str, ...] = ()
#     score: float | None = None   # optional for probability ranking


# @dataclass
# class Move:
#     r: int
#     c: int
#     action: Action
#     kind: int
#     reason: Optional[str] = None
#     score: float | None = None 

#     def __str__(self) -> str:
#         name = KIND_NAMES.get(self.kind, "unknown")
#         if self.reason:
#             return f"{name}: r={self.r},c={self.c}"
#         return f"{name}: r={self.r},c={self.c}"

#     def __repr__(self) -> str:
#         name = KIND_NAMES.get(self.kind, "unknown")
#         return f"Move({name}, r={self.r},c={self.c}, reason={self.reason})"
    
#     def to_string(self) -> str: 
#         name = KIND_NAMES.get(self.kind, "unknown")
#         if self.reason:
#             return f"{name}: r={self.r},c={self.c}"
#         return f"{name}: r={self.r},c={self.c}"

#     def var(self):
#         """return raw tuple"""
#         return self.r, self.c, self.kind, self.reason
    
#     def __eq__(self, other): 
#         return self.r == other.r and self.c == other.c and self.kind == other.kind #and self.reason == other.reason 
    
#     def __lt__(self, other): 
#         if isinstance(other, Move):
#             if self.r == other.r: 
#                 if self.c == other.c: 
#                     if self.kind == other.kind:
#                         return self.reason < other.reason 
#                     return self.kind < other.kind
#                 return self.c
#             return self.r  
#         return NotImplemented 
    

# class MoveList:
#     def __init__(self, one=False): 
#         self.moves = {}  
#         self.conflicts: List[tuple] = [] 
#         self.one = one 
#     def add_move(self, move: Move): 
#         if not isinstance(move, Move): 
#             raise Exception(move)
#             return 
#         if self.one and len(self.moves) > 0: return 
#         rc = move.r, move.c
#         if (rc) in self.moves.keys(): 
#             move_existing = self.moves[rc]
#             if move_existing.kind != move.kind: 
#                 self.conflicts.append(rc)
#         else: 
#             self.moves[rc] = move 
#     def get_arrays(self):  
#         m = [] 
#         for k in self.moves:  
#             m.append(self.moves[k]) 
#         return m, self.conflicts[:]
#     def __len__(self): 
#         return len(self.moves) 