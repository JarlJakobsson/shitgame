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
        "description": "Balanced warriors with versatile combat skills"
    },
    "Orc": {
        "health": 120,
        "strength": 10,
        "agility": 5,
        "initiative": 7,
        "weaponskill": 3,
        "description": "Powerful and hardy, with high health and strength"
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
