package model

type Score struct {
    ID          int64   `json:"id"`
    PlayerName  string  `json:"playerName"`
    Difficulty  string  `json:"difficulty"`
    Rating      float64 `json:"rating"`
    Kills       int     `json:"kills"`
    Deaths      int     `json:"deaths"`
    BulletsUsed int     `json:"bulletsUsed"`
    LevelReached int    `json:"levelReached"`
    Victory     int     `json:"victory"`
    PlayTimeSec float64 `json:"playTimeSec"`
    TimeMs      int     `json:"timeMs"`
    PlayedAt    string  `json:"playedAt"`
    CreatedAt   int64   `json:"createdAt"`
}
