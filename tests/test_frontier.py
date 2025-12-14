# from collections import OrderedDict
# import unittest
# import random 

# from core.dsu import DSU
# from analysis.frontier import dsu_find, _constraints_and_unknown_neighbors, build_frontier
# from core.board import Board
# from solver.solver import Solver 

# class TestFrontier(unittest.TestCase):

#     def assertComponentsEqual(self, components, expected_groups): 
#         actual_sets = {frozenset(v) for v in components.values()}
#         expected_sets = {frozenset(g) for g in expected_groups}
#         self.assertEqual(
#             actual_sets,
#             expected_sets,
#             msg=f"expected groups {expected_sets}, got {actual_sets}",
#         )


#     def test_dsu_no_overlap_masks_all_singletons(self): 
#         masks = [
#             (0, 0b001, 0), 
#             (0, 0b010, 0),
#             (0, 0b100, 0),
#         ]
#         comps = dsu_find(masks)
#         self.assertComponentsEqual(comps, [[0], [1], [2]])


#     def test_dsu_all_overlap(self):  
#         masks = [
#             (0, 0b0011, 0), 
#             (0, 0b0110, 0),
#             (0, 0b1100, 0),
#         ]
#         comps = dsu_find(masks)
#         self.assertComponentsEqual(comps, [[0, 1, 2]]) 


#     def test_dsu_two_separate_components(self):  
#         masks = [
#             (0, 0b0011, 0), 
#             (0, 0b0010, 0),
#             (0, 0b1100, 0),
#             (0, 0b1000, 0),
#         ]
#         comps = dsu_find(masks)
#         self.assertComponentsEqual(comps, [[0, 1], [2, 3]])


#     def test_global_unknowns(self):      
#         # how many unknowns are on the board in general 
#         for _ in range(25): 
#             rows, cols, num_mines = 9, 9, 10
#             seed = random.randint(0,10000)
#             board = Board(rows, cols, num_mines, seed) 

#             board.reveal_cell(random.randint(0,8), random.randint(0,8))

#             gids = []  
#             for i in range(rows): 
#                 for j in range(cols): 
#                     if not board.revealed[i][j]:
#                         gids.append(i * cols + j)

#             _, unknowns = _constraints_and_unknown_neighbors(board) 
#             gids = set(gids)
#             unknowns = set(unknowns)   

#             self.assertTrue(unknowns.issubset(gids))
       

# if __name__ == "__main__":
#     unittest.main()
