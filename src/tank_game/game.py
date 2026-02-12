import getpass
import random
import sys

import pygame

from tank_game.config import BG_COLOR
from tank_game.config import BRICK_COLOR
from tank_game.config import DEFAULT_PLAYER_NAME
from tank_game.config import BULLET_COLOR
from tank_game.config import DB_PATH
from tank_game.config import DIFFICULTIES
from tank_game.config import DIFFICULTY_RATING_CAP
from tank_game.config import FPS
from tank_game.config import GOOD_COLOR
from tank_game.config import GRID_COLOR
from tank_game.config import LEADERBOARD_LIMIT
from tank_game.config import PLAYER_COLOR
from tank_game.config import PLAYER_LIVES
from tank_game.config import RESPAWN_INVINCIBLE_MS
from tank_game.config import SCREEN_HEIGHT
from tank_game.config import SCREEN_WIDTH
from tank_game.config import STEEL_COLOR
from tank_game.config import TEXT_COLOR
from tank_game.config import TOTAL_LEVELS
from tank_game.config import WARN_COLOR
from tank_game.entities import Bullet
from tank_game.entities import EnemyTank
from tank_game.entities import Obstacle
from tank_game.entities import Particle
from tank_game.entities import Tank
from tank_game.input_state import poll_async_keys
from tank_game.namegen import random_player_name
from tank_game.scoring import calculate_rating
from tank_game.storage import GameStatsStore


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Tank Battle")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.key.start_text_input()
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 20)
        self.big_font = pygame.font.SysFont("consolas", 42, bold=True)
        self.title_font = pygame.font.SysFont("consolas", 52, bold=True)

        self.grid_surface = self._build_grid_surface()
        self.overlay_soft = self._build_overlay(130)
        self.overlay_mid = self._build_overlay(150)
        self.overlay_light = self._build_overlay(120)

        self.store = GameStatsStore(DB_PATH)
        self.player_name = DEFAULT_PLAYER_NAME or getpass.getuser()
        self.player_name_input = self.player_name
        self.menu_stage = "name"
        self.menu_selected_difficulty = "medium"
        self.leaderboard = self.store.top_results(LEADERBOARD_LIMIT, difficulty=self.menu_selected_difficulty)
        self.best_rating = self.store.best_rating(difficulty=self.menu_selected_difficulty)

        self.state = "menu"
        self.level = 1
        self.lives = PLAYER_LIVES
        self.difficulty_key = "medium"
        self.cfg = DIFFICULTIES[self.difficulty_key]

        self.player: Tank | None = None
        self.enemies: list[EnemyTank] = []
        self.bullets: list[Bullet] = []
        self.obstacles: list[Obstacle] = []

        self.level_transition_until = 0
        self.particles: list[Particle] = []

        self.round_start_ms = 0
        self.round_kills = 0
        self.round_deaths = 0
        self.round_shots = 0
        self.round_saved = False
        self.final_elapsed_sec = 0.0
        self.final_rating = 0.0
        self.player_invincible_until = 0

        self.frame_keydown: set[int] = set()
        self.pressed_keys: set[int] = set()
        self.async_keys_now: set[str] = set()
        self.async_keys_prev: set[str] = set()

    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            pygame.event.pump()
            self.frame_keydown.clear()
            self._handle_events()
            self._poll_async_keys()

            if self._just_pressed("R", pygame.K_r):
                self._return_to_menu()

            if self.state == "menu":
                self._update_menu()
            elif self.state == "playing":
                self._update_playing()
            elif self.state == "level_transition":
                self._update_level_transition()
            elif self.state == "victory":
                self._update_victory()

            self._draw()

    def _return_to_menu(self) -> None:
        self.state = "menu"
        self.menu_stage = "name"
        self.level = 1
        self.lives = PLAYER_LIVES
        self.final_elapsed_sec = 0.0
        self.final_rating = 0.0
        self.player = None
        self.enemies = []
        self.bullets = []
        self.obstacles = []
        self.particles = []
        self.player_invincible_until = 0
        self._refresh_leaderboard_for_menu()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self.frame_keydown.add(event.key)
                self.pressed_keys.add(event.key)
                if self.state == "menu" and self.menu_stage == "name":
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name_input = self.player_name_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        self._commit_player_name()
                        self.menu_stage = "difficulty"
                        self._refresh_leaderboard_for_menu()
                    elif event.key == pygame.K_n:
                        self._set_random_player_name()
            if event.type == pygame.TEXTINPUT and self.state == "menu" and self.menu_stage == "name":
                if event.text.isprintable() and len(self.player_name_input) < 16:
                    self.player_name_input += event.text
            if event.type == pygame.KEYUP:
                self.pressed_keys.discard(event.key)

    def _poll_async_keys(self) -> None:
        self.async_keys_prev = self.async_keys_now
        self.async_keys_now = poll_async_keys()

    def _just_pressed(self, async_key: str, pygame_key: int) -> bool:
        return (async_key in self.async_keys_now and async_key not in self.async_keys_prev) or (pygame_key in self.frame_keydown)

    def _is_pressed(self, async_key: str, pygame_key: int, key_state: pygame.key.ScancodeWrapper) -> bool:
        return async_key in self.async_keys_now or pygame_key in self.pressed_keys or key_state[pygame_key]

    def _start_game(self, difficulty_key: str) -> None:
        self.difficulty_key = difficulty_key
        self.cfg = DIFFICULTIES[difficulty_key]
        self.level = 1
        self.lives = PLAYER_LIVES

        self.round_start_ms = pygame.time.get_ticks()
        self.round_kills = 0
        self.round_deaths = 0
        self.round_shots = 0
        self.round_saved = False
        self.final_elapsed_sec = 0.0
        self.final_rating = 0.0

        self._start_level(self.level)
        self.state = "playing"

    def _start_level(self, level: int) -> None:
        self.player = Tank(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 56, PLAYER_COLOR, self.cfg["player_speed"])
        self.obstacles = self._build_level_obstacles(level)
        self.enemies = self._spawn_enemies(self._enemy_count_for_level(level), self._enemy_speed_for_level(level))
        self.bullets = []
        self.player_invincible_until = pygame.time.get_ticks() + RESPAWN_INVINCIBLE_MS

    def _enemy_count_for_level(self, level: int) -> int:
        return self.cfg["base_enemy_count"] + (level - 1)

    def _enemy_speed_for_level(self, level: int) -> float:
        return self.cfg["enemy_speed"] * (1.0 + 0.08 * (level - 1))

    def _enemy_fire_cd_for_level(self, level: int) -> int:
        scale = 1.0 + 0.12 * (level - 1)
        return max(500, int(self.cfg["enemy_fire_cd"] / scale))

    def _enemy_fire_chance_for_level(self, level: int) -> float:
        return self.cfg["enemy_fire_chance"] * (1.0 + 0.15 * (level - 1))

    def _spawn_enemies(self, count: int, speed: float) -> list[EnemyTank]:
        enemies: list[EnemyTank] = []
        player_spawn = pygame.Rect(int(SCREEN_WIDTH / 2 - 52), int(SCREEN_HEIGHT - 112), 104, 96)
        attempts = 0
        while len(enemies) < count and attempts < 4000:
            attempts += 1
            candidate = EnemyTank(random.randint(48, SCREEN_WIDTH - 48), random.randint(42, SCREEN_HEIGHT // 2), speed)
            c_rect = candidate.rect()
            if c_rect.colliderect(player_spawn):
                continue
            if any(c_rect.colliderect(o.rect) for o in self.obstacles):
                continue
            if any(c_rect.colliderect(e.rect()) for e in enemies):
                continue
            enemies.append(candidate)
        return enemies

    def _build_level_obstacles(self, level: int) -> list[Obstacle]:
        rng = random.Random((level * 7919) + 17)
        tile = 32
        obstacles: list[Obstacle] = []

        safe_zone = pygame.Rect(int(SCREEN_WIDTH / 2 - 86), SCREEN_HEIGHT - 150, 172, 130)
        enemy_safe_band = pygame.Rect(0, 0, SCREEN_WIDTH, 84)

        def add(kind: str, gx: int, gy: int) -> None:
            rect = pygame.Rect(gx * tile, gy * tile, tile, tile)
            if rect.colliderect(safe_zone) or rect.colliderect(enemy_safe_band):
                return
            if rect.left < 32 or rect.right > SCREEN_WIDTH - 32:
                return
            if rect.top < 32 or rect.bottom > SCREEN_HEIGHT - 32:
                return
            if any(rect.colliderect(o.rect) for o in obstacles):
                return
            obstacles.append(Obstacle(rect=rect, kind=kind, hp=2 if kind == "brick" else 9999))

        center_col = SCREEN_WIDTH // tile // 2
        for gy in range(3, (SCREEN_HEIGHT // tile) - 2):
            if gy not in (7, 8):
                add("steel", center_col, gy)

        for _ in range(14 + level * 3):
            gx = rng.randint(1, (SCREEN_WIDTH // tile) - 2)
            gy = rng.randint(3, (SCREEN_HEIGHT // tile) - 2)
            kind = "steel" if rng.random() < (0.16 + level * 0.03) else "brick"
            add(kind, gx, gy)

        return obstacles

    def _update_menu(self) -> None:
        if self.menu_stage == "name":
            self._commit_player_name()
            return

        if self._just_pressed("1", pygame.K_1):
            self.menu_selected_difficulty = "easy"
            self._refresh_leaderboard_for_menu()
        elif self._just_pressed("2", pygame.K_2):
            self.menu_selected_difficulty = "medium"
            self._refresh_leaderboard_for_menu()
        elif self._just_pressed("3", pygame.K_3):
            self.menu_selected_difficulty = "hard"
            self._refresh_leaderboard_for_menu()
        elif self._just_pressed("ENTER", pygame.K_RETURN):
            self._start_game(self.menu_selected_difficulty)

    def _commit_player_name(self) -> None:
        cleaned = self.player_name_input.strip()
        self.player_name = cleaned if cleaned else (DEFAULT_PLAYER_NAME or getpass.getuser())

    def _set_random_player_name(self) -> None:
        self.player_name_input = random_player_name()
        self._commit_player_name()

    def _refresh_leaderboard_for_menu(self) -> None:
        self.leaderboard = self.store.top_results(LEADERBOARD_LIMIT, difficulty=self.menu_selected_difficulty)
        self.best_rating = self.store.best_rating(difficulty=self.menu_selected_difficulty)

    def _move_tank_with_obstacles(self, tank: Tank, vector: pygame.Vector2) -> None:
        if vector.length_squared() == 0:
            return
        old_pos = tank.pos.copy()
        tank.move(vector)
        if any(tank.rect().colliderect(ob.rect) for ob in self.obstacles):
            tank.pos = old_pos

    def _update_playing(self) -> None:
        if not self.player:
            return

        move_vector = pygame.Vector2(0, 0)
        key_state = pygame.key.get_pressed()
        if self._is_pressed("W", pygame.K_w, key_state) or self._is_pressed("UP", pygame.K_UP, key_state):
            move_vector += pygame.Vector2(0, -1)
        if self._is_pressed("S", pygame.K_s, key_state) or self._is_pressed("DOWN", pygame.K_DOWN, key_state):
            move_vector += pygame.Vector2(0, 1)
        if self._is_pressed("A", pygame.K_a, key_state) or self._is_pressed("LEFT", pygame.K_LEFT, key_state):
            move_vector += pygame.Vector2(-1, 0)
        if self._is_pressed("D", pygame.K_d, key_state) or self._is_pressed("RIGHT", pygame.K_RIGHT, key_state):
            move_vector += pygame.Vector2(1, 0)
        self._move_tank_with_obstacles(self.player, move_vector)

        if self._just_pressed("SPACE", pygame.K_SPACE):
            player_shots = sum(1 for b in self.bullets if b.owner == "player")
            if player_shots < self.cfg["max_player_bullets"] and self.player.can_fire(self.cfg["player_fire_cd"]):
                self.bullets.append(self.player.fire("player"))
                self.round_shots += 1

        fire_cd = self._enemy_fire_cd_for_level(self.level)
        fire_chance = self._enemy_fire_chance_for_level(self.level)
        for enemy in self.enemies:
            enemy.update(self.player.pos)
            if any(enemy.rect().colliderect(ob.rect) for ob in self.obstacles):
                enemy.pos -= enemy.direction * enemy.speed
                enemy.direction = random.choice(
                    [pygame.Vector2(0, -1), pygame.Vector2(0, 1), pygame.Vector2(-1, 0), pygame.Vector2(1, 0)]
                )
            if enemy.can_fire(fire_cd) and random.random() < fire_chance:
                enemy.direction = (self.player.pos - enemy.pos).normalize() if enemy.pos != self.player.pos else enemy.direction
                self.bullets.append(enemy.fire("enemy"))

        for bullet in self.bullets:
            bullet.update()
        self.bullets = [bullet for bullet in self.bullets if not bullet.offscreen()]

        if self._resolve_hits():
            return

        if not self.enemies:
            if self.level >= TOTAL_LEVELS:
                self.state = "victory"
                self._init_victory_animation()
                self._save_round_if_needed(victory=True)
            else:
                self.state = "level_transition"
                self.level_transition_until = pygame.time.get_ticks() + 1300

    def _resolve_hits(self) -> bool:
        if not self.player:
            return False

        for bullet in self.bullets[:]:
            hit_obstacle = next((o for o in self.obstacles if bullet.rect().colliderect(o.rect)), None)
            if hit_obstacle:
                self.bullets.remove(bullet)
                if hit_obstacle.hit():
                    self.obstacles.remove(hit_obstacle)

        removed: set[int] = set()
        for i, b1 in enumerate(self.bullets):
            if i in removed:
                continue
            for j in range(i + 1, len(self.bullets)):
                if j in removed:
                    continue
                b2 = self.bullets[j]
                if b1.owner != b2.owner and b1.rect().colliderect(b2.rect()):
                    removed.add(i)
                    removed.add(j)
                    break
        if removed:
            self.bullets = [b for idx, b in enumerate(self.bullets) if idx not in removed]

        for bullet in self.bullets[:]:
            if bullet.owner == "enemy" and bullet.rect().colliderect(self.player.rect()):
                self.bullets.remove(bullet)
                if self._handle_player_hit():
                    return True
                continue
            if bullet.owner == "player":
                hit_enemy = next((e for e in self.enemies if bullet.rect().colliderect(e.rect())), None)
                if hit_enemy:
                    self.enemies.remove(hit_enemy)
                    self.bullets.remove(bullet)
                    self.round_kills += 1

        for enemy in self.enemies:
            if enemy.rect().colliderect(self.player.rect()) and self._handle_player_hit():
                return True
        return False

    def _handle_player_hit(self) -> bool:
        now = pygame.time.get_ticks()
        if now < self.player_invincible_until:
            return False

        self.lives -= 1
        self.round_deaths += 1
        if self.lives <= 0:
            self.state = "defeat"
            self._save_round_if_needed(victory=False)
            return True

        if self.player:
            self.player.pos = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 56)
            self.player.direction = pygame.Vector2(0, -1)
        self.bullets = [b for b in self.bullets if b.owner == "player"]
        self.player_invincible_until = now + RESPAWN_INVINCIBLE_MS
        return False

    def _update_level_transition(self) -> None:
        if pygame.time.get_ticks() >= self.level_transition_until:
            self.level += 1
            self._start_level(self.level)
            self.state = "playing"

    def _init_victory_animation(self) -> None:
        self.particles = []
        for _ in range(6):
            self._spawn_firework_burst(random.randint(100, SCREEN_WIDTH - 100), random.randint(80, 220))

    def _spawn_firework_burst(self, x: int, y: int) -> None:
        colors = [(255, 120, 120), (255, 220, 100), (120, 220, 255), (150, 255, 150)]
        for _ in range(24):
            angle = random.uniform(0, 6.28318)
            speed = random.uniform(1.5, 4.5)
            vel = pygame.Vector2(speed, 0).rotate_rad(angle)
            life = random.randint(35, 60)
            self.particles.append(
                Particle(
                    pos=pygame.Vector2(x, y),
                    vel=vel,
                    life=life,
                    max_life=life,
                    color=random.choice(colors),
                    radius=random.randint(2, 4),
                )
            )

    def _update_victory(self) -> None:
        if random.random() < 0.05:
            self._spawn_firework_burst(random.randint(90, SCREEN_WIDTH - 90), random.randint(70, 230))
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.alive()]

    def _calculate_rating(self, victory: bool) -> float:
        elapsed = max(1.0, (pygame.time.get_ticks() - self.round_start_ms) / 1000.0)
        return calculate_rating(
            difficulty_key=self.difficulty_key,
            elapsed_sec=elapsed,
            kills=self.round_kills,
            shots=self.round_shots,
            deaths=self.round_deaths,
            victory=victory,
        )

    def _save_round_if_needed(self, victory: bool) -> None:
        if self.round_saved:
            return

        self.final_elapsed_sec = max(1.0, (pygame.time.get_ticks() - self.round_start_ms) / 1000.0)
        self.final_rating = calculate_rating(
            difficulty_key=self.difficulty_key,
            elapsed_sec=self.final_elapsed_sec,
            kills=self.round_kills,
            shots=self.round_shots,
            deaths=self.round_deaths,
            victory=victory,
        )

        self.store.add_result(
            player_name=self.player_name,
            difficulty=self.difficulty_key,
            level_reached=self.level,
            victory=victory,
            play_time_sec=self.final_elapsed_sec,
            kills=self.round_kills,
            deaths=self.round_deaths,
            bullets_used=self.round_shots,
            rating=self.final_rating,
        )
        self.round_saved = True
        self._refresh_leaderboard_for_menu()

    def _build_grid_surface(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill(BG_COLOR)
        gap = 32
        for x in range(0, SCREEN_WIDTH, gap):
            pygame.draw.line(surf, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, gap):
            pygame.draw.line(surf, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
        return surf

    def _build_overlay(self, alpha: int) -> pygame.Surface:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        return overlay

    def _draw_hud(self) -> None:
        diff = DIFFICULTIES[self.difficulty_key]["label"]
        top = self.font.render(
            f"Lv {self.level}/{TOTAL_LEVELS}  Kills {self.round_kills}  Lives {self.lives}  Diff {diff}  FPS {self.clock.get_fps():.0f}",
            True,
            TEXT_COLOR,
        )
        tip = self.font.render("Move: WASD/Arrows  Fire: SPACE  R: Menu", True, TEXT_COLOR)
        self.screen.blit(top, (10, 8))
        self.screen.blit(tip, (10, 32))

    def _draw_menu(self) -> None:
        title = self.title_font.render("TANK BATTLE", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH / 2 - title.get_width() / 2, 32))

        if self.menu_stage == "name":
            step = self.font.render("Step 1/2: Enter Player Name", True, GOOD_COLOR)
            player = self.font.render(f"Player Name: {self.player_name_input or '_'}", True, TEXT_COLOR)
            tip1 = self.font.render("Type name, Backspace delete", True, TEXT_COLOR)
            tip2 = self.font.render("N random name, Enter continue", True, TEXT_COLOR)
            self.screen.blit(step, (SCREEN_WIDTH / 2 - step.get_width() / 2, 100))
            self.screen.blit(player, (SCREEN_WIDTH / 2 - player.get_width() / 2, 142))
            self.screen.blit(tip1, (SCREEN_WIDTH / 2 - tip1.get_width() / 2, 176))
            self.screen.blit(tip2, (SCREEN_WIDTH / 2 - tip2.get_width() / 2, 202))
            return

        options = self.font.render("Step 2/2: 1 Easy   2 Medium   3 Hard", True, GOOD_COLOR)
        start_tip = self.font.render("Press Enter to start", True, TEXT_COLOR)
        selected_label = DIFFICULTIES[self.menu_selected_difficulty]["label"]
        cap = DIFFICULTY_RATING_CAP[self.menu_selected_difficulty]
        best = self.font.render(f"{selected_label} Top Rating: {self.best_rating:.2f}/{cap:.1f}", True, TEXT_COLOR)
        self.screen.blit(options, (SCREEN_WIDTH / 2 - options.get_width() / 2, 92))
        self.screen.blit(start_tip, (SCREEN_WIDTH / 2 - start_tip.get_width() / 2, 122))
        self.screen.blit(best, (SCREEN_WIDTH / 2 - best.get_width() / 2, 150))

        board_title = self.font.render(f"Leaderboard ({selected_label})", True, GOOD_COLOR)
        self.screen.blit(board_title, (34, 188))

        if not self.leaderboard:
            empty = self.font.render("No records yet. Play one round to create rankings.", True, TEXT_COLOR)
            self.screen.blit(empty, (34, 218))
            return

        y = 218
        for idx, row in enumerate(self.leaderboard, start=1):
            line = (
                f"{idx:>2}. {row['player_name'][:10]:<10} "
                f"{float(row['rating']):>4.2f}/{cap:.1f} "
                f"K:{int(row['kills']):<2} D:{int(row['deaths']):<2} "
                f"T:{float(row['play_time_sec']):>5.1f}s"
            )
            self.screen.blit(self.font.render(line, True, GOOD_COLOR if idx == 1 else TEXT_COLOR), (34, y))
            y += 24

    def _draw_level_transition(self) -> None:
        msg = self.big_font.render(f"LEVEL {self.level} CLEAR", True, GOOD_COLOR)
        nxt = self.font.render(f"Next: Level {self.level + 1}", True, TEXT_COLOR)
        self.screen.blit(msg, (SCREEN_WIDTH / 2 - msg.get_width() / 2, SCREEN_HEIGHT / 2 - 42))
        self.screen.blit(nxt, (SCREEN_WIDTH / 2 - nxt.get_width() / 2, SCREEN_HEIGHT / 2 + 8))

    def _draw_defeat(self) -> None:
        rating = self.final_rating if self.round_saved else self._calculate_rating(victory=False)
        cap = DIFFICULTY_RATING_CAP.get(self.difficulty_key, 10.0)
        msg = self.big_font.render("GAME OVER", True, WARN_COLOR)
        stat = self.font.render(
            f"Kills {self.round_kills}  Deaths {self.round_deaths}  Shots {self.round_shots}  Rating {rating:.2f}/{cap:.1f}",
            True,
            TEXT_COLOR,
        )
        hint = self.font.render("Press R to menu", True, TEXT_COLOR)
        self.screen.blit(msg, (SCREEN_WIDTH / 2 - msg.get_width() / 2, SCREEN_HEIGHT / 2 - 52))
        self.screen.blit(stat, (SCREEN_WIDTH / 2 - stat.get_width() / 2, SCREEN_HEIGHT / 2 + 2))
        self.screen.blit(hint, (SCREEN_WIDTH / 2 - hint.get_width() / 2, SCREEN_HEIGHT / 2 + 30))

    def _draw_victory(self) -> None:
        for particle in self.particles:
            alpha = max(35, int(255 * (particle.life / particle.max_life)))
            color = (particle.color[0], particle.color[1], particle.color[2], alpha)
            surf = pygame.Surface((particle.radius * 2 + 2, particle.radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (particle.radius + 1, particle.radius + 1), particle.radius)
            self.screen.blit(surf, (particle.pos.x - particle.radius, particle.pos.y - particle.radius))

        rating = self.final_rating if self.round_saved else self._calculate_rating(victory=True)
        cap = DIFFICULTY_RATING_CAP.get(self.difficulty_key, 10.0)
        msg = self.big_font.render("ALL 5 LEVELS CLEAR!", True, GOOD_COLOR)
        stat = self.font.render(
            f"Kills {self.round_kills}  Deaths {self.round_deaths}  Shots {self.round_shots}  Rating {rating:.2f}/{cap:.1f}",
            True,
            TEXT_COLOR,
        )
        hint = self.font.render("Press R to menu", True, TEXT_COLOR)
        self.screen.blit(msg, (SCREEN_WIDTH / 2 - msg.get_width() / 2, SCREEN_HEIGHT / 2 - 44))
        self.screen.blit(stat, (SCREEN_WIDTH / 2 - stat.get_width() / 2, SCREEN_HEIGHT / 2 + 2))
        self.screen.blit(hint, (SCREEN_WIDTH / 2 - hint.get_width() / 2, SCREEN_HEIGHT / 2 + 30))

    def _draw_world(self) -> None:
        self.screen.blit(self.grid_surface, (0, 0))

        for obstacle in self.obstacles:
            if obstacle.kind == "brick":
                pygame.draw.rect(self.screen, BRICK_COLOR, obstacle.rect, border_radius=3)
                pygame.draw.rect(self.screen, (120, 66, 38), obstacle.rect, 2, border_radius=3)
            else:
                pygame.draw.rect(self.screen, STEEL_COLOR, obstacle.rect, border_radius=3)
                pygame.draw.rect(self.screen, (88, 96, 108), obstacle.rect, 2, border_radius=3)

        if self.player:
            now = pygame.time.get_ticks()
            invincible = now < self.player_invincible_until
            if (not invincible) or ((now // 120) % 2 == 0):
                self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            pygame.draw.circle(self.screen, BULLET_COLOR, (int(bullet.pos.x), int(bullet.pos.y)), 4)

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)
        if self.state == "menu":
            self._draw_menu()
        else:
            self._draw_world()
            self._draw_hud()
            if self.state == "level_transition":
                self.screen.blit(self.overlay_soft, (0, 0))
                self._draw_level_transition()
            elif self.state == "defeat":
                self.screen.blit(self.overlay_mid, (0, 0))
                self._draw_defeat()
            elif self.state == "victory":
                self.screen.blit(self.overlay_light, (0, 0))
                self._draw_victory()

        pygame.display.flip()
