"""
Integration-style tests for API endpoints.
"""

from contextlib import contextmanager
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from gladiator import Gladiator
from main import app
from models import Equipment


client = TestClient(app)


def _mock_get_db(mock_db):
    @contextmanager
    def _ctx():
        yield mock_db

    return _ctx


class TestGladiatorAPI:
    def test_create_gladiator_success(self):
        mock_db = Mock()
        mock_db.query.return_value.first.return_value = None

        payload = {
            "name": "TestGladiator",
            "race": "Human",
            "health": 30,
            "strength": 25,
            "dodge": 25,
            "initiative": 25,
            "weaponskill": 25,
            "stamina": 20,
        }

        with patch("main.get_db", _mock_get_db(mock_db)), patch("main._save_gladiator"):
            response = client.post("/gladiator", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestGladiator"
        assert data["race"] == "Human"
        assert data["level"] == 1

    def test_create_gladiator_invalid_race(self):
        payload = {
            "name": "TestGladiator",
            "race": "InvalidRace",
            "health": 30,
            "strength": 25,
            "dodge": 25,
            "initiative": 25,
            "weaponskill": 25,
            "stamina": 20,
        }

        response = client.post("/gladiator", json=payload)
        assert response.status_code == 400
        assert "Invalid race" in response.json()["detail"]

    def test_get_gladiator_not_found(self):
        mock_db = Mock()
        with patch("main.get_db", _mock_get_db(mock_db)), patch("main._load_gladiator", return_value=None):
            response = client.get("/gladiator")

        assert response.status_code == 404
        assert "No gladiator created" in response.json()["detail"]

    def test_get_gladiator_success(self):
        mock_db = Mock()
        mock_db.query.return_value.first.return_value = Mock(id=1)
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)
        gladiator.max_health = gladiator.current_health = 10

        with (
            patch("main.get_db", _mock_get_db(mock_db)),
            patch("main._load_gladiator", return_value=gladiator),
            patch("main.get_equipped_items", return_value={}),
            patch("main.get_gladiator_equipment", return_value=[]),
        ):
            response = client.get("/gladiator")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestGladiator"
        assert data["race"] == "Human"

    def test_allocate_stat_points_not_enough(self):
        mock_db = Mock()
        gladiator = Gladiator("TestGladiator", "Human", use_race_stats=False)
        gladiator.stat_points = 1

        allocation = {
            "health": 2,
            "strength": 0,
            "dodge": 0,
            "initiative": 0,
            "weaponskill": 0,
            "stamina": 0,
        }

        with patch("main.get_db", _mock_get_db(mock_db)), patch("main._load_gladiator", return_value=gladiator):
            response = client.post("/gladiator/allocate", json=allocation)

        assert response.status_code == 400
        assert "Not enough stat points" in response.json()["detail"]


class TestEquipmentAPI:
    def test_get_all_equipment(self):
        mock_db = Mock()
        equipment = [
            Equipment(
                id=1,
                name="Iron Helmet",
                slot="head",
                item_type="armor",
                rarity="common",
                level_requirement=1,
                strength_bonus=2,
                vitality_bonus=1,
                stamina_bonus=0,
                dodge_bonus=0,
                initiative_bonus=0,
                weaponskill_bonus=0,
                value=25,
                description="A sturdy iron helmet.",
            )
        ]

        with patch("main.get_db", _mock_get_db(mock_db)), patch("main.get_all_equipment", return_value=equipment):
            response = client.get("/equipment")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Iron Helmet"

    def test_equip_item_no_gladiator(self):
        mock_db = Mock()
        mock_db.query.return_value.first.return_value = None

        with patch("main.get_db", _mock_get_db(mock_db)):
            response = client.post("/equipment/equip", json={"equipment_id": 1, "slot": "head"})

        assert response.status_code == 404
        assert "No gladiator created" in response.json()["detail"]


class TestCombatAPI:
    def test_execute_combat_round_no_active_combat(self):
        with patch("main.current_combat", None):
            response = client.post("/combat/round")

        assert response.status_code == 400
        assert "No active combat" in response.json()["detail"]

    def test_finish_combat_no_active_combat(self):
        with patch("main.current_combat", None):
            response = client.post("/combat/finish")

        assert response.status_code == 400
        assert "No active combat" in response.json()["detail"]


class TestUtilityAPI:
    def test_get_races(self):
        response = client.get("/races")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Human" in data
        assert "Orc" in data

    def test_health_check(self):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
