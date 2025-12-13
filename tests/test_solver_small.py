from collections import OrderedDict, defaultdict
import unittest
import random 
import json 

from core.board import Board
from core.frontier import  _constraints_and_unknown_neighbors
from core.snapshot import _create_board_from_object
from core.solver import Solver  

from core.rules import (
    SAFE,
    MINE,
    UNKNOWN, 
)
from core.dsu import DSU 

import logging 
logger = logging.getLogger(__name__)
 
 
class TestSolver(unittest.TestCase):


    # just verifying that my probabilities are still working on a small, 
    # known board.  
    def test_known_probabilities(self): 
        known_probs = {(0, 1): 0.0, (0, 2): 1.0, (1, 1): 0.0, (2, 1): 1.0, 
                       (3, 0): 0.0, (3, 1): 1.0, (0, 6): 0.0, (1, 6): 1.0, 
                       (1, 7): 0.0, (1, 8): 0.0, (2, 8): 0.0, (3, 8): 0.0, 
                       (4, 8): 1.0, (5, 8): 1.0, (7, 4): 1.0, (8, 4): 0.0}
        

        with open("./tests/test_board.json", 'r') as f: 
            obj = json.load(f) 

        board = _create_board_from_object(obj) 
 
        solver = Solver(board) 
        all_probs, _ = solver.prob()

        self.assertEqual(all_probs, known_probs)


    # tests a known board with a known first step 
    def test_known_a_known_step(self):    
        with open("./tests/test_board.json", 'r') as f: 
            obj = json.load(f)  
        board = _create_board_from_object(obj)  
        solver = Solver(board) 
        solver.step() 
        self.assertTrue(board.flagged[0][2])  
 

    # a test without the component/constraint classes and without the bitmask 
    def test_probabilities(self):     
        with open("./tests/test_board.json", 'r') as f: 
            obj = json.load(f)  
        board = _create_board_from_object(obj)  
        scopes, base_unknown = _constraints_and_unknown_neighbors(board)  
        
        scopes.sort() 
 
        chocolate = OrderedDict() 
        vanilla = []  
        for i, scope in enumerate(scopes):  
            chocolate[tuple(scope[0])] = len(scope[0]), scope[1]
            vanilla.append(tuple(scope[0]))  
   
        C = len(scopes)
        dsu = DSU(C)
 
        for i in range(C):
            mi,remi = scopes[i]
            mi = set(mi) 
            for j in range(i + 1, C):
                mj,remj = scopes[j]
                mj = set(mj)  
                if mi.intersection(mj):     
                    dsu.union(i,j)

        dsu_components = OrderedDict() 
        for cid in range(C): 
            root = dsu.find(cid) 
            dsu_components.setdefault(root, []).append(cid) 

        base_unknown = sorted(list(base_unknown))
 
        us = [] 
        rs = []  
        clogarr= []  
        uknown_soldiers= [] 
        for comp in dsu_components:  
            u = [] 
            r = [] 
            cl = [] 
            cg = set() 
            for local in dsu_components[comp]:  
                u_num,r_num = chocolate[vanilla[local]] 
                cl.append(vanilla[local])
                cg.add(base_unknown[local])
                u.append(u_num) 
                r.append(r_num)  

            us.append(u)
            rs.append(r) 
            uknown_soldiers.append(sorted(list(cg)))
            clogarr.append(cl)   
 

        all_probs = {} 
        for compi,root in enumerate(dsu_components): 
 
            uu = us[compi] 
            rr = rs[compi] 
            constraints = clogarr[compi] 
            usoldiers = uknown_soldiers[compi] 
 
            aa = [UNKNOWN] * len(uu) 
            k = len(uu) 
            total_solutions = 0 
            mine_counts = [0] * len(uu)  
            
            def recursion(pos, r, u, a):
                nonlocal k, constraints, usoldiers
                nonlocal total_solutions, mine_counts

                if pos == k:
                    # all unknowns assigned: all constraints must have 0 mines remaining
                    for remaining in r:
                        if remaining != 0:
                            return
                    total_solutions += 1
                    for i in range(k):
                        if a[i] == MINE:
                            mine_counts[i] += 1
                    return

                number = usoldiers[pos]

                for safe_o_mine in (SAFE, MINE):
                    # each branch gets a fresh copy
                    r2 = r[:]
                    u2 = u[:]
                    impossible = False
                    a[pos] = safe_o_mine

                    remaining_cells = k - pos
                    min_mines_assigned = a[:pos].count(1) 
                    max_mines_assinged = min_mines_assigned + remaining_cells

                    for cid, con in enumerate(constraints):
                        if number in con: 
                            u2[cid] -= 1
                            if safe_o_mine == MINE:
                                r2[cid] -= 1

                            if r2[cid] < 0:
                                impossible = True
                                break

                            if r2[cid] > u2[cid]:
                                impossible = True
                                break
                            
                            # no unknowns left but non-zero mines remaining:
                            if u2[cid] == 0 and r2[cid] != 0:
                                impossible = True
                                break 

                            # too many mines already
                            if min_mines_assigned > max_mines_assinged:
                                impossible = True

                            # even if all remaining were mines, you can't reach the minimum
                            if max_mines_assinged + remaining_cells < min_mines_assigned:
                                impossible = True

                    if not impossible:
                        recursion(pos + 1, r2, u2, a)

                a[pos] = UNKNOWN
         
            recursion(0, rr, uu, aa)
  
            self.assertTrue(total_solutions > 0)
            # print("total_solutions", total_solutions)
            # print("mine_counts", mine_counts)
          
            solutions = total_solutions
            if solutions == 0: 
                continue

            mine_counts = mine_counts
 
            for i,unknowns in enumerate(usoldiers):  
                r, c = divmod(unknowns, board.cols) 
                if board.revealed[r][c] or board.flagged[r][c]:
                    continue 
                mine_probability = mine_counts[i] / solutions
                all_probs[(r, c)] = mine_probability 
 
        board = Board(rows=9, cols=9, num_mines=10, seed=0)
        board.reveal_cell(3, 3) 
        solver = Solver(board) 
        all_probs_auto, _  = solver.prob() 
 
        for i in range(board.rows): 
            for j in range(board.cols):
                if (i,j) in all_probs_auto:     
                    self.assertAlmostEqual(
                        all_probs_auto[(i, j)],
                        all_probs[(i, j)],
                        places=9
                    )
 

    def test_probabilities_return_large_board(self):       
        board = Board(rows=16, cols=16, num_mines=41, seed=0)
        board.reveal_cell(7, 7) 
        solver = Solver(board) 
        solver.max_k = 55
        all_probs_auto, _  = solver.prob() 
        self.assertTrue(len(all_probs_auto) > 0)






if __name__ == "__main__":
    unittest.main()
