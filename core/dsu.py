# union find    
import logging 
logger = logging.getLogger(__name__)

class DSU:
    def __init__(self, n):
        self.parent = list(range(n)) 
        self.rank = [0] * n

    def find(self, x):
        # path compression
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b): 
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # union by rank
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def __repr__(self): 
        return f"DSU(parent={self.parent!r}, rank={self.rank!r})"
    
    