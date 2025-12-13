# MineMind

MineMind is a console-based Minesweeper clone with a **logic-based solver** and a **probability engine**.  
You can play manually, ask for hints, step through solver moves, or let it auto-play (with optional guessing).

It’s part game, part solver sandbox.

---

## Features

- Classic Minesweeper gameplay on arbitrary W×H boards with configurable mine counts.
- Interactive CLI shell:
  - `open`, `flag`, `chord`, `undo`, `save`, `load`, etc.
- Deterministic solver:
  - Frontier decomposition into components
  - Constraint-based reasoning and rule application
  - “Hint” and “Step” to explain *why* a move is safe or a mine.
- Probability engine:
  - Exact enumeration of local components (up to `k_max` unknowns)
  - Per-cell mine probabilities and a heatmap
  - `auto --guess` to play with controlled risk.
- Debug/analysis helpers:
  - `frontier` views
  - `verify` flags against the true layout (when allowed)
  - Probability listings.

---

## Installation

- This should be made with only basic libraries but just in case...
- From the main project directory 
    - python -m venv venv 
    - source venv/bin/activate  # On Linux/macOS
        - venv\Scripts\activate     # On Windows
    - pip install -r requirements.txt 

### Requirements

- Python 3.10+ (3.11+ recommended)
- Linux (recommended)

### Run

- `python3 -m minemind`
- `python3 -m minemind new --h 7 --w 7 --mines 10 `
- `python3 -m minemined --expert` 

## Cheatsheet 

### Game Lifecycle 

- Start a new game
```
minemind> new --w 10 --h 10 --mines 20 --seed 42
minemind> new
minemind> new --beginner
minemind> new --intermediate
minemind> new --expert
```

- Display the board
```
minemind> show          # show current visible board
minemind> show --reveal # show full solution (for analysis)
```

- Save / Load 
```
minemind> save game1.json
minemind> load game1.json
```

### Basic Moves 

- Open a cell 
```
minemind> open 3 4 
```

- Toggle a flag 
```
minemind> flag 3 4 
```

- Chord (mass reveal around a flag)
```
minemind> chord 3 4  
```

- List all cells eligible for chord 
``` 
minemind> chords
```

- Undo last move 
``` 
minemind> undo 
```

### Solver / Analysis  

- Hints
```
minemind> hint 
```

- Single Step
```
minemind> step
minemind> step -- guess  
```

- Autoplay 
```
minemind> auto              # as far as deterministic logic goes
minemind> auto --limit 10   # up to 10 moves
minemind> auto --guess      # allow probabilistic guesses
minemind> auto --guess --limit 5
```

- Probabilites 
```
minemind> prob              # render probability heatmap
minemind> prob --verbose    # also list each cell's probability
```

- Frontier View  
```
minemind> frontier          # global view by default
minemind> frontier --local  # local index view per component
```
 
- Verify flags 
```
minemind> verify
# verify: r=1,c=3 is correct
# verify: r=2,c=7 is incorrec
```

- Count flags, mines and unrevealed cells
```
minemind> count
``` 
 
- Get a list of conflicting cells 
```
minemind> conflicts 
# conflicts: r=7,c=4
```

- Help
```
minemind> help 

- First, start the game with the `new` command
- Next, determine the board by making your first reveal
      using the `open` command
- Then use additional commands to play the game.

- OR, load a game from a file using the `load` command

Commands:
  help
  new [--w W] [--h H] [--mines M] [--seed S] [--beginner] [--intermeidate] [--expert]
  show [--reveal]
  open X Y                                 # reveal a cell
  flag X Y                                 # toggle a flag
  chord X Y                                # chord around a revealed cell
  chords                                   # find and list all chord-able cells
  undo                                     # undo the last move (even if losing)
  verify                                   # check placement of existing flags
  hint [--verbose]                         # deterministic hints + reasons
  step [--guess] [--verbose]               # make one automatic move
  auto [--guess] [--limit N] [--verbose]   # multiple automatic moves
  prob [--verbose]                         # probability heatmap / listing
  count                                    # count number of flags vs mines vs unknowns
  frontier [--global] [--local]            # show frontier components
  conflicts                                # show conflicts against rules in the board
  invariants [--on] [--off]                # toggle invariants mode or show state (also makes things verbose)
  max_k K                                  # sets the maximum k for uknown cells in a component
  save path.json                           # save a game
  load path.json                           # load a game
  quit | exit
```

## Known Limitations 
 

### Guessing is inherently risky
Even with exact local probabilities, some boards require guesses to progress.
step --guess / auto --guess may hit mines; this is expected in genuinely ambiguous positions.

### Enumeration cut-off (k_max)
The probability engine enumerates configurations only for frontier components up to a certain size (k_max).
Larger components fall back to simplified heuristics or are left without probabilities.
 
### Flag correctness is not assumed
Probabilities and frontier building assume the board state is consistent, but not that user flags are logically correct.
Debug invariants that rely on the true solution are kept behind explicit debug commands or test harnesses.


