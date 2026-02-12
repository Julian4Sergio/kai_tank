import { TankGame } from "./game.js";

const game = new TankGame({
  canvas: document.querySelector("#game-canvas"),
  hud: document.querySelector("#hud"),
  banner: document.querySelector("#banner"),
  form: document.querySelector("#menu-form"),
  nameInput: document.querySelector("#player-name"),
  difficultySelect: document.querySelector("#difficulty"),
  leaderboardEl: document.querySelector("#leaderboard"),
  bestRatingEl: document.querySelector("#best-rating"),
});

game.boot();
