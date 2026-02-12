import random


RANDOM_NAME_ADJ = ["Swift", "Iron", "Lucky", "Shadow", "Turbo", "Nova", "Pixel", "Silent"]
RANDOM_NAME_NOUN = ["Tiger", "Falcon", "Comet", "Panda", "Ranger", "Blazer", "Knight", "Rocket"]


def random_player_name(max_len: int = 16) -> str:
    name = f"{random.choice(RANDOM_NAME_ADJ)}{random.choice(RANDOM_NAME_NOUN)}{random.randint(10, 99)}"
    return name[:max_len]
