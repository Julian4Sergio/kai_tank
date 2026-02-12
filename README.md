# Kai Tank (Monorepo)

Repository layout:
- `frontend/`: browser game (static HTML/CSS/JS)
- `backend/`: Go API scaffold (`/health`, score APIs)

Gameplay in frontend keeps the original desktop behavior:
- 2-step menu (name + difficulty)
- 5 progressive levels
- 3 lives + short respawn invincibility
- brick / steel obstacles
- score rating and difficulty leaderboard

## Tech
- Vanilla HTML/CSS/JavaScript
- Go (`net/http`) backend scaffold
- GitHub Pages deployment workflow

## Run Frontend Locally
Serve `frontend/` as static files.

Node.js example:

```powershell
npx.cmd serve frontend -l 8080
```

Python example:

```powershell
py -3 -m http.server 8080 --directory frontend
```

Open `http://localhost:8080`.

### Troubleshooting (PowerShell + Node.js)
If you see:
`npx : ... npx.ps1 cannot be loaded because running scripts is disabled on this system`

Use `npx.cmd` instead of `npx` in PowerShell:

```powershell
npx.cmd serve frontend -l 8080
```

## Run Backend Locally
Backend requires Go 1.22+.

```powershell
cd backend
go run ./cmd/server
```

Default backend URL is `http://localhost:8081`.

## Controls
- Move: `WASD` or arrow keys
- Fire: `Space`
- Back to menu: `R`

## Deploy (GitHub Pages)
This repo includes `.github/workflows/pages.yml`.

1. Push to `main`
2. In GitHub repo settings, enable **Pages** with source **GitHub Actions**
3. Workflow publishes `frontend/` automatically
