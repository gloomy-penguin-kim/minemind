# minemind/cli.py

import shlex
import argparse
from typing import List
 
from core.snapshot import save_snapshot, load_snapshot
from core.config import config
from analysis.rules.move import Move
from minemind.game import Game


PROMPT = "minemind> "

def main():
    g = Game()
    run_preloaded_repl(g)

def run_preloaded_repl(g):
    """
    Start the interactive shell using an existing Game() instance.
    """
    while True:
        try:
            line = input(PROMPT).strip()
        except EOFError:
            print()
            break

        if not line:
            continue

        print()

        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"Parse error: {e}\n")
            continue

        cmd, *args = parts
        cmd = cmd.lower()

        if cmd in ("quit", "exit", "q"):
            break

        handler = COMMANDS.get(cmd)
        if handler is None:
            print(f"Unknown command: {cmd}. Type 'help' for a list of commands.\n")
            continue

        handler(g, args)


def cmd_help(g: Game, args=None):
    print(
        "- First, start the game with the `new` command\n"
        "- Next, determine the board by making your first reveal\n"
        "      using the `open` command\n"
        "- Then use additional commands to play the game.\n"
        "\n"
        "- OR, load a game from a file using the `load` command\n"
        "\n"
        "Commands:\n"
        "  help\n"
        "  new [--w W] [--h H] [--mines M] [--seed S] [--beginner] [--intermeidate] [--expert]\n"
        "  show [--reveal]\n"
        "  open X Y                                 # reveal a cell\n"
        "  flag X Y                                 # toggle a flag\n"
        "  chord X Y                                # chord around a revealed cell\n"
        "  chords                                   # find and list all chord-able cells\n"
        "  undo                                     # undo the last move (even if losing)\n"
        "  verify                                   # check placement of existing flags\n"
        "  hint [--guess] [--verbose]               # hints and reasons\n" 
        "  step [--guess] [--verbose]               # make one automatic move\n"
        "  auto [--guess] [--limit N] [--force] [--verbose]   # multiple automatic moves\n"
        "  prob [--verbose]                         # probability heatmap / listing\n"
        "  count                                    # count number of flags vs mines vs unknowns\n"
        "  frontier [--global] [--local]            # show frontier components\n"
        "  conflicts                                # show conflicts against rules in the board\n"
        "  invariants [--on] [--off]                # toggle invariants mode or show state (also makes things verbose)\n"
        "  max_k K                                  # sets the maximum k for uknown cells in a component\n" 
        "  save path.json                           # save a game\n"
        "  load path.json                           # load a game\n"
        "  quit | exit\n"
    )


