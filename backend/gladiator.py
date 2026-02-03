# ============================================
# GLADIATOR CLASS AND ATTRIBUTES
# ============================================

from races import RACES
from constants import STARTING_GOLD, STARTING_EXPERIENCE


class Gladiator:
    """Represents a gladiator warrior in the arena."""
    
    def __init__(self, name: str, race: str = None):
        """
        Initialize a gladiator.
        
        Args:
            name (str): The gladiator's name
            race (str): The gladiator's race (Human or Orc)
        """
        self.name: str = name
        self.race: str = race
        
        # Get base stats from race, if provided
        if race is not None:
            race_stats = RACES[race]
            self.max_health: int = race_stats["health"]
            self.current_health: int = self.max_health
            self.strength: int = race_stats["strength"]
            self.agility: int = race_stats["agility"]
            self.initiative: int = race_stats["initiative"]
            self.weaponskill: int = race_stats["weaponskill"]
        else:
            self.max_health: int = 0
            self.current_health: int = 0
            self.strength: int = 0
            self.agility: int = 0
            self.initiative: int = 0
            self.weaponskill: int = 0
        
        # Game stats
        self.experience: int = STARTING_EXPERIENCE
        self.level: int = 1
        self.gold: int = STARTING_GOLD
        self.wins: int = 0
        self.losses: int = 0
    
    def to_dict(self):
        """Convert gladiator to dictionary for API responses."""
        return {
            "name": self.name,
            "race": self.race,
            "level": self.level,
            "experience": self.experience,
            "current_health": self.current_health,
            "max_health": self.max_health,
            "strength": self.strength,
            "agility": self.agility,
            "initiative": self.initiative,
            "weaponskill": self.weaponskill,
            "gold": self.gold,
            "wins": self.wins,
            "losses": self.losses
        }
    
    def take_damage(self, damage):
        """
        Reduce health by damage amount.
        Args:
            damage (int): The damage dealt
        """
        self.current_health -= damage
        return damage
    
    def heal(self, amount):
        """
        Restore health up to max.
        
        Args:
            amount (int): Amount to heal
        """
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def is_alive(self):
        """Check if gladiator is still alive."""
        return self.current_health > 0
