from typing import List

def get_indicies_from_bitmask(mask) -> List[int]: 
    """Return zero-based indices of bits set in a bitmask."""
    indices: List[int] = [] 
    while mask:
        lsb = mask & -mask
        bit = lsb.bit_length() - 1
        # get those bits out of there! 
        indices.append(bit)
        mask ^= lsb 
    return indices
 

def put_indicies_into_a_bitmask(arr):
    for index in arr:   
        mask |= (1 << index)


def rc_to_gid(r, c, cols):
    return r * cols + c 
 