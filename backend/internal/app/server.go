package app

import (
    "encoding/json"
    "net/http"
    "strconv"
    "strings"

    "tank-game/backend/internal/model"
    "tank-game/backend/internal/store"
)

type Server struct {
    scores         *store.ScoreStore
    frontendOrigin string
}

func NewServer(frontendOrigin string) *Server {
    return &Server{
        scores:         store.NewScoreStore(),
        frontendOrigin: frontendOrigin,
    }
}

func (s *Server) Routes() http.Handler {
    mux := http.NewServeMux()
    mux.HandleFunc("/health", s.handleHealth)
    mux.HandleFunc("/api/scores", s.handleScores)
    mux.HandleFunc("/api/scores/leaderboard", s.handleLeaderboard)
    return s.withCORS(mux)
}

func (s *Server) withCORS(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", s.frontendOrigin)
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
        if r.Method == http.MethodOptions {
            w.WriteHeader(http.StatusNoContent)
            return
        }
        next.ServeHTTP(w, r)
    })
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    writeJSON(w, http.StatusOK, map[string]any{"ok": true, "service": "tank-game-go-backend"})
}

func (s *Server) handleScores(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    var payload model.Score
    if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
        http.Error(w, "invalid json body", http.StatusBadRequest)
        return
    }

    payload.PlayerName = strings.TrimSpace(payload.PlayerName)
    if payload.PlayerName == "" {
        http.Error(w, "playerName is required", http.StatusBadRequest)
        return
    }

    if !isValidDifficulty(payload.Difficulty) {
        http.Error(w, "difficulty must be easy|medium|hard", http.StatusBadRequest)
        return
    }

    if payload.Rating < 0 || payload.Kills < 0 || payload.TimeMs < 0 {
        http.Error(w, "rating/kills/timeMs must be non-negative", http.StatusBadRequest)
        return
    }

    saved := s.scores.Add(model.Score{
        PlayerName: payload.PlayerName,
        Difficulty: payload.Difficulty,
        Rating:     payload.Rating,
        Kills:      payload.Kills,
        TimeMs:     payload.TimeMs,
    })

    writeJSON(w, http.StatusCreated, saved)
}

func (s *Server) handleLeaderboard(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    difficulty := r.URL.Query().Get("difficulty")
    if difficulty != "" && !isValidDifficulty(difficulty) {
        http.Error(w, "difficulty must be easy|medium|hard", http.StatusBadRequest)
        return
    }

    limit := 20
    if raw := r.URL.Query().Get("limit"); raw != "" {
        parsed, err := strconv.Atoi(raw)
        if err != nil || parsed <= 0 || parsed > 100 {
            http.Error(w, "limit must be integer in [1,100]", http.StatusBadRequest)
            return
        }
        limit = parsed
    }

    writeJSON(w, http.StatusOK, s.scores.Leaderboard(difficulty, limit))
}

func isValidDifficulty(v string) bool {
    return v == "easy" || v == "medium" || v == "hard"
}

func writeJSON(w http.ResponseWriter, status int, data any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    _ = json.NewEncoder(w).Encode(data)
}
