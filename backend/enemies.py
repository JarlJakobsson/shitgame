# ============================================
# ENEMY DEFINITIONS
# ============================================

ENEMIES = {
    "Goblin": {
        "health": 60,
        "strength": 5,
        "dodge": 10,
        "initiative": 12,
        "weaponskill": 3,
        "stamina": 27,
        "min_level": 3,
        "description": "A sneaky goblin, quick but fragile."
    },
    "Skeleton": {
        "health": 80,
        "strength": 7,
        "dodge": 7,
        "initiative": 8,
        "weaponskill": 4,
        "stamina": 41,
        "min_level": 4,
        "description": "A reanimated skeleton, hard to kill."
    },
    "Minotaur": {
        "health": 140,
        "strength": 14,
        "dodge": 4,
        "initiative": 6,
        "weaponskill": 6,
        "stamina": 58,
        "min_level": 8,
        "description": "A massive beast with brutal power."
    },
    "Dark Knight": {
        "health": 110,
        "strength": 10,
        "dodge": 8,
        "initiative": 9,
        "weaponskill": 8,
        "stamina": 47,
        "min_level": 6,
        "description": "A fallen knight, skilled and dangerous."
    },
    "Slime": {
        "health": 50,
        "strength": 3,
        "dodge": 5,
        "initiative": 5,
        "weaponskill": 1,
        "stamina": 24,
        "min_level": 1,
        "description": "A weak but persistent blob of goo."
    },
    "Bandit": {
        "health": 90,
        "strength": 8,
        "dodge": 11,
        "initiative": 11,
        "weaponskill": 5,
        "stamina": 34,
        "min_level": 2,
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
