from core.utility import get_indicies_from_bitmask


def render_board(board, timer, reveal_all, moves=1):
    """
    Print a simple text representation of the board.
    reveal_all=True shows the whole board (for debugging / after game).
    """
    def cell_char(r, c):
        if reveal_all:
            if board.is_mine[r][c]:
                return '*'
            if board.adj[r][c] == 0:
                return ' '
            return str(board.adj[r][c])

        # normal play view
        if board.revealed[r][c]:
            if board.is_mine[r][c]:
                return '*'
            if board.adj[r][c] == 0:
                return ' '
            return str(board.adj[r][c])
        else:
            if board.flagged[r][c]:
                return 'F'
            return '.'
    
    if timer: 
        print(f"Start Date: {timer.get_created_dt()}")
        print(f"Last Resume Date: {timer.get_resumed_dt()}")
        print(f"Elapsed Time: {timer.get_elapsed_seconds_hms()}")
        print(f"Moves: {moves}\n")

    print("   " + " ".join(f"{c:2}" for c in range(board.cols)))
    for r in range(board.rows):
        row_str = " ".join(f"{cell_char(r, c):2}" for c in range(board.cols))
        print(f"{r:2}  {row_str}")
    print()
     

def render_prob_heatmap(board, probs) -> None:
    """
    render an ASCII probability heatmap.
    """

    def cell_char(r: int, c: int) -> str:
        # revealed cells
        if board.revealed[r][c]:
            if board.is_mine[r][c]:
                return '*'  # after loss / reveal-all
            val = board.adj[r][c]
            if val <= 0:
                return ' '  # empty zero
            return str(val)

        # flagged cells
        if board.flagged[r][c]:
            return 'F'

        # unknown cell: see if we have a probability
        p = probs.get((r, c))
        if p is None:
            return '.'   

        # bucket into ASCII symbols
        if p == 0.0:
            return '0'
        if p == 1.0:
            return 'X'
        if p < 0.15:
            return '.'
        if p < 0.35:
            return ':'
        if p < 0.55:
            return '-'
        if p < 0.75:
            return '+'
        if p < 0.9:
            return '*'
        return '#'  
  
    print("Probability heatmap:\n")
 
    print("   " + " ".join(f"{c:2}" for c in range(board.cols)))
    for r in range(board.rows):
        row_str = " ".join(f"{cell_char(r, c):2}" for c in range(board.cols))
        print(f"{r:2}  {row_str}")
    print()  


def render_frontier(components, board, global_or_local="global"):
    print(f"Frontier has {len(components)} components:")
    for i, comp in enumerate(components):
        print(f"\nComponent {i}: unknown={comp.k}")

        # print mapping
        print("  local_to_global:")
        for local, glbl in enumerate(comp.local_to_global):
            r, c = divmod(glbl, board.cols)
            print(f"      {local}: (r={r}, c={c}) gid={glbl}")

        # print constraints
        print("  constraints:")
        for i,cons in enumerate(comp.constraints): 
            m = cons.mask_global if global_or_local == "global" else cons.mask_local  
            arr = get_indicies_from_bitmask(m)            
            print(f"      {i}: arr={arr}, remaining={cons.remaining}")
            
        print("  local bitmasks:")
        for i,cons in enumerate(comp.constraints):              
            print(f"      {i}: mask={bin(cons.mask_local)}")
    print() 
