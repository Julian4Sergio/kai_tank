from tank_game.scoring import calculate_rating


def test_hard_mode_can_reach_ten() -> None:
    rating = calculate_rating(
        difficulty_key="hard",
        elapsed_sec=1,
        kills=999,
        shots=999,
        deaths=0,
        victory=True,
    )
    assert rating == 10.0


def test_easy_mode_is_capped() -> None:
    rating = calculate_rating(
        difficulty_key="easy",
        elapsed_sec=1,
        kills=999,
        shots=999,
        deaths=0,
        victory=True,
    )
    assert rating <= 7.5
