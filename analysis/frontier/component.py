
from dataclasses import dataclass
from typing import List, Tuple

from analysis.frontier.frontier import Constraint

 
class Component:
    k: int                               # number of local unknowns
    constraints: List[Constraint]        # constraints for this component
    local_to_global: List[int]           # len == k, each is a global cell id 
    prob: int = -1                       # number of maybe mines for render_heatmap 

    def local_coord(self, i: int, cols: int) -> Tuple[int, int]:
        gid = self.local_to_global[i]
        return divmod(gid, cols)