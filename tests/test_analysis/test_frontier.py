# #frontier.py – build “frontier” and components:
# #collect all numbered cells adjacent to unknowns
# #build constraints
# #build the intersection graph & use union–find to split into components.

# # build frontier, local indexing., component extraction 
 
# # core/frontier.py 
# from dataclasses import dataclass
# from typing import List, Tuple 
# from core.dsu import DSU   
# from core.board import Board  
# from core.config import config  

# import logging

# from core.utility import rc_to_gid 
# logger = logging.getLogger(__name__)
   
 

# def check_dsu_invariants(dsu: DSU, components, global_masks):
#     seen = []
#     for comp in components.values():
#         seen.extend(comp)
#     assert sorted(seen) == list(range(len(global_masks)))

#     n = len(dsu.parent)
#     # 1. roots are self-parent
#     for x in range(n):
#         r = dsu.find(x)
#         assert dsu.parent[r] == r

#     # 2. no parent points outside range
#     for x in range(n):
#         assert 0 <= dsu.parent[x] < n

#     # 3. rank: children cannot have higher rank than parents
#     for x in range(n):
#         p = dsu.parent[x]
#         if x != p:
#             assert dsu.rank[x] <= dsu.rank[p]

pass            