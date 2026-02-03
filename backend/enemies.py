# ============================================
# ENEMY DEFINITIONS
# ============================================

ENEMIES = {
    "Goblin": {
        "health": 60,
        "strength": 5,
        "agility": 10,
        "initiative": 12,
        "weaponskill": 3,
        "description": "A sneaky goblin, quick but fragile."
    },
    "Skeleton": {
        "health": 80,
        "strength": 7,
        "agility": 7,
        "initiative": 8,
        "weaponskill": 4,
        "description": "A reanimated skeleton, hard to kill."
    },
    "Minotaur": {
        "health": 140,
        "strength": 14,
        "agility": 4,
        "initiative": 6,
        "weaponskill": 6,
        "description": "A massive beast with brutal power."
    },
    "Dark Knight": {
        "health": 110,
        "strength": 10,
        "agility": 8,
        "initiative": 9,
        "weaponskill": 8,
        "description": "A fallen knight, skilled and dangerous."
    },
    "Slime": {
        "health": 50,
        "strength": 3,
        "agility": 5,
        "initiative": 5,
        "weaponskill": 1,
        "description": "A weak but persistent blob of goo."
    },
    "Bandit": {
        "health": 90,
        "strength": 8,
        "agility": 11,
        "initiative": 11,
        "weaponskill": 5,
        "description": "A quick and greedy human outlaw."
    }
}

def get_enemy(enemy_name):
    """
    Get enemy attributes by name.
    Args:
        enemy_name (str): The name of the enemy
    Returns:
        dict: Enemy attributes, or None if not found
    """
    return ENEMIES.get(enemy_name)
