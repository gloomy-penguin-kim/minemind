
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