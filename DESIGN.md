# Primary Functions adn Invariants

#### 1. `hint()` 
- Verify the board to make sure there is a valid game in play to analuze 
- Loop through each of the frontier components
    - Run `apply_rules()` with the parameter `stop_after_one=True` set and recieve back a list of `Moves` and any conflicts 
    - The first rule available will be selected and returned to `cli.py`
- There is a very easy option here that if no deterministic moves are found by using the rules, `_heap()` is called and the probabilities are calculated and a list of `Moves` are returned with probability percentages.  This list would continues until the first `SAFE` move is listed because these moves are prioritized by specification. Although implemented, it is commented out for now as per specification.  

##### 2. `auto(guess=False, limit=None)`
- Verify the board to make sure there is a valid game in play to analyze 
- While the board stays valid and in play and the limit has not been met:
    - Refresh the frontier components 
    - For each frontier component: 
        - verify the limit has not been met 
        - run `apply_rules()` and recieve a list of `Moves` back 
        - combine these moves with the accuring list for all components so it is within the limit length 
        - if there are moves to apply, run them now
            - invariants are checked to make sure only relevant cells are modified 
        - verify the cam is not over
        - if a any move was applied, continue to the next component because the limit has either been reached or all moves applied for this component or a refresh of the frontier is needed before it will have more moves to apply
        - if no moves were applied:
            - if `guessing=false` continue to the next component 
            - if `guessing=True`: 
                -   use the probabilities `_heap()` function to get the first/lowest probability off of the heap 
                    - the heap will apply the move itself and return the effected cells and list of moves which are added to arrays accumulating for all the components 
- If the length of effected cells is above zero, a modification has been made to the board `verify_and_history()` with the effected cells, a count of applied moves (one move may effect many cells) and a note.  These things create a snapshot for the `undo()` function and for invariants to test against 

##### 3. `step(guess=False)`
- Verify the board to make sure there is a valid game in play to analyze 
- For each frontier component: 
    - Tun `apply_rules()` and recieve a list of `Moves` back 
    - If there is a rule/`Move` returned: 
        - Take the first and apply it to the board
        - Call `verify_history()` with list of effected cells, a note and the count of moves is defaulted to 1 
        - Returl to `cli.py`
- If `guess=True` and no data was returned from the rules, 
    - Consult `_heap()` for 1 step
        - this will apply the move and return a list of effected cells 
    - Return the `Move` to `cli.py` 

