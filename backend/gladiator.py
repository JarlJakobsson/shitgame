# ============================================
# GLADIATOR CLASS AND ATTRIBUTES
# ============================================

from races import RACES
from constants import STARTING_GOLD, STARTING_EXPERIENCE




# Base Character class
class Character:
    """Represents a character in the arena (gladiator or enemy)."""
    def __init__(self, name: str):
        self.name: str = name
        self.race: str = None
        self.max_health: int = 0
        self.current_health: int = 0
        self.strength: int = 0
        self.dodge: int = 0
        self.initiative: int = 0
        self.weaponskill: int = 0
        self.stamina: int = 0

    def to_dict(self):
        return {
            "name": self.name,
            "race": self.race,
            "max_health": self.max_health,
            "current_health": self.current_health,
            "strength": self.strength,
            "dodge": self.dodge,
            "initiative": self.initiative,
            "weaponskill": self.weaponskill,
            "stamina": self.stamina,
        }

    def take_damage(self, damage):
        self.current_health -= damage
        return damage

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)

    def is_alive(self):
        return self.current_health > 0

# Gladiator subclass
class Gladiator(Character):
    def __init__(self, name: str, race: str = None, use_race_stats: bool = False):
        super().__init__(name)
        self.race = race
        # Gladiator-specific stats
        self.experience: int = STARTING_EXPERIENCE
        self.level: int = 1
        self.gold: int = STARTING_GOLD
        self.wins: int = 0
        self.losses: int = 0
        if use_race_stats:
            self.apply_race_stats()

    def apply_race_stats(self):
        if not self.race or self.race not in RACES:
            return

        race_data = RACES[self.race]
        self.max_health = race_data["health"]
        self.current_health = race_data["health"]
        self.strength = race_data["strength"]
        self.dodge = race_data["dodge"]
        self.initiative = race_data["initiative"]
        self.weaponskill = race_data["weaponskill"]
        self.stamina = race_data.get("stamina", max(1, race_data["health"] // 10))

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "level": self.level,
            "experience": self.experience,
            "gold": self.gold,
            "wins": self.wins,
            "losses": self.losses
        })
        return data

    def display_stats(self):
        print("\n===== GLADIATOR STATS =====")
        print(f"Name: {self.name}")
        print(f"Race: {self.race}")
        print(f"Level: {self.level}")
        print(f"Experience: {self.experience}")
        print(f"Gold: {self.gold}")
        print(f"Health: {self.current_health} / {self.max_health}")
        print(f"Stamina: {self.stamina}")
        print(f"Strength: {self.strength}")
        print(f"Dodge: {self.dodge}")
        print(f"Initiative: {self.initiative}")
        print(f"Weaponskill: {self.weaponskill}")
        print(f"Wins: {self.wins}")
        print(f"Losses: {self.losses}")

# Enemy subclass
class Enemy(Character):
    def __init__(self, name: str, stats: dict):
        super().__init__(name)
        self.race = "Enemy"
        self.max_health = stats["health"]
        self.current_health = stats["health"]
        self.strength = stats["strength"]
        self.dodge = stats["dodge"]
        self.initiative = stats["initiative"]
        self.weaponskill = stats["weaponskill"]
        self.stamina = stats["stamina"]
