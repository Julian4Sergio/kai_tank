from tank_game.config import DIFFICULTY_RATING_CAP
from tank_game.config import PLAYER_LIVES
from tank_game.config import SCORING


def calculate_rating(
    difficulty_key: str,
    elapsed_sec: float,
    kills: int,
    shots: int,
    deaths: int,
    victory: bool,
) -> float:
    elapsed = max(1.0, float(elapsed_sec))
    kill_score = min(1.0, kills / SCORING["target_kills"])
    accuracy = min(1.0, kills / max(1, shots))
    # Treat 1 second as the practical lower bound for elapsed time so max score remains reachable.
    time_score = max(0.0, 1.0 - ((elapsed - 1.0) / SCORING["target_time_sec"]))
    survival = max(0.0, 1.0 - deaths / PLAYER_LIVES)
    victory_bonus = 1.0 if victory else 0.0

    weighted = (
        kill_score * SCORING["w_kills"]
        + accuracy * SCORING["w_accuracy"]
        + time_score * SCORING["w_time"]
        + survival * SCORING["w_survival"]
        + victory_bonus * SCORING["w_victory_bonus"]
    )
    difficulty_cap = DIFFICULTY_RATING_CAP.get(difficulty_key, 10.0)
    return round(max(0.0, min(difficulty_cap, weighted * difficulty_cap)), 2)