##### 4. `prob()` 
- This function creates the `_heap()` used by `hint()`, `auto()`, and `step()` 
- Verify the board to make sure there is a valid game in play to analyze 
- Refresh the frontier components 
- For each frontier component: 
    - Run `_get_probabilites(component)` where a result is returend that holds an associative array of solutions and mine counts 
        - The components here are cached, enumerated or skipped for size lmitiations 
    -  An invarinats test is started here, gathering the total number of mines in component.  This is the real number based on the board and is only used in invariants mode and not for any calculation the user will see. 
    - For each index of the unknown cells in the component:
        - find the global ID number to dertermin the row and column of the cell 
        - if the cell is flagged or revealed, skip and continue 
        - The mine probability is calcualated by taking the mine count per all solutions for this index divied by total solution count.  This is then added to a `all_probs[(row,col)] = mine_probability` 
        - if the invariants mode is turned on, the tests are completed which check the probability sums with the known mine counts. These verify: 
            - The location already being revealed or flagged
            - The mine probability being 0.0 (a safe spot) but a mine in the location (conflicting with the user's flag location possibly but this is for invariants mode only)
            - a mine probablity of 1.0 on a safe spot
            - zero remaning mines with a positive probability value
            - all locations in the component being mines, and that the mine probability is within range
        - Tiebreakers are determined: 
            - the centrality of the location by using the Euclidean distance to the center
            - the rating: how close the probability is to 0 or 1 
            - the safety: promote safe cells instead of mines so that those are listed or guessed first 
        - Thse values are added to the heap with the `(row,col)` coordinates 
- Return all probabilities for unknown cells in every component along with the created heap 

##### 5. `_get_probabilities(component)` 
- This function is ran per component and returns either a cached set of probabilities or runs the enumeration function to return and cache 
- If the this component is cached in the signature cashe, return the probabilites for this component
- If the number of unknown cells in this component is greater than `max_K`, do nothing and return 
- Else, run `_run_probabilities(component)`and put the results in the signature cache 

##### 6. `_run_probabilties(component)`
- Gather all variables 
    - the number of unknown cells in this component
    - an array of the remaining count of mines per unknwon cell, aligning with the indices of unknown cell  
    - An empty array for assigned mine values that will accumulate for all solutions 
    - An empty array for unknown values, corresponding to the bitcount of the local mask 
    - total solutions count
    - an empty array to hold the mine counts perrecursive solution
    - a list of all the constraints for the component 
- The recursive function by dfs:  
    - Parmmeters: `position index`, `reamining` array, `unknown` array, `assignment` array 
    - Nonlocal, global values: `total solutions` count and array for `total mine count`
    - Fhe function body: 
        - Conditional check for recusion closure: 
            - if all positiions have been assigned, and there are no remaning we have a valid solution!  Incrememnt the values in `mine_counts[i]` with the values in the `assignment[i]` array 
        - For each value in `(SAFE, MINE)` to attempt to forward `assignment` with:
            - assign `assignment[position_index]` to either safe or mine 
            - copy the `remaining` array and the `uknown` array because it is recursion 
            - For each enumerated constraint with constraint ID from the enumeration, 
                - Get the local `bitmask`to gather the local `indices`
                - For each position in the `incides` array 
                    - decrememnt the unknown values for this constraint ID index
                    - if we are adding a `MINE` decrement the remaining mine values for this constraint ID index 
                    - Pruning: 
                        - if the `remaining[constraint_id]` is less than 0
                        - if the `remaining[constraint_id]` is greater than the `unknown[constraint_id]`
                        - if the `unknown[constraint_id]` == 0 and `remaining[constraint_id]`!= 0 
                    - If not pruned, call the dfs recursive function again with the updated `pos_inidex`, the updated `remaning` array, the updated `unknown` count array and the `remaining` count array 
    - Return an associative array of the total solution count and the mine count array with corresponding indicies to the unknown value array 

##### 7. `apply_rules()`
- A constraint says (locally or globally) that a certain set of cells ther are a certain amount of mines
- Singles: 
    - if there are no mines, all the cells are considered safe
    - if there are the same number of cells as remanining mines, they are all mines
- Subset rule: 
    - For every A,B combination in this component: 
        - If A inertsects B, A is inside of B and based on the bitmask of the two, the ones overlapp.  Every hiddent cell in A is also in B but B also has some extra cells.  
            - If `A == B` the extra cells are all safe cells. 
            - if `b - a` the extra cells are all mine cells.  
    - The logic is the swapped for B, A 


#### Invariants 

I have a really small `config.py` class that handles the `invariants [--on] [--off]` flag for the program so it can do tests while running in additional to the documents found ing the `./test/` directory

##### 1. DSU Invariants 

This is found in `frontier.oy` so that it can be ran while the program is running with the `invariants --on` option.  
    - This checks to make sure that roots are self-parents. 
    - That no parent points outside of the range/scope 
    - Children cannot have a higher rank than their parents.  
    - All values are seen once and oly once 

##### 2. Board Invariants 

Warning: There are several tests that can run during in game play to verify invariants.  Some of these might affect a user's game so the `invariants` mode should only be used if they want a very verfied level of assurance. 
    - total mines <= total unknowns 
    - the adjacent mines numbers must match the number af adjacent mines
    - mines cannot be revelaed ever besides the end (they may be revealed, though)
    - the undo function tests the previous state of the board to the current board in terms of flagas, unknowns, revealed cells, mine cells. it also verifies a list of modified, effected cells which were caused by the move.  Each move can be undone therefore a snapshot is taken and compared for every move besides the very first one.  
    - get the remaning mines per component for probabilities invariants 
    - test that flagged cells cannot be revealed 
 
##### 3. Solve Invariants 

Warning: There are several tests that can run during in game play to verify invariants.  Some of these might affect a user's game so the `invariants` mode should only be used if they want a very verfied level of assurance. 
    - if the invariants mode is turned on, the tests are completed which check the probability sums with the known mine counts. These verify: 
        - The location already being revealed or flagged
        - The mine probability being 0.0 (a safe spot) but a mine in the location (conflicting with the user's flag location possibly but this is for invariants mode only)
        - a mine probablity of 1.0 on a safe spot
        - zero remaning mines with a positive probability value
        - all locations in the component being mines, and that the mine probability is within range
        - Tiebreakers are determined: 
        - the centrality of the location by using the Euclidean distance to the center
        - the rating: how close the probability is to 0 or 1 
        - the safety: promote safe cells instead of mines so that those are listed or guessed first 
    - `_apply_move(move)` houses the main invariant check for the solver where it checks the cell count of unknown celles before and after a move 
    - `verify_and_history(effected_cells, note, count)` runs the board invariant tests before it takes a state snapshot 
        - `test_flagged_mines_and_unknowns()`- this tests the counts of the entire board 
        - `test_adj_numbers()` - the adjacent mines numbers must match the number af adjacent mines
        - `test_mines_not_revealed()` - this tests that mines are not revealed 
        - `test_cells_cannot_be_flagged_and_revealed()`- this tests that cells cannot be flagged and revealed 

#### Max_K Choice 

I understand the complexity associated with a high `max_k` choice, which is the number of unknowns per component, however the program still works even though it is ran at a higher `max_k` value such as 55.  I have decided to make this a option on the command line so the user may allow for a higher amount of computations (probably with `invnariants --off`)