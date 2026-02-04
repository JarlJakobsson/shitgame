# ============================================
# COMBAT SYSTEM
# ============================================

import random
import math


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
        self.player_stamina = max(0, int(player.stamina))
        self.opponent_stamina = max(0, int(opponent.stamina))

    @staticmethod
    def _required_stamina_for_round(round_number):
        if round_number <= 2:
            return 0
        # Power curve fit to the provided table (approximate).
        a = 1.3081954270168985
        b = 1.4465293529691468
        return max(0, int(round(a * (round_number ** b))))

    def _drain_stamina_end_of_round(self, round_info):
        required_now = self._required_stamina_for_round(self.round)
        required_prev = self._required_stamina_for_round(self.round - 1)
        drain = max(0, required_now - required_prev)

        self.player_stamina = max(0, self.player_stamina - drain)
        self.opponent_stamina = max(0, self.opponent_stamina - drain)

        round_info["actions"].append(
            f"Stamina drain {drain}: {self.player.name}={self.player_stamina}, {self.opponent.name}={self.opponent_stamina}"
        )

        # Check in order: player 1 then player 2.
        if self.player_stamina <= 0:
            round_info["actions"].append(f"{self.player.name} collapses from exhaustion!")
            round_info["winner"] = "opponent"
            return True
        if self.opponent_stamina <= 0:
            round_info["actions"].append(f"{self.opponent.name} collapses from exhaustion!")
            round_info["winner"] = "player"
            return True
        return False
    
    def calculate_attack_damage(self, attacker, defender):
        """
        Calculate damage for an attack.
        
        Args:
            attacker (Gladiator): The attacking gladiator
            defender (Gladiator): The defending gladiator
            
        Returns:
            tuple: (damage, is_critical_hit)
        """
        # Base damage from strength with a small multiplier-based randomizer
        base_damage = attacker.strength * 0.088
        damage_multiplier = random.uniform(0.85, 1.15)
        base_damage = int(round(base_damage * damage_multiplier))
        if base_damage == 0 and attacker.strength > 0:
            base_damage = 1

        # Hit chance based on a weaponskill vs dodge contest
        hit_rating = max(1.0, attacker.weaponskill)
        dodge_rating = max(1.0, defender.dodge * 0.25)
        hit_chance = hit_rating / (hit_rating + dodge_rating)
        hit_chance = max(0.05, min(0.95, hit_chance))
        if random.random() > hit_chance:
            return 0, False  # Miss

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
        # Determine who goes first each round based on initiative difference
        init_diff = self.player.initiative - self.opponent.initiative
        first_chance = 0.5 + (init_diff * 0.045)
        first_chance = max(0.05, min(0.95, first_chance))
        player_first = random.random() < first_chance

        first_attacker = self.player if player_first else self.opponent
        first_defender = self.opponent if player_first else self.player

        # First attacker
        damage, critical = self.calculate_attack_damage(first_attacker, first_defender)
        if damage == 0:
            action = f"{first_attacker.name} MISSES!"
        else:
            actual_damage = first_defender.take_damage(damage)
            hit_type = " (CRITICAL!)" if critical else ""
            action = f"{first_attacker.name} hits {first_defender.name} for {actual_damage} damage{hit_type}"
        round_info["actions"].append(action)

        # Check if defender is defeated
        if not first_defender.is_alive():
            round_info["winner"] = "player" if first_attacker == self.player else "opponent"
            return round_info

        # Second attacker
        second_attacker = first_defender
        second_defender = first_attacker
        damage, critical = self.calculate_attack_damage(second_attacker, second_defender)
        if damage == 0:
            action = f"{second_attacker.name} MISSES!"
        else:
            actual_damage = second_defender.take_damage(damage)
            hit_type = " (CRITICAL!)" if critical else ""
            action = f"{second_attacker.name} hits {second_defender.name} for {actual_damage} damage{hit_type}"
        round_info["actions"].append(action)

        # Check if defender is defeated
        if not second_defender.is_alive():
            round_info["winner"] = "player" if second_attacker == self.player else "opponent"
            return round_info

        if self._drain_stamina_end_of_round(round_info):
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
