from analysis.rules.move import MoveList
from analysis.rules.subsets import _process_moves_for_this_mask
from core.constants import Action 
from analysis.frontier.component import Component


def _apply_equivalence(
        comp: Component,
        board,
        moves: MoveList,
        stop_after_one: bool
    ):
    """
    Equivalence / Scope-equality rule:

    1) If A == B but rem differs -> contradiction (conflict)
    2) If A ⊂ B and rem(A) == rem(B) -> (B \\ A) SAFE
       (same as subset "equality" case, but grouped here explicitly)

    Note: your _apply_subset already does case (2). This function is mainly:
      - explicit conflict detection for equal scopes
      - optional separation for debugging/clarity
    """ 

    constraints = comp.constraints
    n = len(constraints)

    for i in range(n):
        mask_a = constraints[i].mask_local
        rem_a = constraints[i].remaining
        if mask_a == 0:
            continue

        for j in range(i + 1, n):
            mask_b = constraints[j].mask_local
            rem_b = constraints[j].remaining
            if mask_b == 0:
                continue

            # # --- (1) Exact scope equality contradiction check ---
            # if mask_a == mask_b and rem_a != rem_b:
            #     conflicts.append((
            #         "SCOPE_EQUALITY_CONTRADICTION",
            #         i, j,
            #         mask_a, rem_a,
            #         mask_b, rem_b,
            #     ))
            #     # if you prefer: early stop on first contradiction
            #     continue

            # --- (2) Proper subset + equal remaining => diff SAFE ---
            # A ⊂ B
            if (mask_a & mask_b) == mask_a and mask_a != mask_b and rem_a == rem_b:
                diff = mask_b & ~mask_a
                if diff:
                    reasons = (
                        "Equivalence: A⊂B and rem(A)==rem(B) -> B\\A SAFE",
                        f"{bin(mask_a)} rem={rem_a} is subset of {bin(mask_b)} rem={rem_b}",
                    )
                    _process_moves_for_this_mask(
                        board=board,
                        moves=moves,
                        local_to_global=comp.local_to_global,
                        mask=diff,
                        action=Action.OPEN,
                        reasons=reasons,
                    )
                    if stop_after_one and len(moves) > 0:
                        return moves

            # B ⊂ A
            if (mask_a & mask_b) == mask_b and mask_a != mask_b and rem_a == rem_b:
                diff = mask_a & ~mask_b
                if diff:
                    reasons = (
                        "Equivalence: B⊂A and rem(A)==rem(B) -> A\\B SAFE",
                        f"{bin(mask_b)} rem={rem_b} is subset of {bin(mask_a)} rem={rem_a}",
                    )
                    _process_moves_for_this_mask(
                        board=board,
                        moves=moves,
                        local_to_global=comp.local_to_global,
                        mask=diff,
                        action=Action.OPEN,
                        reasons=reasons,
                    )
                    if stop_after_one and len(moves) > 0:
                        return moves

    return moves
