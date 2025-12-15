
def find_chords(b) -> list[tuple[int,int]]: 
    if b.game_over or not b.mines_placed:
        return []

    moves = []
    for r in range(b.rows):
        for c in range(b.cols):
            if not b.revealed[r][c]:
                continue
            n = b.adj[r][c]
            if n <= 0:
                continue

            flagged = 0
            unknown = 0
            for nr, nc in b.neighbors(r, c):
                if b.flagged[nr][nc]:
                    flagged += 1
                elif not b.revealed[nr][nc]:
                    unknown += 1

            if flagged == n and unknown > 0:
                moves.append((r, c))

    return moves



# def find_chords(self, r: int, c: int) -> ChangeSet:
#     cs = ChangeSet()

#     if self.game_over:
#         return cs
#     if not self.revealed[r][c]:
#         return cs

#     num_mines = self.adj[r][c]
#     if num_mines <= 0:
#         return cs

#     flagged = 0
#     unknowns: list[tuple[int,int]] = []

#     for nr, nc in self.neighbors(r, c):
#         if self.flagged[nr][nc]:
#             flagged += 1
#         elif not self.revealed[nr][nc]:
#             # if it's not revealed and not flagged, it's an unknown candidate
#             unknowns.append((nr, nc))

#     if flagged != num_mines:
#         return cs

#     # reveal all chord-opened neighbors
#     for nr, nc in unknowns:
#         sub = self.reveal_cell(nr, nc)   # ChangeSet
#         cs.revealed |= sub.revealed
#         cs.flagged  |= sub.flagged
#         cs.game_over = cs.game_over or sub.game_over
#         cs.win = cs.win or sub.win
#         if cs.game_over:  # optional short-circuit
#             break

#     return cs
