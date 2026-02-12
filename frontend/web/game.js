import { bestRating, saveResult, topResults } from "./db.js";

const WIDTH = 960;
const HEIGHT = 600;
const TILE = 32;
const TOTAL_LEVELS = 5;
const PLAYER_LIVES = 3;
const RESPAWN_INV_MS = 1300;
const LEADERBOARD_LIMIT = 8;

const COLORS = {
  bg: "#171f2b",
  grid: "#243041",
  player: "#5ce08f",
  enemy: "#df6f62",
  bullet: "#ffe08a",
  brick: "#bc7a4e",
  steel: "#8e9aa9",
  text: "#e9f2ff",
};

const DIFFICULTIES = {
  easy: {
    label: "Easy",
    playerSpeed: 230,
    enemySpeed: 80,
    playerFireCd: 0.2,
    enemyFireCd: 1.7,
    enemyFireChance: 0.007,
    maxPlayerBullets: 6,
    baseEnemyCount: 3,
    cap: 7.5,
  },
  medium: {
    label: "Medium",
    playerSpeed: 210,
    enemySpeed: 102,
    playerFireCd: 0.26,
    enemyFireCd: 1.4,
    enemyFireChance: 0.011,
    maxPlayerBullets: 5,
    baseEnemyCount: 4,
    cap: 9,
  },
  hard: {
    label: "Hard",
    playerSpeed: 185,
    enemySpeed: 128,
    playerFireCd: 0.3,
    enemyFireCd: 1.0,
    enemyFireChance: 0.017,
    maxPlayerBullets: 4,
    baseEnemyCount: 5,
    cap: 10,
  },
};

