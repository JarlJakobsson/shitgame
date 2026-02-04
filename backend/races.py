# ============================================
# RACE DEFINITIONS
# ============================================

RACES = {
    "Human": {
        "health": 100,
        "strength": 8,
        "agility": 8,
        "initiative": 10,
        "weaponskill": 5,
        "description": "Balanced warriors with versatile combat skills",
        "origin": "City-states of the inner realm",
        "specialty": "Adaptability and disciplined combat"
    },
    "Orc": {
        "health": 120,
        "strength": 10,
        "agility": 5,
        "initiative": 7,
        "weaponskill": 3,
        "description": "Powerful and hardy, with high health and strength",
        "origin": "Volcanic badlands and war camps",
        "specialty": "Brute force and endurance"
    },
    "Goblin": {
        "health": 60,
        "strength": 4,
        "agility": 12,
        "initiative": 14,
        "weaponskill": 2,
        "description": "Super fast but fragile, relying on speed over power",
        "origin": "Cave warrens and overgrown ruins",
        "specialty": "Speed, trickery, and ambushes"
    },
    "Minotaur": {
        "health": 150,
        "strength": 15,
        "agility": 3,
        "initiative": 5,
        "weaponskill": 5,
        "description": "Slow and crushingly strong, built to overpower enemies",
        "origin": "Ancient labyrinths of the south",
        "specialty": "Raw power and unstoppable charges"
    },
    "Skeleton": {
        "health": 90,
        "strength": 7,
        "agility": 6,
        "initiative": 7,
        "weaponskill": 5,
        "description": "Steady and resilient, harder to put down than it looks",
        "origin": "Forgotten crypts and ruined battlefields",
        "specialty": "Relentless endurance and fearlessness"
    }
}


def get_race(race_name):
    """
    Get race attributes by name.
    
    Args:
        race_name (str): The name of the race
        
    Returns:
        dict: Race attributes, or None if not found
    """
    return RACES.get(race_name)
