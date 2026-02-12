import sqlite3
from pathlib import Path
from typing import Any


class GameStatsStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    played_at TEXT NOT NULL DEFAULT (datetime('now')),
                    player_name TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    level_reached INTEGER NOT NULL,
                    victory INTEGER NOT NULL,
                    play_time_sec REAL NOT NULL,
                    kills INTEGER NOT NULL,
                    deaths INTEGER NOT NULL,
                    bullets_used INTEGER NOT NULL,
                    rating REAL NOT NULL
                )
                """
            )

    def add_result(
        self,
        player_name: str,
        difficulty: str,
        level_reached: int,
        victory: bool,
        play_time_sec: float,
        kills: int,
        deaths: int,
        bullets_used: int,
        rating: float,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO game_results (
                    player_name,
                    difficulty,
                    level_reached,
                    victory,
                    play_time_sec,
                    kills,
                    deaths,
                    bullets_used,
                    rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player_name,
                    difficulty,
                    int(level_reached),
                    1 if victory else 0,
                    float(play_time_sec),
                    int(kills),
                    int(deaths),
                    int(bullets_used),
                    float(rating),
                ),
            )

    def top_results(self, limit: int, difficulty: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if difficulty:
                rows = conn.execute(
                    """
                    SELECT played_at, player_name, difficulty, level_reached, victory,
                           play_time_sec, kills, deaths, bullets_used, rating
                    FROM game_results
                    WHERE difficulty = ?
                    ORDER BY rating DESC, kills DESC, play_time_sec ASC
                    LIMIT ?
                    """,
                    (difficulty, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT played_at, player_name, difficulty, level_reached, victory,
                           play_time_sec, kills, deaths, bullets_used, rating
                    FROM game_results
                    ORDER BY rating DESC, kills DESC, play_time_sec ASC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def best_rating(self, difficulty: str | None = None) -> float:
        with self._connect() as conn:
            if difficulty:
                row = conn.execute(
                    "SELECT MAX(rating) AS best FROM game_results WHERE difficulty = ?",
                    (difficulty,),
                ).fetchone()
            else:
                row = conn.execute("SELECT MAX(rating) AS best FROM game_results").fetchone()
        return float(row["best"] or 0.0)
