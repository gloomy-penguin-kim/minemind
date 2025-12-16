
from enum import Enum, IntEnum, auto


class CellType(Enum): 
    UNKNOWN = -1 
    SAFE  = 0
    MINE  = 1

class Action(IntEnum):
    OPEN  = auto()  
    FLAG  = auto() 
    CHORD = auto()

    STEP  = auto() 
    AUTO  = auto() 
    GUESS = auto() 
    RULE  = auto() 

KIND_NAMES = {
    Action.OPEN:   "open",
    Action.FLAG:   "flag",
    Action.CHORD:  "chord",
    Action.STEP:   "step",
    Action.AUTO:   "auto",
    Action.GUESS:  "guess", 
    Action.RULE:   "rule",
}
