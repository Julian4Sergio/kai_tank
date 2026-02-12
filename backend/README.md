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

Sample `POST /api/scores` body:
```json
{
  "playerName": "Kai",
  "difficulty": "medium",
  "rating": 8.32,
  "kills": 24,
  "deaths": 1,
  "bulletsUsed": 53,
  "levelReached": 5,
  "victory": 1,
  "playTimeSec": 181.7,
  "timeMs": 181700,
  "playedAt": "2026-02-12T12:34:56.000Z"
}
```
