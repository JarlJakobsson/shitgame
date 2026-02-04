# ============================================
# COMBAT SYSTEM
# ============================================

import random


class Combat:
    """Handles combat between two gladiators."""
    
    def __init__(self, player, opponent):
        """
        Initialize a combat encounter.
        
        Args:
            player (Gladiator): The player's gladiator
            opponent (Gladiator): The opponent gladiator
        """
        self.player = player
        self.opponent = opponent
        self.round = 0
        self.battle_log = []
    
    def calculate_attack_damage(self, attacker, defender):
        """
        Calculate damage for an attack.
        
        Args:
            attacker (Gladiator): The attacking gladiator
            defender (Gladiator): The defending gladiator
            
        Returns:
            tuple: (damage, is_critical_hit)
        """
        # Base damage from strength
        base_damage = attacker.strength + random.randint(1, 10)

        # Miss chance based on weaponskill
        base_miss_chance = 10  # percent
        miss_chance = max(0, base_miss_chance - attacker.weaponskill)
        miss_roll = random.randint(1, 100)
        if miss_roll <= miss_chance:
            return 0, False  # Miss

        # Dodge chance based on defender's agility (0-100)
        dodge_roll = random.randint(1, 100)
        dodge_chance = defender.agility * 2  # 2% per agility point
        if dodge_roll <= dodge_chance:
            return 0, False  # Dodge

        # Critical hit chance (static 5%)
        crit_roll = random.randint(1, 100)
        if crit_roll <= 5:
            base_damage = int(base_damage * 1.5)
            return base_damage, True  # Critical hit

        return base_damage, False
    
    def execute_round(self):
        """
        Execute one round of combat.
        Returns:
            dict: Round information
        """
        self.round += 1
        round_info = {"round": self.round, "actions": []}



        # Player attacks first
        damage, critical = self.calculate_attack_damage(self.player, self.opponent)
        if damage == 0:
            action = f"{self.player.name} MISSES!"
        else:
            actual_damage = self.opponent.take_damage(damage)
            hit_type = " (CRITICAL!)" if critical else ""
            action = f"{self.player.name} hits {self.opponent.name} for {actual_damage} damage{hit_type}"
        round_info["actions"].append(action)

        # Check if opponent is defeated
        if not self.opponent.is_alive():
            round_info["winner"] = "player"
            return round_info

        # Opponent attacks
        damage, critical = self.calculate_attack_damage(self.opponent, self.player)
        if damage == 0:
            action = f"{self.opponent.name} MISSES!"
        else:
            actual_damage = self.player.take_damage(damage)
            hit_type = " (CRITICAL!)" if critical else ""
            action = f"{self.opponent.name} hits {self.player.name} for {actual_damage} damage{hit_type}"
        round_info["actions"].append(action)

        # Check if player is defeated
        if not self.player.is_alive():
            round_info["winner"] = "opponent"
            return round_info

        round_info["winner"] = None
        return round_info
    
    def get_state(self):
        """Get current combat state."""
        return {
            "round": self.round,
            "player_health": self.player.current_health,
            "player_max_health": self.player.max_health,
            "opponent_health": self.opponent.current_health,
            "opponent_max_health": self.opponent.max_health,
            "player_name": self.player.name,
            "opponent_name": self.opponent.name,
            "battle_log": self.battle_log
        }
