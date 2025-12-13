
---

## 4. `COMPLEXITY.md`

##### ChatGPT did absolutely help me establish this document so that it makes sense and is correct.  Some of the code has been modified for more efficiency since I analyzed it, however, the basics remain the same.  `invariants --on` mode does change the complexity quite a bit and is not included in this since it is an optional feature that is not necessary for basic game play.  

```markdown
# MineMind Complexity

This document describes the time/space complexity of core operations.

Let:

- `R` = number of rows
- `C` = number of columns
- `N = R * C` = total cells
- `d` ≈ average number of neighbors (~8 for interior)
- `k` = number of unknown cells in a frontier component
- `k_max` = cutoff for enumeration (e.g., 20)
- `m` = number of constraints in a component

---

## 1. `open(r, c)`

### Single-cell reveal

- Checking if `(r, c)` is a mine or number is `O(1)`:
  - Access `is_mine[r][c]` or `adj[r][c]`.

### Flood reveal (zeros)

When `adj[r][c] == 0`, we BFS/DFS to reveal:

- Worst-case visits every cell once: `O(N)`.
- Each visited cell processes its neighbors: `O(d)` per cell, so still `O(N)`.

**Time**:
- Best case (non-zero cell): `O(1)`
- Worst case (zero-region flood): `O(N)`

**Space**:
- BFS queue / DFS stack: `O(N)` in worst case.

---

## 2. Building the Frontier

We scan the whole board to find:

- Revealed clue cells with `adj[r][c] > 0`
- Their unknown and flagged neighbors

For each of `N` cells:

- Constant-time checks: revealed? adj > 0?
- Scan neighbors: `O(d)` (bounded by 8)

**Time**:  
`O(N * d) = O(N)`

We then:

- Allocate constraints: each constraint references some subset of neighbors.
- Insert unknowns into DSU:
  - Find/union operations: `O(α(F))` per operation, where `F` is number of frontier cells (α is inverse Ackermann, ~constant).

**Overall time**:  
Frontier build ≈ `O(N + F * α(F)) ≈ O(N)`.

**Space**:

- Store frontier set: `O(F)`
- DSU parents/ranks: `O(F)`
- Constraints: `O(M)` where `M` is total constraints.

---

## 3. Rule Pass (Deterministic Logic)

Given a component with:

- `k` unknown cells
- `m` constraints

The rule engine may do:

- Simple single-constraint rules:
  - e.g., if `remaining == 0` → all cells safe; if `remaining == #unknown` → all mines.
  - These are `O(m * k)` in the worst case (scanning bits).

- Subset-based rules:
  - e.g., if constraint A’s scope ⊆ constraint B’s scope, derive new constraint.
  - Naïvely `O(m^2 * k)` using bitset operations.

In practice, `m` and `k` are relatively small per component (local frontiers), and bitsets compress the constants.

Across all components, the total cost per rule pass is roughly:

**Time**:
- `Σ over components (m_i^2 * k_i)`  
- With typical Minesweeper frontiers (small connected pockets), this is manageable.

**Space**:
- Constraints and temporary masks: `O(m * k)` per component.

---

## 4. Enumeration Complexity

For each component with `k` unknowns, enumeration worst-case is:

- Try every assignment: `2^k` patterns.
- For each pattern:
  - Check all `m` constraints:
    - Bitcount on `mask & constraint.mask_local` — `O(1)` with precomputed popcount.
    - So `O(m)` per pattern.

Thus worst-case:

```text
Time per component: O(m * 2^k)
```
This is only viable if k is small. Hence we enforce `k_max`.

### `k_max` choice (e.g., 20)

- `k_max` was chosen by the professor probably because:
    - `2^k_max` is big but still feasible with pruning and typical constraint structure.
    - `2^20 = 1,048,576` patterns:
        - In practice, most are pruned early by constraint violations.
        - Components often have tight constraints reducing actual work.

- Given that:
    - Real Minesweeper frontiers rarely form a single large 20-cell “free” component.  
    - Many assignments fail early in constraint checking.
    
- `k_max ≈ 15–20` is a reasonable trade-off:
    - Below 15: might miss exact probabilities in interesting mid-game positions.
    - Above 20–22: exponential blow-up becomes too painful for a casual solver.

### Implementation detail:

- If `k > k_max`:
    - We can skip exact enumeration for that component.
    - Either leave probabilities undefined or use approximations (e.g., uniform, Monte Carlo, or break into overlapping subcomponents).

## 5. Probability Computation

- For each component where k ≤ k_max:
    - Enumeration: `O(m * 2^k)` as above.
    - Probability assignment:
        - For each local index i:
            - `p[i] = mine_counts[i] / solutions` turns into `O(k)` total.

- Combined:
    - Time: dominated by enumeration `O(m * 2^k)`
    - Space:
        - mine_counts: `O(k)`
        - Storing solutions: `O(1)`
        - Across all components, worst-case total is:
            - `Σ over components with k_i ≤ k_max of O(m_i * 2^{k_i})` 

## 6. hint, step, auto

- All three use the underlying primitives:
    - refresh_frontier() – `O(N)`
    - rule pass – dominated by `Σ(m_i^2 * k_i)` for each pass
    - Optional enumeration – `Σ(m_i * 2^{k_i})` for probabilistic steps or hints

- `hint`
    - Builds frontier, runs deterministic rules once.
    - Complexity: roughly one pass over all components, no enumeration unless you choose to.

- `step(guess=False)`
    - Single deterministic move:
        - Build frontier: `O(N)`
        - Run rules, stop after the first non-empty result.
    - Complexity: `O(N + cost_of_first_rule_match).`

- `step(guess=True)`
    - Same as above, but if no deterministic move:
        - `prob()` is called:
                - `O(N)` to ensure frontier is up to date
                - `O(m * 2^k)` for enumerated components (bounded by `k_max`).

- `auto(guess=False, limit=L)`
    - Up to L moves (or fewer if stuck or game over).
    - Each loop:
        - Frontier build: `O(N)`
        - Rule pass: as above

- `auto(guess=True, limit=L)`
    - Same as auto without guessing, plus:
        - Occasional calls to `prob()` if stuck.
        - Enumeration cost amortized over relatively few guess events.

## 7. Space Complexity Summary

- Board:
    - `is_mine`, `adj`, `revealed`, `flagged` is `O(N)` each.

- Frontier / DSU:
    - Frontier list + DSU arrays: O(F), F ≤ N.

- Constraints per frontier build:
    - `O(M)` total across components.

- Enumeration:
    - `O(k)` per component for `mine_counts`.
    - Stack/recursion if using recursive enumeration.

- Total space is dominated by `O(N)` board storage plus modest overhead for frontier/solver state.