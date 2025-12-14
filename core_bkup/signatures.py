# canonical component signature 
 
from typing import Tuple
from .frontier import Component  

# Signature = (k, (sorted_masks...), (sorted_remaining...))
Signature = Tuple[int, Tuple[int, ...], Tuple[int, ...]]


def component_signature(comp: Component) -> Signature:
    """
    get the hash on 
    """
    k = comp.k

    # Extract (mask, remaining) for each constraint
    pairs = [(c.mask_global, c.remaining) for c in comp.constraints]
 
    pairs.sort(key=lambda p: (p[0], p[1]))

    scopes = tuple(p[0] for p in pairs)
    rems   = tuple(p[1] for p in pairs)

    return (k, scopes, rems)
