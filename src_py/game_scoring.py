HINT_PENALTY = 2


def get_raw_guess_count(game: dict) -> int:
    guesses = game.get("guesses", [])
    if isinstance(guesses, list):
        return len(guesses)
    return int(guesses or 0)


def get_hint_penalty_count(game: dict) -> int:
    if not game:
        return 0
    penalty = game.get("hintPenalty", 0)
    if isinstance(penalty, (int, float)) and penalty > 0:
        return int(penalty)
    return HINT_PENALTY if game.get("hintUsed") else 0


def get_effective_guess_count(game: dict, max_guesses: int = 999999) -> int:
    return min(max_guesses, get_raw_guess_count(game) + get_hint_penalty_count(game))
