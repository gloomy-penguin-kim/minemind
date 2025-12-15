from typing import List, Tuple, Iterable, Any

from core.changes import ChangeSet, Action 
from core.generator import generate_board
from core.config import config 

from dataclasses import dataclass
from typing import Set, Tuple

import logging

from analysis.rules.move import MoveKind, Move

# logger = logging.getLogger(__name__) 

class Board:
    def __init__(self, rows: int, cols: int, num_mines: int, seed: int = 0, invariants: bool = True) -> None:
        """Initialize a minesweeper board."""
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.seed = seed

        self.is_mine: List[List[bool]] = [[False] * cols for _ in range(rows)]
        self.adj: List[List[int]] = [[0] * cols for _ in range(rows)]
        self.revealed: List[List[bool]] = [[False] * cols for _ in range(rows)]
        self.flagged: List[List[bool]] = [[False] * cols for _ in range(rows)]

        self.mines_placed: bool = False
        self.game_over: bool = False
        self.win: bool = False

        self.moves: int = 0 

        self._remaining_safe: int = rows * cols - num_mines  

        self._undo_stack: list[ChangeSet] = [] 
    

    def neighbors(self, r: int, c: int) -> Iterable[Tuple[int, int]]:
        """Yield all valid neighbor coordinates of (r, c)."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc


    def build_board(self, first_r: int, first_c: int) -> None:
        """Place mines and adjacencies after the first click."""
        if self.mines_placed:
            return

        is_mine, adj = generate_board(
            rows=self.rows,
            cols=self.cols,
            num_mines=self.num_mines,
            seed=self.seed,
            first_click=(first_r, first_c),
        )

        self.is_mine = is_mine
        self.adj = adj
        self.mines_placed = True


    def apply(self, action: Action, r: int, c: int) -> ChangeSet:
        """
        The only place that mutates board state.
        """
        before_revealed = set()
        before_flagged = set()

        # snapshot old state for diff
        for i in range(self.rows):
            for j in range(self.cols):
                if self.revealed[i][j]:
                    before_revealed.add((i, j))
                if self.flagged[i][j]:
                    before_flagged.add((i, j))

        if action == Action.OPEN:
            self.reveal_cell(r, c)
        elif action == Action.FLAG:
            self.toggle_flag(r, c)
        elif action == Action.CHORD:
            self.chord(r, c)

        # compute diffs
        after_revealed = {
            (i, j)
            for i in range(self.rows)
            for j in range(self.cols)
            if self.revealed[i][j]
        }
        after_flagged = {
            (i, j)
            for i in range(self.rows)
            for j in range(self.cols)
            if self.flagged[i][j]
        }

        cs = ChangeSet(
            revealed=after_revealed - before_revealed,
            flagged=after_flagged - before_flagged,
            game_over=self.game_over,
            win=self.win,
        )  
        return cs 
    

    def _apply_move(self, move: Move) -> ChangeSet | None: 
        return self.apply(move.action, move.r, move.c)

 
    def undo(self, changes: ChangeSet):
        for cell, prev in reversed(changes.cells):
            r, c = cell
            self.revealed[r][c] = prev.revealed
            self.flagged[r][c] = prev.flagged
            self.adj[r][c] = prev.adj 
        

    def reveal_cell(self, r: int, c: int) -> ChangeSet:
        if self.game_over or self.revealed[r][c] or self.flagged[r][c]:
            return ChangeSet()

        if not self.mines_placed:
            self.build_board(r, c)

        # Mine click
        if self.is_mine[r][c]:
            self.revealed[r][c] = True
            self.game_over = True 
            self.win = False 
            return ChangeSet(
                revealed={(r, c)},
                flagged=set(), 
                game_over=True,
                win=False
            )

        # Safe click
        revealed = self._flood_reveal(r, c)

        win_cs = self._check_win_condition()

        return ChangeSet(
            revealed=revealed | win_cs.revealed,
            flagged=win_cs.flagged,
            game_over=self.game_over,
            win=self.win,
        )


    def _flood_reveal(self, r: int, c: int) -> set[tuple[int,int]]:
        revealed = set()
        stack = [(r, c)]

        while stack:
            cr, cc = stack.pop()

            if self.revealed[cr][cc]:
                continue
            if self.flagged[cr][cc]:
                continue
            if self.is_mine[cr][cc]:
                continue

            self.revealed[cr][cc] = True
            revealed.add((cr, cc))
            self._remaining_safe -= 1

            if self.adj[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        stack.append((nr, nc))

        return revealed


    def _check_win_condition(self) -> ChangeSet:
        flagged = set() 
        if self._remaining_safe <= 0 and not self.game_over:
            for i in range(self.rows):
                for j in range(self.cols):
                    if not self.revealed[i][j] and not self.flagged[i][j]:
                        self.flagged[i][j] = True
                        flagged.add((i, j))

            self.win = True
            self.game_over = True
            # cs.win = True
            # cs.game_over = True

        return ChangeSet(
            revealed=set(),
            flagged=flagged,
            game_over=self.game_over,
            win=self.win,
        ) 



    def toggle_flag(self, r: int, c: int) -> ChangeSet: 

        if self.game_over or self.revealed[r][c]:
            return ChangeSet(
                revealed=set(),
                flagged=set(),
                game_over=self.game_over,
                win=self.win,
            )  
        flagged = set()

        self.flagged[r][c] = not self.flagged[r][c]
        flagged.add((r, c))

        # merge in win-condition changes (auto-flagging)
        win_cs = self._check_win_condition() 

        return ChangeSet(
            revealed=set(),
            flagged=flagged | win_cs.flagged,
            game_over=win_cs.game_over,
            win=win_cs.win,
        )
        return cs 
    

    def chord(self, r: int, c: int) -> ChangeSet:
        cs = ChangeSet()

        num_mines = self.adj[r][c]
        if self.game_over or not self.revealed[r][c] or num_mines <= 0:
            return ChangeSet(
                revealed=set(),
                flagged=set(),
                game_over=self.game_over,
                win=self.win,
            )   

        flagged = 0
        unknowns: list[tuple[int,int]] = []

        for nr, nc in self.neighbors(r, c):
            if self.flagged[nr][nc]:
                flagged += 1
            elif not self.revealed[nr][nc]:
                # if it's not revealed and not flagged, it's an unknown candidate
                unknowns.append((nr, nc))

        if flagged != num_mines:
            return cs

        game_over, win = False, False 
        revealed, flagged = set(), set() 
        # reveal all chord-opened neighbors
        for nr, nc in unknowns:
            sub = self.reveal_cell(nr, nc)   # ChangeSet
            revealed |= sub.revealed
            flagged  |= sub.flagged
            game_over = game_over or sub.game_over
            win = win or sub.win
            if game_over:   
                break

        return ChangeSet(
            revealed=revealed,
            flagged=flagged,
            game_over=game_over,
            win=win,
        )


    def chords(self) -> List[Tuple[int, int]]:
        """Find all coordinates where a chord is possible."""
        moves: List[Tuple[int, int]] = []
        for i in range(self.rows):
            for j in range(self.cols):
                if self.revealed[i][j] and self.adj[i][j] > 0:
                    flagged = 0
                    revealed = 0
                    neighbors = 0
                    for (nr, nc) in self.neighbors(i, j):
                        if self.flagged[nr][nc]:
                            flagged += 1
                        if self.flagged[nr][nc] or self.revealed[nr][nc]:
                            revealed += 1
                        neighbors += 1
                    if flagged == self.adj[i][j] and revealed != neighbors:
                        moves.append((i, j))
        return moves


    def count_flags_on_board(self) -> int:
        """Count how many flags are placed on the board."""
        flags = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if self.flagged[i][j]:
                    flags += 1
        return flags 


    def count_unkown_cells(self) -> int: 
        """Count how many unknown cells are on the board."""
        unknowns = 0 
        for i in range(self.rows):
            for j in range(self.cols):
                if not self.revealed[i][j] and not self.flagged[i][j]:
                    unknowns += 1 
        return unknowns


    def count_revealed_cells(self) -> int: 
        """Count how many revealed cells are on the board."""
        revealed = 0 
        for i in range(self.rows):
            for j in range(self.cols):
                if self.revealed[i][j]:
                    revealed += 1 
        return revealed


    def verify_all_existing_flags_found(self) -> List[Tuple[int, int, bool]]:
        """Return list of (r,c,correct) for each existing flag."""
        total_found = 0
        total_flagged = 0
        messages: List[Tuple[int, int, bool]] = []
        for i in range(self.rows):
            for j in range(self.cols):
                if self.flagged[i][j]:
                    if not self.is_mine[i][j]:
                        messages.append((i, j, False))
                    else:
                        messages.append((i, j, True))
                        total_flagged += 1
                if self.is_mine[i][j]:
                    total_found += 1
        return messages 
    
     
    def undo(self, cs: ChangeSet):
        for r, c in cs.revealed:
            self.revealed[r][c] = False
        for r, c in cs.flagged:
            self.flagged[r][c] = False
        self.game_over = False
        self.win = False
        self._remaining_safe = (self.rows * self.cols - self.num_mines) - self.count_revealed_cells()


    # ---------------- Debug helpers ----------------


    def render_board(self, reveal_all: bool = False) -> None:
        """Print an ASCII representation of the board."""
        def cell_char(r: int, c: int) -> str:
            if reveal_all:
                if self.is_mine[r][c]:
                    return '*'
                if self.adj[r][c] == 0:
                    return ' '
                return str(self.adj[r][c])

            if self.revealed[r][c]:
                if self.is_mine[r][c]:
                    return '*'
                if self.adj[r][c] == 0:
                    return ' '
                return str(self.adj[r][c])
            else:
                if self.flagged[r][c]:
                    return 'F'
                return '.'

        print(f"Moves: {self.moves}\n")
        print("   " + " ".join(f"{c:2}" for c in range(self.cols)))
        for r in range(self.rows):
            row_str = " ".join(f"{cell_char(r, c):2}" for c in range(self.cols))
            print(f"{r:2} {row_str}")
        print()


    # ---------------- Invariant helpers ----------------    


    def test_flagged_mines_and_unknowns(self) -> bool:
        """Check invariant: flagged mines count <= unknown cells."""
        if not config.invariants:
            return True
        total_mines = 0
        total_unknown = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if self.is_mine[i][j] and self.flagged[i][j]:
                    total_mines += 1
                if not self.revealed[i][j]:
                    total_unknown += 1 
        if total_mines > total_unknown:
            raise AssertionError(
                f"total_mines({total_mines}) > total_unknown({total_unknown})"
            )
        return True


    def test_adj_numbers(self) -> bool:
        """Check that adj[r][c] matches the count of neighboring mines."""
        if not config.invariants:
            return True
        for i in range(self.rows):
            for j in range(self.cols):
                mines_recorded = self.adj[i][j]
                if mines_recorded > 0:
                    mines_found = 0
                    for nr, nc in self.neighbors(i, j):
                        if self.is_mine[nr][nc]:
                            mines_found += 1
                    if mines_recorded != mines_found:
                        raise AssertionError(
                            f"mines_recorded({mines_recorded}) != "
                            f"mines_found({mines_found}), r={i},c={j}"
                        )
        return True


    def test_mines_not_revealed(self) -> bool:
        """Check that no mine is revealed unless game_over is True."""
        if not config.invariants:
            return True
        if self.game_over:
            return True
        for i in range(self.rows):
            for j in range(self.cols):
                if self.is_mine[i][j] and self.revealed[i][j]:
                    raise AssertionError(
                        f"a mine has been revealed and it shouldn't have been: r={i},c={j}"
                    )
        return True


    def test_previous_state(self, prev: dict[str, Any], changed: List[Tuple[int, int]]) -> bool: 
        """Check that only cells in 'changed' differ from previous state."""
        if not config.invariants:
            return True

        if prev["adj"] != self.adj:
            raise AssertionError("prev.adj != self.adj and they should always be equal.")
        if prev["is_mine"] != self.is_mine:
            raise AssertionError("prev.is_mine != self.is_mine and they should always be equal.")

        for i in range(self.rows):
            for j in range(self.cols):
                if prev["flagged"][i][j] != self.flagged[i][j]: 
                    if (i, j) not in changed:
                        raise AssertionError(
                            f"a cell was changed and it shouldn't have been (flagged): r={i},c={j}"
                        )
                if prev["revealed"][i][j] != self.revealed[i][j]: 
                    if (i, j) not in changed:
                        raise AssertionError(
                            f"a cell was changed and it shouldn't have been (revealed): r={i},c={j}"
                        )
        return True


    def test_get_remaining_mines_per_component(self, unknowns: List[int]) -> int:
        """Return count of true, unflagged, unrevealed mines in a component."""
        mines = 0
        for g in unknowns:
            r, c = divmod(g, self.cols)
            if self.is_mine[r][c] and not self.flagged[r][c] and not self.revealed[r][c]:
                mines += 1
        return mines


    def test_cells_cannot_be_flagged_and_revealed(self) -> bool:
        """Check that no cell is both flagged and revealed."""
        if not config.invariants:
            return True
        for i in range(self.rows):
            for j in range(self.cols):
                if self.revealed[i][j] and self.flagged[i][j]:
                    raise AssertionError(
                        f"a cell is both revealed and flagged at r={i},c={j}"
                    )
        return True