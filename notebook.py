""""
Board
- state
- apply(Action,r,c) -> ChangeSet
- undo stack
- win logic
- invariants (optional but recommended)

Solver
- build_frontier(board) (read-only)
- apply_rules(comp, board) (read-only)
- enumeration/probabilities (read-only)
- chooses an action when asked (step, auto) by calling board.apply

CLI
- parses
- calls solver for actions or queries
- prints results
"""