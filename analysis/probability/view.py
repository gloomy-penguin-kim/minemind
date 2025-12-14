# def prob_view(self) -> ProbView:
#     p_mine, heap = self.prob()  # keep your current enumeration logic
#     ranked = []
#     for (r,c), pm in p_mine.items():
#         ranked.append((r,c, pm, (1-pm)*100.0))
#     ranked.sort(key=lambda t: t[2])  # most safe first (lowest mine prob)
#     return ProbView(p_mine=p_mine, ranked=ranked)

# @dataclass
# class FrontierView:
#     num_components: int
#     summary: List[Tuple[int,int,int]]  # (idx, k, m)
#     # optionally: full components for verbose print
#     components: Any
