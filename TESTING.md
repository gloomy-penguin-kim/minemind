## Test Files Overview

#### 1. `test_board.py`

- Initial state
  - Board(rows=3, cols=3, num_mines=1, seed=42)
  - Verifies:
    - mines_placed == False
    - game_over == False
    - win == False
    - _remaining_safe is rows*cols - num_mines
    - All cells unrevealed and unflagged.  

- Deterministic 9×9 board from seed & first click
  - Board(9, 9, 10, seed=0); reveal_cell(3, 3)
  - Asserts is_mine and adj exactly match tests/test_board.json.  

- Adjacency consistency property test
  - For 200 random seeds:
    - Build a 9×9 board with 10 mines.
    - For every cell with adj[r][c] > 0, recompute adjacent mine count from is_mine and assert equality.  

- Revealing safe cells
  - For random boards:
    - After an initial reveal at (3, 3), every non-mine cell can be revealed:
    - revealed[r][c] == True
    - is_mine[r][c] == False
    - flagged[r][c] == False.  

- Revealing a mine
  - Find a mine cell, reveal it, and assert:
    - That cell is still not marked as revealed
    - is_mine[row][col] == True
    - game_over == True
    - win == False. 
    - test_board

- Flood-reveal with zero mines
  - On a 9×9 board with num_mines=0:
    - Reveal (1, 1)
    - All cells become revealed
    - game_over == True
    - win == True
    - _remaining_safe == 0. 
 
- Chord behavior (good case)
  - On many random boards, for any numbered cell where:
    - There are more neighbors than the number on the cell
    - You reveal it, flag all the true mines around it, and then call chord(i, j)
    - After chording, all neighbors are either revealed or flagged. 

-Chord behavior (bad case)
  - On a fixed board:
    - Reveal (3, 3), then (0, 1), then chord(0, 1)
    - asserts that specific neighbors remain unrevealed (no accidental mass-reveal).

#### 2. `test_generator.py`

- Determinism with same seed + first click
  - Same (rows, cols, num_mines, seed, first_click) → identical is_mine and adj. 

- Changing seed changes layout
  - Same params but different seed → different layouts. 

- Changing first click changes layout
  - Same seed, different first_click positions → different layouts. 

- First click region is always safe (property test)
  - For 200 random board sizes and first clicks:
    - num_mines ≈ 15% of the board
    - Asserts that the first click cell and all its neighbors are not mines. 
 
- Mine count correctness
  - Counts True values in is_mine and checks it equals num_mines.  

- Golden 9×9 layout
  - Rebuilds the same canonical 9×9/10-mine board with seed 0 and first click (3,3), and compares to `test_board.json`. 

#### 3. `test_solver_small.py`

Known probability map on fixed board
  - Loads test_board.json, builds a Board, runs Solver(board).prob(), and compares the returned probability dict to a hard-coded expected dict. 
  - Validates the exact mine probability per cell on this canonical board.

- Known first step behavior
  - On the same board:
    - solver.step()
    - Asserts that a specific cell (0,2) ends up flagged. 

- Hand-rolled probability solver matches Solver.prob()
  - Uses _constraints_and_unknown_neighbors and a plain backtracking enumerator over assignments to:
    - Enumerate all valid mine assignments for each DSU component
    - Compute exact probabilities for each unknown cell
  - Then compares these probabilities to Solver.prob() on a board built from Board(9,9,10,seed=0) with first click (3,3). 
  - Asserts assertAlmostEqual(..., places=9) for each cell’s probability. 

- Large board probability computation smoke test
  - Board(16, 16, num_mines=41, seed=0) with first click (7,7).
  - Sets solver.max_k = 55 and asserts that prob() returns at least one probability (not empty).


#### 4. `test_frontier.py`

- DSU mask grouping behavior via dsu_find:
  - No overlap → all singletons
    - Three disjoint masks → three single-element components. 
  - All overlap → one component
    - Three pairwise-overlapping masks all end up in the same DSU component. 
  - Two separate components
    - Overlapping pairs forming exactly two connected components. 

- Global unknown set containment
  - On many random boards:
    - After an initial reveal, gathers all unrevealed cells as global IDs.
    - Calls _constraints_and_unknown_neighbors(board), takes the returned unknowns, and asserts unknowns ⊆ all_unrevealed. 

- Frontier / component construction smoke test (test_stuff)
  - On a 9×9 board with the canonical (3,3) click:
    - Builds scopes from _constraints_and_unknown_neighbors
    - Builds global_masks

- Runs dsu_find
  - Uses the result to build Component and Constraint structures
  - There are currently no assertions here; it's effectively a smoke test that component construction doesn’t crash. 


#### 5. `test_rules.py`

- Uses a DummyBoard with only rows, cols, revealed, and flagged to isolate rule logic from actual board generation. 

- Helper compare_move_r_c_kind ensures that Move objects match in (r, c, kind) regardless of reason text. 

- Singles via apply_rules
  - Sets up a Component where a constraint’s mask_local selects two local indices and remaining == 0.
  - Asserts that those two cells are emitted as SAFE moves at the correct (r, c). 

- get_indicies_from_bitmask utility
  - Verifies that a mask with bits at 1, 2, and 4 returns exactly [1, 2, 4]. 

- Singles via _apply_singles directly
  - Remaining 0, therefore all cells in the scope are SAFE. 
  - Remaining |scope| therefore all cells in the scope are MINE. 

- Subset rule (A ⊂ B)
  - Case 1: a == b → B \ A are SAFE. 
  - Case 2: b - a == |B \ A| → B \ A are MINE