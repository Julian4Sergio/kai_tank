from pathlib import Path

from tank_game.storage import GameStatsStore


def test_store_and_query_by_difficulty(tmp_path: Path) -> None:
    db_file = tmp_path / "stats.db"
    store = GameStatsStore(db_file)

    store.add_result(
        player_name="sergiokai",
        difficulty="easy",
        level_reached=2,
        victory=False,
        play_time_sec=44.5,
        kills=7,
        deaths=3,
        bullets_used=20,
        rating=5.5,
    )
    store.add_result(
        player_name="sergiokai",
        difficulty="hard",
        level_reached=5,
        victory=True,
        play_time_sec=110.2,
        kills=30,
        deaths=1,
        bullets_used=45,
        rating=9.8,
    )

    easy = store.top_results(limit=10, difficulty="easy")
    hard = store.top_results(limit=10, difficulty="hard")

    assert len(easy) == 1
    assert len(hard) == 1
    assert easy[0]["difficulty"] == "easy"
    assert hard[0]["difficulty"] == "hard"
    assert store.best_rating(difficulty="hard") == 9.8
