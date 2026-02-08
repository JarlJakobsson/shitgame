"""
Unit tests for combat functionality.
"""

from unittest.mock import patch

from combat import Combat
from gladiator import Gladiator


class TestCombat:
    """Test cases for the Combat class."""

    def test_combat_initialization(self):
        player = Gladiator("Player", "Human", use_race_stats=True)
        opponent = Gladiator("Opponent", "Orc", use_race_stats=True)

        combat = Combat(player, opponent)

        assert combat.player == player
        assert combat.opponent == opponent
        assert combat.round == 0
        assert isinstance(combat.battle_log, list)
        assert combat.player_max_rounds == Combat._round_capacity_from_stamina(player.stamina)
        assert combat.opponent_max_rounds == Combat._round_capacity_from_stamina(opponent.stamina)

    def test_stamina_capacity_curve(self):
        assert Combat._round_capacity_from_stamina(0) == 2
        assert Combat._round_capacity_from_stamina(1) >= 2
        assert Combat._round_capacity_from_stamina(18) == 6
        assert Combat._round_capacity_from_stamina(30) == 8
        assert Combat._round_capacity_from_stamina(32) == 9
        assert Combat._round_capacity_from_stamina(177) == 30
        assert Combat._round_capacity_from_stamina(30) > Combat._round_capacity_from_stamina(20)

    def test_calculate_attack_damage_miss(self):
        attacker = Gladiator("Attacker", "Human", use_race_stats=False)
        attacker.strength = 30
        attacker.weaponskill = 10

        defender = Gladiator("Defender", "Human", use_race_stats=False)
        defender.dodge = 100

        combat = Combat(attacker, defender)

        with patch("combat.random.uniform", return_value=1.0), patch("combat.random.random", return_value=0.99):
            damage, critical = combat.calculate_attack_damage(attacker, defender)

        assert damage == 0
        assert critical is False

    def test_calculate_attack_damage_critical(self):
        attacker = Gladiator("Attacker", "Human", use_race_stats=False)
        attacker.strength = 30
        attacker.weaponskill = 100

        defender = Gladiator("Defender", "Human", use_race_stats=False)
        defender.dodge = 1

        combat = Combat(attacker, defender)

        with patch("combat.random.uniform", return_value=1.0), patch("combat.random.random", return_value=0.0), patch("combat.random.randint", return_value=1):
            damage, critical = combat.calculate_attack_damage(attacker, defender)

        assert damage > 0
        assert critical is True

    def test_execute_round_increments_and_returns_expected_shape(self):
        player = Gladiator("Player", "Human", use_race_stats=False)
        player.max_health = player.current_health = 20
        player.strength = 20
        player.weaponskill = 50
        player.dodge = 1
        player.initiative = 20
        player.stamina = 30

        opponent = Gladiator("Opponent", "Orc", use_race_stats=False)
        opponent.max_health = opponent.current_health = 20
        opponent.strength = 20
        opponent.weaponskill = 50
        opponent.dodge = 1
        opponent.initiative = 10
        opponent.stamina = 30

        combat = Combat(player, opponent)

        with patch("combat.random.random", return_value=0.0), patch("combat.random.uniform", return_value=1.0), patch("combat.random.randint", return_value=100):
            round_info = combat.execute_round()

        assert round_info["round"] == 1
        assert isinstance(round_info["actions"], list)
        assert "winner" in round_info
        assert len(round_info["actions"]) >= 2

    def test_stamina_exhaustion_order_first_attacker_checked_first(self):
        player = Gladiator("Player", "Human", use_race_stats=False)
        opponent = Gladiator("Opponent", "Orc", use_race_stats=False)

        player.max_health = player.current_health = 999
        opponent.max_health = opponent.current_health = 999
        player.strength = opponent.strength = 1
        player.weaponskill = opponent.weaponskill = 1
        player.dodge = opponent.dodge = 9999
        player.initiative = opponent.initiative = 0

        player.stamina = 18
        opponent.stamina = 18

        combat = Combat(player, opponent)
        combat.round = combat.player_max_rounds + 1
        round_info = {"round": combat.round, "actions": []}
        exhausted = combat._check_exhaustion(round_info, player)
        assert exhausted is True
        assert round_info["winner"] == "opponent"

    def test_round_two_triggers_exhaustion_for_zero_stamina(self):
        player = Gladiator("Player", "Human", use_race_stats=False)
        opponent = Gladiator("Opponent", "Orc", use_race_stats=False)

        player.max_health = player.current_health = 999
        opponent.max_health = opponent.current_health = 999
        player.strength = opponent.strength = 1
        player.weaponskill = opponent.weaponskill = 1
        player.dodge = opponent.dodge = 9999
        player.initiative = 10
        opponent.initiative = 0
        player.stamina = 0
        opponent.stamina = 0

        combat = Combat(player, opponent)

        with patch("combat.random.random", return_value=0.0), patch("combat.random.uniform", return_value=1.0), patch("combat.random.randint", return_value=100):
            round1 = combat.execute_round()
            round2 = combat.execute_round()
            round3 = combat.execute_round()

        assert round1["winner"] is None
        assert round2["winner"] in {"player", "opponent"}
        assert round3["winner"] in {"player", "opponent"}

    def test_get_state(self):
        player = Gladiator("Player", "Human", use_race_stats=False)
        opponent = Gladiator("Opponent", "Orc", use_race_stats=False)

        player.max_health = player.current_health = 10
        opponent.max_health = opponent.current_health = 12

        combat = Combat(player, opponent)
        state = combat.get_state()

        assert state["round"] == 0
        assert state["player_name"] == "Player"
        assert state["opponent_name"] == "Opponent"
        assert state["player_max_health"] == 10
        assert state["opponent_max_health"] == 12
