import random
from dataclasses import dataclass

import pygame

from tank_game.config import BULLET_SPEED
from tank_game.config import ENEMY_COLOR
from tank_game.config import SCREEN_HEIGHT
from tank_game.config import SCREEN_WIDTH


@dataclass
class Bullet:
    pos: pygame.Vector2
    direction: pygame.Vector2
    owner: str

    def update(self) -> None:
        self.pos += self.direction * BULLET_SPEED

    def rect(self) -> pygame.Rect:
        size = 6
        return pygame.Rect(int(self.pos.x - size / 2), int(self.pos.y - size / 2), size, size)

    def offscreen(self) -> bool:
        return self.pos.x < 0 or self.pos.x > SCREEN_WIDTH or self.pos.y < 0 or self.pos.y > SCREEN_HEIGHT


@dataclass
class Obstacle:
    rect: pygame.Rect
    kind: str
    hp: int

    def hit(self) -> bool:
        if self.kind == "steel":
            return False
        self.hp -= 1
        return self.hp <= 0


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    life: int
    max_life: int
    color: tuple[int, int, int]
    radius: int

    def update(self) -> None:
        self.pos += self.vel
        self.vel.y += 0.05
        self.life -= 1

    def alive(self) -> bool:
        return self.life > 0


class Tank:
    def __init__(self, x: float, y: float, color: tuple[int, int, int], speed: float) -> None:
        self.pos = pygame.Vector2(x, y)
        self.direction = pygame.Vector2(0, -1)
        self.color = color
        self.speed = speed
        self.size = pygame.Vector2(36, 36)
        self.last_fire_ms = 0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.pos.x - self.size.x / 2),
            int(self.pos.y - self.size.y / 2),
            int(self.size.x),
            int(self.size.y),
        )

    def draw(self, screen: pygame.Surface) -> None:
        body = self.rect()
        pygame.draw.rect(screen, self.color, body, border_radius=5)
        pygame.draw.rect(screen, (16, 16, 16), body, 2, border_radius=5)
        muzzle_end = self.pos + self.direction * 22
        pygame.draw.line(screen, self.color, self.pos, muzzle_end, 6)

    def move(self, vector: pygame.Vector2) -> None:
        if vector.length_squared() == 0:
            return
        vector = vector.normalize()
        self.direction = vector
        self.pos += vector * self.speed
        self.pos.x = max(self.size.x / 2, min(SCREEN_WIDTH - self.size.x / 2, self.pos.x))
        self.pos.y = max(self.size.y / 2, min(SCREEN_HEIGHT - self.size.y / 2, self.pos.y))

    def can_fire(self, cooldown_ms: int) -> bool:
        return pygame.time.get_ticks() - self.last_fire_ms >= cooldown_ms

    def fire(self, owner: str) -> Bullet:
        self.last_fire_ms = pygame.time.get_ticks()
        return Bullet(self.pos + self.direction * 26, self.direction.copy(), owner)


class EnemyTank(Tank):
    def __init__(self, x: float, y: float, speed: float) -> None:
        super().__init__(x, y, ENEMY_COLOR, speed)
        self.change_dir_at = pygame.time.get_ticks() + random.randint(280, 900)

    def update(self, player_pos: pygame.Vector2) -> None:
        now = pygame.time.get_ticks()
        if now >= self.change_dir_at:
            if random.random() < 0.58:
                self.direction = (player_pos - self.pos).normalize() if player_pos != self.pos else pygame.Vector2(0, 1)
            else:
                self.direction = random.choice(
                    [pygame.Vector2(0, -1), pygame.Vector2(0, 1), pygame.Vector2(-1, 0), pygame.Vector2(1, 0)]
                )
            self.change_dir_at = now + random.randint(280, 900)

        self.move(self.direction)
        if self.pos.x <= self.size.x / 2 or self.pos.x >= SCREEN_WIDTH - self.size.x / 2:
            self.direction.x *= -1
        if self.pos.y <= self.size.y / 2 or self.pos.y >= SCREEN_HEIGHT - self.size.y / 2:
            self.direction.y *= -1
