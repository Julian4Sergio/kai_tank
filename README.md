# Tank Battle (Python + pygame)

A local single-player tank battle game with 5 progressive levels, difficulty-based scoring, and SQLite leaderboard.

## Standard Project Layout (src)
```text
tank_game/
|- src/
|  |- tank_game/
|     |- __init__.py
|     |- __main__.py
|     |- game.py
|     |- entities.py
|     |- input_state.py
|     |- scoring.py
|     |- storage.py
|     |- namegen.py
|     |- config.py
|- tests/
|- pyproject.toml
|- tank_battle.py
```

## Quick Start
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Run game (recommended):
```powershell
tank-battle
```

Alternative runs:
```powershell
python -m tank_game
python tank_battle.py
```

Run tests:
```powershell
pytest -q
```

## Controls
- Move: `WASD` or arrow keys
- Fire: `Space`
- Return to menu: `R`

## Notes
- Local data is stored in `game_stats.db`.
- Core tuning constants are in `src/tank_game/config.py`.
- Rating caps: Easy 7.5, Medium 9.0, Hard 10.0.
