# Kai Tank (Web)

Browser version of the tank battle game.  
Gameplay kept from the original desktop version:
- 2-step menu (name + difficulty)
- 5 progressive levels
- 3 lives + short respawn invincibility
- brick / steel obstacles
- score rating and difficulty leaderboard

## Tech
- Vanilla HTML/CSS/JavaScript
- Canvas 2D rendering
- IndexedDB for browser-side result storage
- GitHub Pages deployment workflow

## Run Locally
Any static server works. Example:

```powershell
py -3 -m http.server 8080
```

Open `http://localhost:8080`.

## Controls
- Move: `WASD` or arrow keys
- Fire: `Space`
- Back to menu: `R`

## Deploy (GitHub Pages)
This repo includes `.github/workflows/pages.yml`.

1. Push to `main`
2. In GitHub repo settings, enable **Pages** with source **GitHub Actions**
3. Workflow publishes the site automatically
