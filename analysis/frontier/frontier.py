#frontier.py – build “frontier” and components:
#collect all numbered cells adjacent to unknowns
#build constraints
#build the intersection graph & use union–find to split into components.

# build frontier, local indexing., component extraction 
 
# core/frontier.py 
from dataclasses import dataclass
from typing import List, Tuple 
from core.dsu import DSU   
from core.board import Board  
from core.config import config  

import logging

from core.utility import rc_to_gid 
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
   

@dataclass
class Constraint:
    mask_local: int         # bitmask over local unknown indices 0..k-1
    mask_global: int 
    remaining: int          # how many mines among bits set in mask
    def __repr__(self): 
        return f"Constraint(mask_local={bin(self.mask_local)}, mask_global={self.mask_global}, remaining={self.remaining})"
 

@dataclass
class Component:
    k: int                               # number of local unknowns
    constraints: List[Constraint]        # constraints for this component
    local_to_global: List[int]           # len == k, each is a global cell id 
    prob: int = -1                       # number of maybe mines for render_heatmap 

    def local_coord(self, i: int, cols: int) -> Tuple[int, int]:
        gid = self.local_to_global[i]
        return divmod(gid, cols)
    
  
 
def _constraints_and_unknown_neighbors(board: Board):
    """
    build a list of the neighbors (constraints) and their remainer (mines - flags)
    """
    rows, cols = board.rows, board.cols

    scopes = []
    seen = set()
    all_unknowns = set()

    for r in range(rows):
        for c in range(cols):

            # if the cell is not revealed, it is an unknown and cannot
            # give us any information right now so continue  
            if not board.revealed[r][c]:
                continue

            # get the number of the adjacent mines 
            adj_mines = board.adj[r][c]

            # if adjacent_mines is zero (safe) or a mine istelf, continue 
            if adj_mines <= 0:
                continue 

            # get a count of neighbors that are flagged
            # get an array of neighbors that are not flagged and not revealed
            flagged = 0
            unknown_neighbors = []
            for nr, nc in board.neighbors(r, c):
                if board.flagged[nr][nc]:
                    flagged += 1
                elif not board.revealed[nr][nc]:
                    unknown_neighbors.append((nr, nc))

            # if all our neighbors are known, continue 
            if not unknown_neighbors:
                continue

            # the remaining mines count is adjacent_mines - flagged neighbors 
            remaining = adj_mines - flagged

            # get the global id numbers for all our unknown neighbors for
            # this known cell, which becomes a scope 
            scope_gids = []
            for nr, nc in unknown_neighbors:
                gid = rc_to_gid(nr, nc, cols)
                scope_gids.append(gid)
                all_unknowns.add(gid)

            # add this to the list to the distinct array of scopes 
            key = (tuple(scope_gids), remaining)
            if key not in seen:
                seen.add(key)
                scopes.append((scope_gids, remaining))

    return scopes, sorted(all_unknowns)


def dsu_find(global_masks): 
    """
    DSU union find for the global masks w/ indicies 
    """
    C = len(global_masks)
    dsu = DSU(C)

    for i in range(C):
        _,maski,_ = global_masks[i] 
        for j in range(i + 1, C):
            _,maskj,_ = global_masks[j]  
            if maski & maskj:     
                dsu.union(i, j) 

    # {0: [0, 2, 3, 7, 9, 10], 1: [1, 4, 5, 6, 8, 11, 12, 14], 13: [13, 15]}
    components = {}
    for cid in range(C): 
        root = dsu.find(cid) 
        components.setdefault(root, []).append(cid) 

    if config.invariants: 
        check_dsu_invariants(dsu, components, global_masks) 

    return components 


def build_frontier(board): 
    """
    build the components based on the baoard for the frontier area(s) 
    """
    scopes, _ = _constraints_and_unknown_neighbors(board)  

    for i,scope in enumerate(scopes):
        logger.debug("%s: %s",i, scope) 
 
    # put those indicies in the global index bitmask!
    global_masks = [] 
    for i,(indicies,remaining) in enumerate(scopes):  
        logger.debug("%s: %s", i, indicies) 
        mask = 0 
        for index in indicies:  
            mask |= (1 << index)
        global_masks.append((indicies, mask, remaining))
    
    # if no bitmasks! return an empty array 
    if len(global_masks) == 0: 
        return []

    for g in global_masks:
        logger.debug("%s",g) 
    logger.debug("")

    # use DSU fo find overlopping areas with bitmasks! 
    components = dsu_find(global_masks)  

    comps = [] 
    for key in components:  
        scope = components[key] 

        # a set so there will be no duplictaes in our data 
        local_to_global = set()   

        # for each index in our overlapping scope get the 
        # global index value together now that we are working 
        # per component instead of for the whole board 
        for index in scope:  
            logger.debug("index %s, %s", index, scopes[index]) 
            l,r = scopes[index] 
            for s in l: 
                # create our distinct set of global indexes
                local_to_global.add(s)   
 
        # we can do this because numbers are naturally incrementing 
        # abd our board/grid is in order... 1,2,3... etc 
        local_to_global = sorted(list(local_to_global))  

        # create an associative array for the global to local conversion 
        # that happens later.  the index of array of global indexes is 
        # actually just the local_id for this association 
        global_to_local = {global_id: local for local, global_id in enumerate(local_to_global)}

        # for each index in schope, make a constraint 
        cons = []  
        for index in scope:  
            logger.debug("index %s, %s", index, scopes[index]) 

            # get the array of scopes which are global id's 
            arr,rem = scopes[index]  

            # for each global id in the scope array... 
            local_m = 0 
            for gid in arr:  
                # get the local id 
                local = global_to_local[gid]
                # make a list of the local id's 
                # put those local id's into a bitmask
                local_m |= (1 << local) 

            global_m = global_masks[index][1]
            remaining = global_masks[index][2]

            if config.invariants and rem != remaining: 
                raise AssertionError("the scope remaining number does not match the global mask remaining")

            logger.debug("locals=%s, bin_mask=%s, r=%s", locals, bin(local_m), remaining)

            # make a constraint with a local mask, global mask 
            # and remaining mines count that will be sorted 
            cons.append(Constraint(local_m, global_m, remaining)) 

        # build a Component with number of unknown cells in this range 
        # all of its constraints (sorted), and a list of global id's for
        # the unknown cells in this range 
        comps.append(Component(len(local_to_global), 
                               sorted(cons, key=lambda x: x.mask_local), 
                               local_to_global))

    # sort the components by their global indicies 
    comps = sorted(comps, key=lambda x: min(x.local_to_global))

    for comp in comps: 
        logger.debug("comp.k = %s",comp.k) 
        logger.debug("comp.local_to_global = %s",comp.local_to_global)
        for c in comp.constraints: 
            logger.debug("%s",c) 
    
    return comps 


def check_dsu_invariants(dsu: DSU, components, global_masks):
    seen = []
    for comp in components.values():
        seen.extend(comp)
    assert sorted(seen) == list(range(len(global_masks)))

    n = len(dsu.parent)
    # 1. roots are self-parent
    for x in range(n):
        r = dsu.find(x)
        assert dsu.parent[r] == r

    # 2. no parent points outside range
    for x in range(n):
        assert 0 <= dsu.parent[x] < n

    # 3. rank: children cannot have higher rank than parents
    for x in range(n):
        p = dsu.parent[x]
        if x != p:
            assert dsu.rank[x] <= dsu.rank[p]

            