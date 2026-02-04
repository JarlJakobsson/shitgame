# ============================================
# RACE DEFINITIONS
# ============================================

RACES = {
    "Human": {
        "health": 100,
        "strength": 8,
        "dodge": 8,
        "initiative": 10,
        "weaponskill": 5,
        "description": "Balanced warriors with versatile combat skills",
        "origin": "City-states of the inner realm",
        "specialty": "Adaptability and disciplined combat",
        "racials": [
            {
                "title": "Increased Critical Hit Chance",
                "description": "Humans start with a higher minimum and maximum critical hit chance than other races, giving them an edge in combat."
            },
            {
                "title": "Leadership",
                "description": "Humans have a 30% chance at the start of each combat round to unleash a leadership roar that increases their leadership and initiative by 15%. The minimum increase is +15 leadership and +10 initiative."
            }
        ],
        "racial_bonus": [
            { "stat": "Strength", "value": "+10%" },
            { "stat": "Health", "value": "+10%" },
            { "stat": "Stamina", "value": "+10%" },
            { "stat": "Dodge", "value": "+10%" },
            { "stat": "Initiative", "value": "+10%" }
        ]
    },
    "Orc": {
        "health": 120,
        "strength": 10,
        "dodge": 5,
        "initiative": 7,
        "weaponskill": 3,
        "description": "Powerful and hardy, with high health and strength",
        "origin": "Volcanic badlands and war camps",
        "specialty": "Brute force and endurance",
        "racials": [
            {
                "title": "Increased Critical Damage",
                "description": "Orcs are raging warriors and gain a damage bonus on critical hits. When an orc lands a critical hit, their critical damage increases by 7%."
            },
            {
                "title": "Berserk",
                "description": "Orcs have a strong will to survive (and inflict pain). When their HP falls below 90% of max HP, their strength increases by 10%. Damage dealt with the bonus strength cannot exceed the damage cap. Once activated, the effect lasts until the end of the fight."
            }
        ],
        "racial_bonus": [
            { "stat": "Health", "value": "+20%" },
            { "stat": "Strength", "value": "+30%" },
            { "stat": "Stamina", "value": "+0%" },
            { "stat": "Initiative", "value": "+0%" },
            { "stat": "Dodge", "value": "-30%" },
            { "stat": "Weaponskill", "value": "+10%" }
        ]
    },
    "Goblin": {
        "health": 60,
        "strength": 4,
        "dodge": 12,
        "initiative": 14,
        "weaponskill": 2,
        "description": "Super fast but fragile, relying on speed over power",
        "origin": "Cave warrens and overgrown ruins",
        "specialty": "Speed, trickery, and ambushes",
        "racials": [
            {
                "title": "Increased Bonus from Total Physique",
                "description": "Goblins' compact, agile build gives them a higher bonus to all physical stats from their total physique. (Each point in a physical stat gives a small boost to all physical stats — all races get this, but goblins get a higher bonus.)"
            },
            {
                "title": "Dirty Fighting Tricks",
                "description": "Goblins fight dirty and are not ashamed to use underhanded tactics. Each time they are attacked, they have a 20% chance to counter by throwing sand, grit, and dust into the attacker’s eyes, increasing the chance that the attacker misses their next attack by 5%."
            }
        ],
        "racial_bonus": [
            { "stat": "Health", "value": "-15%" },
            { "stat": "Strength", "value": "+20%" },
            { "stat": "Stamina", "value": "+0%" },
            { "stat": "Initiative", "value": "+10%" },
            { "stat": "Dodge", "value": "+30%" },
            { "stat": "Weaponskill", "value": "+10%" }
        ]
    },
    "Minotaur": {
        "health": 150,
        "strength": 15,
        "dodge": 3,
        "initiative": 5,
        "weaponskill": 5,
        "description": "Slow and crushingly strong, built to overpower enemies",
        "origin": "Ancient labyrinths of the south",
        "specialty": "Raw power and unstoppable charges",
        "racials": [
            {
                "title": "Enthralling Terror",
                "description": "Minotaurs are massive and intimidating. They have a 65% chance to frighten the opponent when they attack during the first round of a fight, causing the enemy to freeze and be unable to dodge the attack."
            },
            {
                "title": "Higher Weapon Damage Cap",
                "description": "A minotaur’s enormous strength lets them hit harder than other races. When using a weapon, their damage potential is 15% higher than others."
            }
        ],
        "racial_bonus": [
            { "stat": "Health", "value": "+50%" },
            { "stat": "Strength", "value": "+50%" },
            { "stat": "Stamina", "value": "-20%" },
            { "stat": "Initiative", "value": "-40%" },
            { "stat": "Dodge", "value": "-60%" },
            { "stat": "Weaponskill", "value": "-15%" }
        ]
    },
    "Skeleton": {
        "health": 90,
        "strength": 7,
        "dodge": 6,
        "initiative": 7,
        "weaponskill": 5,
        "description": "Steady and resilient, harder to put down than it looks",
        "origin": "Forgotten crypts and ruined battlefields",
        "specialty": "Relentless endurance and fearlessness",
        "racials": [
            {
                "title": "Life Drain",
                "description": "When the undead attack, they have a 10% chance to steal 5% of the opponent’s current HP and transfer it to themselves. Limited to a maximum of two times per round."
            }
        ],
        "racial_bonus": [
            { "stat": "Health", "value": "+10%" },
            { "stat": "Strength", "value": "+0%" },
            { "stat": "Stamina", "value": "+100%" },
            { "stat": "Initiative", "value": "-10%" },
            { "stat": "Dodge", "value": "+5%" },
            { "stat": "Weaponskill", "value": "+5%" }
        ]
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
