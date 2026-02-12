package main

import (
    "log"
    "net/http"
    "os"

    "tank-game/backend/internal/app"
)

func main() {
    port := os.Getenv("PORT")
    if port == "" {
        port = "8081"
    }

    frontendOrigin := os.Getenv("FRONTEND_ORIGIN")
    if frontendOrigin == "" {
        frontendOrigin = "*"
    }

    server := app.NewServer(frontendOrigin)

    addr := ":" + port
    log.Printf("backend listening on %s", addr)
    if err := http.ListenAndServe(addr, server.Routes()); err != nil {
        log.Fatal(err)
    }
}
