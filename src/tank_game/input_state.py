import ctypes

import pygame


MOVE_KEYS = {
    pygame.K_w: pygame.Vector2(0, -1),
    pygame.K_UP: pygame.Vector2(0, -1),
    pygame.K_s: pygame.Vector2(0, 1),
    pygame.K_DOWN: pygame.Vector2(0, 1),
    pygame.K_a: pygame.Vector2(-1, 0),
    pygame.K_LEFT: pygame.Vector2(-1, 0),
    pygame.K_d: pygame.Vector2(1, 0),
    pygame.K_RIGHT: pygame.Vector2(1, 0),
}

VK_CODES = {
    "W": 0x57,
    "A": 0x41,
    "S": 0x53,
    "D": 0x44,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "SPACE": 0x20,
    "ENTER": 0x0D,
    "R": 0x52,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
}


def poll_async_keys() -> set[str]:
    pressed: set[str] = set()
    for name, vk in VK_CODES.items():
        if ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000:
            pressed.add(name)
    return pressed
