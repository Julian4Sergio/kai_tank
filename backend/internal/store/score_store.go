package store

import (
    "sort"
    "sync"
    "time"

    "tank-game/backend/internal/model"
)

type ScoreStore struct {
    mu     sync.RWMutex
    nextID int64
    data   []model.Score
}

func NewScoreStore() *ScoreStore {
    return &ScoreStore{nextID: 1}
}

func (s *ScoreStore) Add(score model.Score) model.Score {
    s.mu.Lock()
    defer s.mu.Unlock()

    score.ID = s.nextID
    score.CreatedAt = time.Now().UnixMilli()
    s.nextID++
    s.data = append(s.data, score)
    return score
}

func (s *ScoreStore) Leaderboard(difficulty string, limit int) []model.Score {
    s.mu.RLock()
    defer s.mu.RUnlock()

    if limit <= 0 {
        limit = 20
    }

    filtered := make([]model.Score, 0, len(s.data))
    for _, score := range s.data {
        if difficulty == "" || score.Difficulty == difficulty {
            filtered = append(filtered, score)
        }
    }

    sort.Slice(filtered, func(i, j int) bool {
        a, b := filtered[i], filtered[j]
        if a.Rating != b.Rating {
            return a.Rating > b.Rating
        }
        if a.Kills != b.Kills {
            return a.Kills > b.Kills
        }
        if a.TimeMs != b.TimeMs {
            return a.TimeMs < b.TimeMs
        }
        return a.CreatedAt < b.CreatedAt
    })

    if limit > len(filtered) {
        limit = len(filtered)
    }
    return filtered[:limit]
}