def cmd_new(g: Game, args):
    """
    new --w W --h H --mines M [--seed S]
    """
    parser = argparse.ArgumentParser(prog="new", add_help=False)
    parser.add_argument("--w", "--width", dest="width", type=int)
    parser.add_argument("--h", "--height", dest="height", type=int)
    parser.add_argument("--mines", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--beginner", action="store_true") 
    parser.add_argument("--intermediate", action="store_true") 
    parser.add_argument("--expert", action="store_true") 

    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return
    
    if not(ns.width and ns.height and ns.mines): 
        if ns.width and ns.height and not ns.mines: 
            print("Number of mines not provided\n")
            return 
        if ns.width and not ns.height and ns.mines: 
            print("Height not provided\n")
            return 
        if not ns.width and ns.height and ns.mines: 
            print("Width not provided\n")
            return 
        if ns.intermediate: 
            print("Intermediate Board")
            ns.width = 16 
            ns.height = 16 
            ns.mines = 40 
        elif ns.expert: 
            print("Expert Board")
            ns.width = 30 
            ns.height = 16 
            ns.mines = 99 
        elif ns.beginner: 
            print("Beginner Board")
            ns.width = 9 
            ns.height = 9 
            ns.mines = 10 
        else: 
            print("Expert Board")
            ns.width = 30 
            ns.height = 16 
            ns.mines = 140 

    else: 
        if ns.height < 1: 
            print("height must be >= 1")
        if ns.width < 1: 
            print("width must be >= 1")
             
    g.new(rows=ns.height, cols=ns.width, mines=ns.mines, seed=ns.seed)

    print(f"New game: {ns.width}x{ns.height}, mines={ns.mines}, seed={ns.seed}")
    g.render_board()


def cmd_show(g: Game, args):
    if not g.validate_board():
        return

    parser = argparse.ArgumentParser(prog="show", add_help=False)
    parser.add_argument("--reveal", action="store_true")
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return

    g.render_board(ns.reveal)


def _parse_rc(args, usage: str):
    if len(args) != 2:
        print(f"usage: {usage}\n")
        return None
    try:
        r, c = map(int, args)
    except ValueError:
        print(f"usage: {usage}  (R and C must be integers)\n")
        return None
    return r, c


def _print_conflicts(conflicts): 
    if len(conflicts) > 0: 
        print("please check conflicts\n")
        # print("conflicts found, cannot continue")
        # for (r,c) in conflicts: 
        #     print(f"conflicts: r={r},c={c}") 
        # print()     


def _print_moves(moves, verbose=False):
    if not moves:
        return

    def first_reason(m):
        return m.reasons[0] if getattr(m, "reasons", None) else ""
 
    if isinstance(moves, list) and len(moves) == 1: 
        moves = moves[0] 
    
    if isinstance(moves, Move):
        m = moves
        if verbose:
            print(m)
            for line in (m.reasons or ()):
                print(f"   {line}")
            print()
        else:
            r = first_reason(m)
            print(m, r)
            print()
        return
    if isinstance(moves, List):
        for i, m in enumerate(moves, start=1):
            if verbose:
                print(f"{i:2} -", m)
                for line in (m.reasons or ()):
                    print(f"       {line}")
            else:
                r = first_reason(m)
                print(f"{i:2} -", m, r)
        print()


def cmd_open(g: Game, args):
    if not g.has_curr_game():
        return

    coords = _parse_rc(args, "open X Y")
    if coords is None:
        return
    r, c = coords
    if not g.verify_coords(r, c):
        return

    if not g.board.mines_placed:
        g.start_timer()
    
    try:
        opened = g.open(r,c)

        if not opened: 
            print("open did not succeed... please restart program\n")
            return
         
        if opened.empty: 
            print("nothing changed (already revealed/flagged or game over)\n")
            return 

        r = len(opened.revealed)

        if r == 1: 
            print(f"revealed: {r} cell") 
        else:
            print(f"revealed: {r} cells") 
        print()
        g.render_board()
        g.is_winner(opened.game_over, opened.win)
    except AssertionError as e:
        g.render_board() 
        print(e)  

    # revealed: Set[Coord] = field(default_factory=set)
    # flagged: Set[Coord] = field(default_factory=set)
    # game_over: bool = False
    # win: bool = False
    # note: str = ""


def cmd_flag(g: Game, args):
    if not g.validate_board():
        return

    coords = _parse_rc(args, "flag X Y")
    if coords is None:
        return
    r, c = coords
    if not g.verify_coords(r, c):
        return

    try: 
        flagged = g.flag(r, c)
        
        if not flagged:
            print("flag has failed you... try again\n")
            return
        
        _print_moves(flagged)
        print()
        g.render_board()
        g.is_winner(flagged.game_over, flagged.win)
    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_chord(g: Game, args):
    if not g.validate_board():
        return

    r,c = _parse_rc(args, "chord X Y")  
    if not g.verify_coords(r, c):
        return

    try:
        chord = g.solver.chord(r, c)  
        
        if len(chord.revealed) == 0:
            print("chord found no cells to reveal for you\n")
            return

        for r, c in chord.revealed:
            print(f"chord: r={r},c={c}")

        print()
        g.render_board()
        g.is_winner(chord.game_over, chord.win)
    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_chords(g: Game, args=None):  
    try: 
        chords = g.chords() 
        if not chords:
            print("no chords were found\n")
            return

        for r, c in chords:
            print(f"chords: r={r},c={c}")

        print() 
    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_undo(g: Game, args=None):  
    if args:
        print("usage: undo\n")
        return

    result = g.undo()
    if result is not True:
        print(result)
        return 
        
    g.render_board()

    # if g.board and g.solver: 
    #     game_over = g.board.game_over
    #     try:
    #         undone = g.solver.undo() 
    #         if not undone: 
    #             print("undo had some issues...\n")
    #             return
    #         if game_over: 
    #             g.resume_timer()  
    #         g.render_board()
    #     except AssertionError as e:
    #         g.render_board() 
    #         print(e)   
    # else:
    #     print("use 'new ...' or 'load ...' to start a new game.\n")


def cmd_verify(g: Game, args=None): 
    try:
        messages = g.solver.verify()
        if not messages:
            print("all flags found are correct\n")
            return

        for r, c, correct in messages:
            status = "correct" if correct else "incorrect"
            print(f"verify: r={r},c={c} is {status}")
        print()
    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_hint(g: Game, args=None):
    parser = argparse.ArgumentParser(prog="hint", add_help=False)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--guess", action="store_true")
    try:
        ns = parser.parse_args(args or [])
    except SystemExit:
        return

    try:
        moves,conflicts = g.hint(guess=ns.guess)   # <- make hint return list[Move]
        
        if not moves:
            msg = "no move found"
            if not ns.guess:
                msg += ". try `hint --guess` (or `prob --verbose`)"
            print(msg + "\n")
            return
        
        _print_conflicts(conflicts) 

        _print_moves(moves, ns.verbose)

    except AssertionError as e:
        g.render_board()
        print(e)



def cmd_step(g: Game, args):
    """
    step [--guess]
    """  
    parser = argparse.ArgumentParser(prog="step", add_help=False)
    parser.add_argument("--guess", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return

    try: 
        move, cs, conflicts = g.step(ns.guess)
        print(move) 
        if move: 
            _print_moves(move, ns.verbose)
            _print_conflicts(conflicts)
            g.render_board()
            g.is_winner(cs.game_over, cs.win)
            
        else: 
            msg = "no move found"
            if not ns.guess:
                msg += ". try using `step --guess`"
            print(msg + "\n")
            _print_conflicts(conflicts)
            return 

    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_auto(g: Game, args):
    """
    auto [--guess] [--limit N]
    """
    parser = argparse.ArgumentParser(prog="auto", add_help=False)
    parser.add_argument("--guess", action="store_true") 
    parser.add_argument("--limit", type=int)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--force", action="store_true")
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return

    if ns.limit is not None and ns.limit <= 0:
        print("limit must be a positive number\n")
        return
    
    if ns.force and not ns.guess: 
        print("forcing is not used without guessing\n")

    try:
        moves, cs, conflicts = g.auto(ns.guess, ns.limit, ns.force)
        
        if len(moves) > 0: 
            _print_moves(moves, ns.verbose)
            _print_conflicts(conflicts) 
            g.render_board()
            g.is_winner(cs.game_over, cs.win)

        else:
            msg = "no moves found"
            if not ns.guess:
                msg += ". try `auto --guess`"
            elif not ns.force: 
                msg += ". try `auto --guess --force`"
            print(msg + "\n") 
            _print_conflicts(conflicts) 
            
 
    except AssertionError as e:
        g.render_board() 
        print(e)  



def cmd_prob(g: Game, args):
    if not g.validate_board():
        return

    parser = argparse.ArgumentParser(prog="prob", add_help=False)
    parser.add_argument("--verbose", action="store_true")
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return
    
    try: 
        probs, _ = g.solver.prob()

        if not probs:
            print("no probability data\n")
            return

        g.render_prob_heatmap(probs)

        if ns.verbose:
            print("a number close to 0 is safe; close to 1 is a mine")
            pitems = sorted(probs.items(), key=lambda x: x[1]) 
            for (r, c), p in pitems:
                perc = p * 100
                print(f"prob: r={r},c={c} mine probability: {perc:.2f}%")
            print()

    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_count(g: Game, args=None):
    if not g.validate_board():
        return
    try: 
        flags, unknown, revealed = g.solver.count()

        print(f"count:")
        print(f"   {flags} flags / {g.board.num_mines} mines")
        print(f"   {unknown} unknown cells")
        print(f"   {revealed} revealed cells w/o flags\n")
    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_frontier(g: Game, args):
    if not g.validate_board():
        return

    parser = argparse.ArgumentParser(prog="frontier", add_help=False)
    parser.add_argument("--local", action="store_true", default=False) 
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return
    try:
        g.solver.refresh_frontier()

        # Default to global view if neither is set
        display = "local" if ns.local else "global"
        g.render_frontier(display)

    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_conflcits(g: Game, args=None):
    if not g.validate_board():
        return
    try:
        conflicts = g.solver.conflicts()
        for rc,reasons in conflicts: 
            print(f"conflicts: r={rc[0]},c={rc[1]}")
            for reason in reasons: 
                print(f"   {reason}") 
        if len(conflicts) == 0: 
            print("no conflicts found")
        print("")

    except AssertionError as e:
        g.render_board() 
        print(e)  


def cmd_invariants(g: Game, args=None):
    parser = argparse.ArgumentParser(prog="invariants", add_help=False)
    parser.add_argument("--on", action="store_true", default=False) 
    parser.add_argument("--off", action="store_true", default=False) 
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return
    if not ns.on and not ns.off: 
        if config.invariants: 
            print("invariants mode is on\n")
        else: 
            print("invariants mode is off\n")
    if ns.on: 
        config.invariants = True 
    else:  
        config.invariants = False 


def cmd_max_k(g: Game, args=None):
    parser = argparse.ArgumentParser(prog="k_max", add_help=False)
    parser.add_argument("k", type=str, default=20)
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return
    try:
        k = int(ns.k) 
    except ValueError:
        print(f"k must be an integer.\n")
        return None 
    if k < 1: 
        print("k must be a positive integer.\n")
    g.set_k_max(k) 
     

def cmd_save(g: Game, args):
    if not g.validate_board():
        return

    parser = argparse.ArgumentParser(prog="save", add_help=False)
    parser.add_argument("filename", type=str)
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return

    if not save_snapshot(g, ns.filename):
        print("save: file could not be saved.\n")


def cmd_load(g: Game, args):
    parser = argparse.ArgumentParser(prog="load", add_help=False)
    parser.add_argument("filename", type=str)
    try:
        ns = parser.parse_args(args)
    except SystemExit:
        return

    load_snapshot(g, ns.filename)


COMMANDS = {
    "help": cmd_help,
    "new": cmd_new,
    "show": cmd_show,
    "open": cmd_open,
    "flag": cmd_flag,
    "chord": cmd_chord,
    "chords": cmd_chords,
    "undo": cmd_undo,
    "verify": cmd_verify,
    "hint": cmd_hint,
    "step": cmd_step,
    "auto": cmd_auto,
    "prob": cmd_prob,
    "count": cmd_count,
    "frontier": cmd_frontier,
    "invariants": cmd_invariants,
    "conflicts": cmd_conflcits,
    "max_k": cmd_max_k,
    "save": cmd_save,
    "load": cmd_load,
} 