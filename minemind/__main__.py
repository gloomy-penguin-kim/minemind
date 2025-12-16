import logging 

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')

# minemind/__main__.py
# minemind/__main__.py
import sys
from .cli import main as interactive_main
from .cli import COMMANDS, run_preloaded_repl
from .game import Game


def _entry():

    argv = sys.argv[1:]

    # case 1: just `python -m minemind`
    if not argv:
        return interactive_main()

    # case 2: run a command, THEN open interactive shell
    cmd, *args = argv
    cmd = cmd.lower()

    g = Game()

    handler = COMMANDS.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd}")
        return interactive_main()

    # Execute the one-shot command on the Game()
    handler(g, args)

    # Now drop into the interactive shell with the same game instance
    print()  # spacing
    run_preloaded_repl(g)


if __name__ == "__main__":
    _entry()
