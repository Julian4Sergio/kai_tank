from pathlib import Path


SCREEN_WIDTH = 720
SCREEN_HEIGHT = 520
FPS = 60
DEFAULT_PLAYER_NAME = "sergiokai"

BULLET_SPEED = 7.6
TOTAL_LEVELS = 5
PLAYER_LIVES = 3
RESPAWN_INVINCIBLE_MS = 1300

BG_COLOR = (24, 24, 30)
GRID_COLOR = (38, 38, 48)
PLAYER_COLOR = (72, 190, 108)
ENEMY_COLOR = (207, 87, 75)
BULLET_COLOR = (240, 232, 165)
TEXT_COLOR = (236, 236, 240)
GOOD_COLOR = (120, 230, 140)
WARN_COLOR = (238, 134, 110)
BRICK_COLOR = (183, 104, 63)
STEEL_COLOR = (128, 137, 150)

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "player_speed": 4.8,
        "enemy_speed": 1.1,
        "player_fire_cd": 200,
        "enemy_fire_cd": 1750,
        "enemy_fire_chance": 0.008,
        "max_player_bullets": 6,
        "base_enemy_count": 3,
    },
    "medium": {
        "label": "Medium",
        "player_speed": 4.2,
        "enemy_speed": 1.4,
        "player_fire_cd": 260,
        "enemy_fire_cd": 1400,
        "enemy_fire_chance": 0.012,
        "max_player_bullets": 5,
        "base_enemy_count": 4,
    },
    "hard": {
        "label": "Hard",
        "player_speed": 3.8,
        "enemy_speed": 1.8,
        "player_fire_cd": 300,
        "enemy_fire_cd": 1000,
        "enemy_fire_chance": 0.018,
        "max_player_bullets": 4,
        "base_enemy_count": 5,
    },
}

DIFFICULTY_RATING_CAP = {
    "easy": 7.5,
    "medium": 9.0,
    "hard": 10.0,
}

SCORING = {
    "target_kills": 30,
    "target_time_sec": 220,
    "w_kills": 0.32,
    "w_accuracy": 0.28,
    "w_time": 0.20,
    "w_survival": 0.10,
    "w_victory_bonus": 0.10,
}

LEADERBOARD_LIMIT = 8
DB_PATH = Path("game_stats.db")
