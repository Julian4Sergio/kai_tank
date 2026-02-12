# Backend (Go)

Minimal Go backend for health check and score leaderboard APIs.

## Requirements
- Go 1.22+

## Run
```powershell
cd backend
go run ./cmd/server
```

Server defaults:
- `PORT=8081`
- `FRONTEND_ORIGIN=*`

## Endpoints
- `GET /health`
- `POST /api/scores`
- `GET /api/scores/leaderboard?difficulty=easy&limit=20`