const SCORE = {
  targetKills: 30,
  targetTimeSec: 220,
  wKills: 0.32,
  wAccuracy: 0.28,
  wTime: 0.2,
  wSurvival: 0.1,
  wVictory: 0.1,
};

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function collides(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function seeded(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function calculateRating(difficulty, elapsedSec, kills, shots, deaths, victory) {
  const cfg = DIFFICULTIES[difficulty];
  const elapsed = Math.max(1, elapsedSec);
  const killScore = Math.min(1, kills / SCORE.targetKills);
  const accuracy = Math.min(1, kills / Math.max(1, shots));
  const timeScore = Math.max(0, 1 - (elapsed - 1) / SCORE.targetTimeSec);
  const survival = Math.max(0, 1 - deaths / PLAYER_LIVES);
  const victoryBonus = victory ? 1 : 0;
  const weighted =
    killScore * SCORE.wKills +
    accuracy * SCORE.wAccuracy +
    timeScore * SCORE.wTime +
    survival * SCORE.wSurvival +
    victoryBonus * SCORE.wVictory;
  return Math.round(clamp(weighted * cfg.cap, 0, cfg.cap) * 100) / 100;
}

export class TankGame {
  constructor({ canvas, hud, banner, form, nameInput, difficultySelect, leaderboardEl, bestRatingEl }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.hud = hud;
    this.banner = banner;
    this.form = form;
    this.nameInput = nameInput;
    this.difficultySelect = difficultySelect;
    this.leaderboardEl = leaderboardEl;
    this.bestRatingEl = bestRatingEl;

    this.state = "menu";
    this.playerName = "Player";
    this.menuDifficulty = "medium";
    this.diffKey = "medium";

    this.keysDown = new Set();
    this.keysEdge = new Set();
    this.lastTs = performance.now();

    this.level = 1;
    this.lives = PLAYER_LIVES;
    this.player = null;
    this.enemies = [];
    this.bullets = [];
    this.obstacles = [];
    this.transitionUntil = 0;
    this.invUntil = 0;

    this.roundStartSec = 0;
    this.roundKills = 0;
    this.roundDeaths = 0;
    this.roundShots = 0;
    this.saved = false;
    this.finalRating = 0;

    this.installEvents();
  }

  async boot() {
    await this.refreshLeaderboard();
    this.loop = this.loop.bind(this);
    requestAnimationFrame(this.loop);
  }

  installEvents() {
    window.addEventListener("keydown", (e) => {
      const k = e.key.toLowerCase();
      if (!this.keysDown.has(k)) this.keysEdge.add(k);
      this.keysDown.add(k);
      if ([" ", "arrowup", "arrowdown", "arrowleft", "arrowright"].includes(k)) e.preventDefault();
      if (k === "r") this.backToMenu();
    });

    window.addEventListener("keyup", (e) => {
      this.keysDown.delete(e.key.toLowerCase());
    });

    this.difficultySelect.addEventListener("change", async () => {
      this.menuDifficulty = this.difficultySelect.value;
      await this.refreshLeaderboard();
    });

    this.form.addEventListener("submit", async (e) => {
      e.preventDefault();
      this.playerName = (this.nameInput.value || "Player").trim().slice(0, 16) || "Player";
      this.menuDifficulty = this.difficultySelect.value;
      this.startRound(this.menuDifficulty);
    });
  }

  keyPressed(...aliases) {
    return aliases.some((k) => this.keysDown.has(k));
  }

  keyEdge(...aliases) {
    return aliases.some((k) => this.keysEdge.has(k));
  }

  startRound(diffKey) {
    this.state = "playing";
    this.diffKey = diffKey;
    this.level = 1;
    this.lives = PLAYER_LIVES;
    this.roundStartSec = performance.now() / 1000;
    this.roundKills = 0;
    this.roundDeaths = 0;
    this.roundShots = 0;
    this.saved = false;
    this.finalRating = 0;
    this.banner.textContent = "";
    this.startLevel(1);
  }

  startLevel(level) {
    const cfg = DIFFICULTIES[this.diffKey];
    this.player = { x: WIDTH / 2 - 18, y: HEIGHT - 78, w: 36, h: 36, dx: 0, dy: -1, speed: cfg.playerSpeed, lastFire: 0 };
    this.obstacles = this.buildObstacles(level);
    this.enemies = this.spawnEnemies(cfg.baseEnemyCount + level - 1, cfg.enemySpeed * (1 + 0.08 * (level - 1)));
    this.bullets = [];
    this.invUntil = performance.now() + RESPAWN_INV_MS;
  }

  spawnEnemies(count, speed) {
    const list = [];
    const spawnBox = { x: WIDTH / 2 - 52, y: HEIGHT - 112, w: 104, h: 96 };
    let guard = 0;
    while (list.length < count && guard < 4000) {
      guard += 1;
      const e = {
        x: 40 + Math.random() * (WIDTH - 80),
        y: 30 + Math.random() * (HEIGHT / 2 - 60),
        w: 36,
        h: 36,
        dx: 0,
        dy: 1,
        speed,
        changeDirAt: performance.now() + 280 + Math.random() * 700,
        lastFire: 0,
      };
      if (collides(e, spawnBox)) continue;
      if (this.obstacles.some((o) => collides(e, o))) continue;
      if (list.some((t) => collides(e, t))) continue;
      list.push(e);
    }
    return list;
  }

  buildObstacles(level) {
    const rng = seeded(level * 7919 + 17);
    const list = [];
    const safeZone = { x: WIDTH / 2 - 86, y: HEIGHT - 150, w: 172, h: 130 };
    const enemyBand = { x: 0, y: 0, w: WIDTH, h: 84 };

    const add = (type, gx, gy) => {
      const o = { x: gx * TILE, y: gy * TILE, w: TILE, h: TILE, hp: type === "brick" ? 2 : 9999, type };
      if (collides(o, safeZone) || collides(o, enemyBand)) return;
      if (o.x < 32 || o.x + o.w > WIDTH - 32) return;
      if (o.y < 32 || o.y + o.h > HEIGHT - 32) return;
      if (list.some((it) => collides(o, it))) return;
      list.push(o);
    };

    const centerCol = Math.floor(WIDTH / TILE / 2);
    for (let gy = 3; gy < Math.floor(HEIGHT / TILE) - 2; gy += 1) {
      if (gy !== 7 && gy !== 8) add("steel", centerCol, gy);
    }
    const count = 14 + level * 3;
    for (let i = 0; i < count; i += 1) {
      const gx = 1 + Math.floor(rng() * (Math.floor(WIDTH / TILE) - 2));
      const gy = 3 + Math.floor(rng() * (Math.floor(HEIGHT / TILE) - 5));
      add(rng() < 0.16 + level * 0.03 ? "steel" : "brick", gx, gy);
    }
    return list;
  }

  fireFrom(actor, owner) {
    this.bullets.push({
      x: actor.x + actor.w / 2 + actor.dx * 23,
      y: actor.y + actor.h / 2 + actor.dy * 23,
      r: 4,
      dx: actor.dx,
      dy: actor.dy,
      owner,
      speed: 460,
    });
  }

  backToMenu() {
    this.state = "menu";
    this.banner.textContent = "";
    this.refreshLeaderboard();
  }

  moveActor(actor, dt, dx, dy) {
    if (!dx && !dy) return;
    const len = Math.hypot(dx, dy) || 1;
    actor.dx = dx / len;
    actor.dy = dy / len;
    const oldX = actor.x;
    const oldY = actor.y;
    actor.x += actor.dx * actor.speed * dt;
    actor.y += actor.dy * actor.speed * dt;
    actor.x = clamp(actor.x, 0, WIDTH - actor.w);
    actor.y = clamp(actor.y, 0, HEIGHT - actor.h);
    if (this.obstacles.some((o) => collides(actor, o))) {
      actor.x = oldX;
      actor.y = oldY;
    }
  }

  enemyFireCd(level) {
    const cfg = DIFFICULTIES[this.diffKey];
    return Math.max(0.5, cfg.enemyFireCd / (1 + 0.12 * (level - 1)));
  }

  enemyFireChance(level) {
    const cfg = DIFFICULTIES[this.diffKey];
    return cfg.enemyFireChance * (1 + 0.15 * (level - 1));
  }

  updatePlaying(dt, now) {
    const cfg = DIFFICULTIES[this.diffKey];
    const p = this.player;

    let dx = 0;
    let dy = 0;
    if (this.keyPressed("w", "arrowup")) dy -= 1;
    if (this.keyPressed("s", "arrowdown")) dy += 1;
    if (this.keyPressed("a", "arrowleft")) dx -= 1;
    if (this.keyPressed("d", "arrowright")) dx += 1;
    this.moveActor(p, dt, dx, dy);

    if (this.keyEdge(" ") || this.keyEdge("space")) {
      const activePlayerBullets = this.bullets.filter((b) => b.owner === "player").length;
      if (activePlayerBullets < cfg.maxPlayerBullets && now - p.lastFire >= cfg.playerFireCd * 1000) {
        p.lastFire = now;
        this.fireFrom(p, "player");
        this.roundShots += 1;
      }
    }

    const fireCd = this.enemyFireCd(this.level) * 1000;
    const fireChance = this.enemyFireChance(this.level);
    for (const e of this.enemies) {
      if (now >= e.changeDirAt) {
        if (Math.random() < 0.58) {
          const tx = p.x - e.x;
          const ty = p.y - e.y;
          const l = Math.hypot(tx, ty) || 1;
          e.dx = tx / l;
          e.dy = ty / l;
        } else {
          const dirs = [
            [0, -1],
            [0, 1],
            [-1, 0],
            [1, 0],
          ];
          const pick = dirs[Math.floor(Math.random() * dirs.length)];
          e.dx = pick[0];
          e.dy = pick[1];
        }
        e.changeDirAt = now + 300 + Math.random() * 900;
      }
      this.moveActor(e, dt, e.dx, e.dy);

      if (now - e.lastFire >= fireCd && Math.random() < fireChance) {
        const tx = p.x - e.x;
        const ty = p.y - e.y;
        const l = Math.hypot(tx, ty) || 1;
        e.dx = tx / l;
        e.dy = ty / l;
        e.lastFire = now;
        this.fireFrom(e, "enemy");
      }
    }

    for (const b of this.bullets) {
      b.x += b.dx * b.speed * dt;
      b.y += b.dy * b.speed * dt;
    }
    this.bullets = this.bullets.filter((b) => b.x >= 0 && b.x <= WIDTH && b.y >= 0 && b.y <= HEIGHT);

    if (this.resolveHits(now)) return;

    if (this.enemies.length === 0) {
      if (this.level >= TOTAL_LEVELS) {
        this.state = "victory";
        this.banner.textContent = "ALL 5 LEVELS CLEAR";
        this.saveResult(true);
      } else {
        this.state = "transition";
        this.transitionUntil = now + 1200;
        this.banner.textContent = `LEVEL ${this.level} CLEAR`;
      }
    }
  }

  hitPlayer(now) {
    if (now < this.invUntil) return false;
    this.lives -= 1;
    this.roundDeaths += 1;
    if (this.lives <= 0) {
      this.state = "defeat";
      this.banner.textContent = "GAME OVER";
      this.saveResult(false);
      return true;
    }
    this.player.x = WIDTH / 2 - this.player.w / 2;
    this.player.y = HEIGHT - 78;
    this.player.dx = 0;
    this.player.dy = -1;
    this.bullets = this.bullets.filter((b) => b.owner === "player");
    this.invUntil = now + RESPAWN_INV_MS;
    return false;
  }

  resolveHits(now) {
    for (const b of [...this.bullets]) {
      const rect = { x: b.x - b.r, y: b.y - b.r, w: b.r * 2, h: b.r * 2 };
      const hit = this.obstacles.find((o) => collides(rect, o));
      if (!hit) continue;
      this.bullets.splice(this.bullets.indexOf(b), 1);
      if (hit.type === "brick") {
        hit.hp -= 1;
        if (hit.hp <= 0) this.obstacles.splice(this.obstacles.indexOf(hit), 1);
      }
    }

    const removeIdx = new Set();
    for (let i = 0; i < this.bullets.length; i += 1) {
      if (removeIdx.has(i)) continue;
      for (let j = i + 1; j < this.bullets.length; j += 1) {
        if (removeIdx.has(j)) continue;
        const a = this.bullets[i];
        const b = this.bullets[j];
        if (a.owner === b.owner) continue;
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d <= a.r + b.r + 1) {
          removeIdx.add(i);
          removeIdx.add(j);
          break;
        }
      }
    }
    if (removeIdx.size) this.bullets = this.bullets.filter((_, idx) => !removeIdx.has(idx));

    for (const b of [...this.bullets]) {
      const bRect = { x: b.x - b.r, y: b.y - b.r, w: b.r * 2, h: b.r * 2 };
      if (b.owner === "enemy" && collides(bRect, this.player)) {
        this.bullets.splice(this.bullets.indexOf(b), 1);
        if (this.hitPlayer(now)) return true;
      } else if (b.owner === "player") {
        const hitEnemy = this.enemies.find((e) => collides(bRect, e));
        if (hitEnemy) {
          this.bullets.splice(this.bullets.indexOf(b), 1);
          this.enemies.splice(this.enemies.indexOf(hitEnemy), 1);
          this.roundKills += 1;
        }
      }
    }

    for (const e of this.enemies) {
      if (collides(e, this.player) && this.hitPlayer(now)) return true;
    }
    return false;
  }

  async saveResult(victory) {
    if (this.saved) return;
    const elapsed = Math.max(1, performance.now() / 1000 - this.roundStartSec);
    this.finalRating = calculateRating(
      this.diffKey,
      elapsed,
      this.roundKills,
      this.roundShots,
      this.roundDeaths,
      victory
    );
    await saveResult({
      playedAt: new Date().toISOString(),
      playerName: this.playerName,
      difficulty: this.diffKey,
      levelReached: this.level,
      victory: victory ? 1 : 0,
      playTimeSec: elapsed,
      kills: this.roundKills,
      deaths: this.roundDeaths,
      bulletsUsed: this.roundShots,
      rating: this.finalRating,
    });
    this.saved = true;
    await this.refreshLeaderboard();
  }

  async refreshLeaderboard() {
    const diff = this.menuDifficulty;
    const cap = DIFFICULTIES[diff].cap;
    const rows = await topResults(LEADERBOARD_LIMIT, diff);
    const best = await bestRating(diff);
    this.bestRatingEl.textContent = `Top Rating: ${best.toFixed(2)}/${cap.toFixed(1)}`;
    this.leaderboardEl.innerHTML = "";
    if (!rows.length) {
      const li = document.createElement("li");
      li.textContent = "No records yet.";
      this.leaderboardEl.appendChild(li);
      return;
    }
    rows.forEach((r) => {
      const li = document.createElement("li");
      li.textContent = `${r.playerName.slice(0, 10)}  ${r.rating.toFixed(2)}/${cap.toFixed(1)}  K:${r.kills} D:${
        r.deaths
      } T:${r.playTimeSec.toFixed(1)}s`;
      this.leaderboardEl.appendChild(li);
    });
  }

  drawGrid() {
    const c = this.ctx;
    c.fillStyle = COLORS.bg;
    c.fillRect(0, 0, WIDTH, HEIGHT);
    c.strokeStyle = COLORS.grid;
    c.lineWidth = 1;
    for (let x = 0; x < WIDTH; x += TILE) {
      c.beginPath();
      c.moveTo(x, 0);
      c.lineTo(x, HEIGHT);
      c.stroke();
    }
    for (let y = 0; y < HEIGHT; y += TILE) {
      c.beginPath();
      c.moveTo(0, y);
      c.lineTo(WIDTH, y);
      c.stroke();
    }
  }

  drawTank(t, color) {
    const c = this.ctx;
    c.fillStyle = color;
    c.strokeStyle = "#111";
    c.lineWidth = 2;
    c.fillRect(t.x, t.y, t.w, t.h);
    c.strokeRect(t.x, t.y, t.w, t.h);
    const cx = t.x + t.w / 2;
    const cy = t.y + t.h / 2;
    c.beginPath();
    c.moveTo(cx, cy);
    c.lineTo(cx + t.dx * 24, cy + t.dy * 24);
    c.lineWidth = 6;
    c.strokeStyle = color;
    c.stroke();
  }

  render() {
    this.drawGrid();
    const c = this.ctx;
    for (const o of this.obstacles) {
      c.fillStyle = o.type === "brick" ? COLORS.brick : COLORS.steel;
      c.fillRect(o.x, o.y, o.w, o.h);
    }
    for (const b of this.bullets) {
      c.fillStyle = COLORS.bullet;
      c.beginPath();
      c.arc(b.x, b.y, b.r, 0, Math.PI * 2);
      c.fill();
    }
    for (const e of this.enemies) this.drawTank(e, COLORS.enemy);
    const now = performance.now();
    if (this.player && (now > this.invUntil || Math.floor(now / 120) % 2 === 0)) {
      this.drawTank(this.player, COLORS.player);
    }

    const diffLabel = DIFFICULTIES[this.diffKey].label;
    this.hud.textContent =
      this.state === "menu"
        ? `Menu · select name and difficulty`
        : `Lv ${this.level}/${TOTAL_LEVELS} · Kills ${this.roundKills} · Lives ${this.lives} · Diff ${diffLabel}`;
  }

  loop(ts) {
    const now = ts;
    const dt = Math.min(0.05, (now - this.lastTs) / 1000);
    this.lastTs = now;

    if (this.state === "playing") this.updatePlaying(dt, now);
    else if (this.state === "transition" && now >= this.transitionUntil) {
      this.level += 1;
      this.state = "playing";
      this.banner.textContent = "";
      this.startLevel(this.level);
    }

    this.render();
    this.keysEdge.clear();
    requestAnimationFrame(this.loop);
  }
}


