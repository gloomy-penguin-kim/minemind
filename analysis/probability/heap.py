


def heap(self, limit=5):
    """
    Build or consume a guess heap.
    If apply=True, apply a single best guess and return [move].
    If apply=False, return a list of guess candidates until the first SAFE.
    """
    _, heap = self.prob()
    if heap is None:
        return []

    safe = False

    all_moves = []
    effected_cells = [] 

    while heap and ((apply and len(all_moves) == 0) or (not apply and not safe)):
        rating, safety, p_mine, centerness, (r, c) = heappop(heap)
        logger.debug(
            "heappop guess candidate: (%d,%d) p=%.3f rating=%s safety=%s centerness=%.2f",
            r, c, p_mine, rating, safety, centerness
        )

        if self.board.revealed[r][c] or self.board.flagged[r][c]:
            continue

        safety_percent = p_mine * 100.0

        if p_mine < 0.5:
            guess = Move(r, c, MoveKind.SAFE, [f"GUESS - mine probability: {safety_percent:6.2f}%"])
        else:
            guess = Move(r, c, MoveKind.MINE, [f"GUESS - mine probability: {safety_percent:6.2f}%"])

        # TODO: move this apply to the other functions and evict this apply "feature"
        if apply:
            ec = self._apply_move(guess)
            if len(ec) > 0:
                effected_cells += ec  
                all_moves.append(guess)
                break
        else:
            all_moves.append(guess)
        
        if self.board.game_over: 
            break 

    return all_moves, effected_cells