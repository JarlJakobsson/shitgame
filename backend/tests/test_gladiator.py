"""
Unit tests for gladiator functionality.
"""

from math import floor

from gladiator import Gladiator
from races import RACES


class TestGladiator:
    """Test cases for the Gladiator class."""

    def test_gladiator_creation_basic(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)

        assert gladiator.name == "TestGladiator"
        assert gladiator.race == "Human"
        assert gladiator.level == 1
        assert gladiator.experience == 0
        assert gladiator.gold == 100
        assert gladiator.wins == 0
        assert gladiator.losses == 0

    def test_gladiator_creation_with_race_stats(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=True)
        human = RACES["Human"]

        assert gladiator.max_health == human["health"]
        assert gladiator.current_health == human["health"]
        assert gladiator.vitality == max(0, int(floor((human["health"] - 1) / 1.5)))
        assert gladiator.strength == human["strength"]
        assert gladiator.dodge == human["dodge"]
        assert gladiator.initiative == human["initiative"]
        assert gladiator.weaponskill == human["weaponskill"]

    def test_gladiator_apply_persisted_stats(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)

        persisted_stats = {
            "name": "PersistedGladiator",
            "race": "Orc",
            "level": 5,
            "experience": 250,
            "gold": 500,
            "wins": 10,
            "losses": 2,
            "vitality": 40,
            "max_health": 61,
            "current_health": 50,
            "strength": 35,
            "dodge": 20,
            "initiative": 18,
            "weaponskill": 25,
            "stamina": 30,
            "stat_points": 3,
        }

        gladiator.apply_persisted_stats(persisted_stats)

        assert gladiator.name == "PersistedGladiator"
        assert gladiator.race == "Orc"
        assert gladiator.level == 5
        assert gladiator.experience == 250
        assert gladiator.gold == 500
        assert gladiator.wins == 10
        assert gladiator.losses == 2
        assert gladiator.vitality == 40
        assert gladiator.max_health == 61
        assert gladiator.current_health == 50
        assert gladiator.strength == 35
        assert gladiator.dodge == 20
        assert gladiator.initiative == 18
        assert gladiator.weaponskill == 25
        assert gladiator.stamina == 30
        assert gladiator.stat_points == 3

    def test_gladiator_to_dict(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)
        gladiator.vitality = 30
        gladiator.current_health = 40
        gladiator.max_health = 46

        gladiator_dict = gladiator.to_dict()

        assert isinstance(gladiator_dict, dict)
        assert gladiator_dict["name"] == "TestGladiator"
        assert gladiator_dict["race"] == "Human"
        assert gladiator_dict["vitality"] == 30
        assert gladiator_dict["current_health"] == 40
        assert "max_health" in gladiator_dict
        assert "level" in gladiator_dict
        assert "experience" in gladiator_dict

    def test_gladiator_is_alive(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)

        gladiator.current_health = 10
        assert gladiator.is_alive() is True

        gladiator.current_health = 0
        assert gladiator.is_alive() is False

        gladiator.current_health = -5
        assert gladiator.is_alive() is False

    def test_different_races_stats(self):
        human = Gladiator("Human", "Human", use_race_stats=True)
        orc = Gladiator("Orc", "Orc", use_race_stats=True)
        goblin = Gladiator("Goblin", "Goblin", use_race_stats=True)

        assert orc.strength > human.strength
        assert orc.max_health > human.max_health
        assert goblin.dodge > human.dodge
        assert goblin.initiative > human.initiative

    def test_equipment_bonus_application(self):
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)

        original_strength = gladiator.strength
        original_vitality = gladiator.vitality
        original_stamina = gladiator.stamina
        original_dodge = gladiator.dodge
        original_initiative = gladiator.initiative
        original_weaponskill = gladiator.weaponskill

        equipment_bonuses = {
            "strength_bonus": 5,
            "vitality_bonus": 3,
            "stamina_bonus": 2,
            "dodge_bonus": 1,
            "initiative_bonus": 1,
            "weaponskill_bonus": 4,
        }

        gladiator.strength += equipment_bonuses["strength_bonus"]
        gladiator.vitality += equipment_bonuses["vitality_bonus"]
        gladiator.stamina += equipment_bonuses["stamina_bonus"]
        gladiator.dodge += equipment_bonuses["dodge_bonus"]
        gladiator.initiative += equipment_bonuses["initiative_bonus"]
        gladiator.weaponskill += equipment_bonuses["weaponskill_bonus"]

        assert gladiator.strength == original_strength + 5
        assert gladiator.vitality == original_vitality + 3
        assert gladiator.stamina == original_stamina + 2
        assert gladiator.dodge == original_dodge + 1
        assert gladiator.initiative == original_initiative + 1
        assert gladiator.weaponskill == original_weaponskill + 4
