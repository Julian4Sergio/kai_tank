package model

type Score struct {
    ID         int64  `json:"id"`
    PlayerName string `json:"playerName"`
    Difficulty string `json:"difficulty"`
    Rating     int    `json:"rating"`
    Kills      int    `json:"kills"`
    TimeMs     int    `json:"timeMs"`
    CreatedAt  int64  `json:"createdAt"`
}
