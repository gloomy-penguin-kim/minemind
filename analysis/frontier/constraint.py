
from dataclasses import dataclass 

@dataclass
class Constraint:
    mask_local: int         # bitmask over local unknown indices 0..k-1
    mask_global: int 
    remaining: int          # how many mines among bits set in mask
    def __repr__(self): 
        return f"Constraint(mask_local={bin(self.mask_local)}, mask_global={self.mask_global}, remaining={self.remaining})"
 