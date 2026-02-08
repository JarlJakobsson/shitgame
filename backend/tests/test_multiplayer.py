"""
Tests for multiplayer token isolation and random battle queue behavior.
"""

from contextlib import contextmanager
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from main import app
from models_db import Base


@contextmanager
def _db_context(session):
    yield session


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def _create_payload(name: str):
    return {
        "name": name,
        "race": "Human",
        "health": 30,
        "strength": 20,
        "dodge": 20,
        "initiative": 20,
        "weaponskill": 20,
        "stamina": 20,
    }


class TestMultiplayer:
    def setup_method(self):
        main.random_battle_queue.clear()
        main.random_battle_notifications.clear()
        main.current_combats.clear()
        main.current_combat = None

    def test_two_players_can_create_and_fetch_separate_gladiators(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("main.get_db", lambda: _db_context(session)):
            response_a = client.post("/gladiator", headers=headers_a, json=_create_payload("Alpha"))
            response_b = client.post("/gladiator", headers=headers_b, json=_create_payload("Bravo"))
            get_a = client.get("/gladiator", headers=headers_a)
            get_b = client.get("/gladiator", headers=headers_b)

        assert response_a.status_code == 200
        assert response_b.status_code == 200
        assert get_a.status_code == 200
        assert get_b.status_code == 200
        assert get_a.json()["name"] == "Alpha"
        assert get_b.json()["name"] == "Bravo"

    def test_random_battle_matches_two_queued_players_and_notifies_both(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("main.get_db", lambda: _db_context(session)):
            client.post("/gladiator", headers=headers_a, json=_create_payload("Alpha"))
            client.post("/gladiator", headers=headers_b, json=_create_payload("Bravo"))

            queued = client.post("/pvp/random-battle/join", headers=headers_a)
            matched = client.post("/pvp/random-battle/join", headers=headers_b)

            notes_a = client.get("/notifications", headers=headers_a)
            notes_b = client.get("/notifications", headers=headers_b)
            history_a = client.get("/history", headers=headers_a)
            history_b = client.get("/history", headers=headers_b)

            updated_a = client.get("/gladiator", headers=headers_a)
            updated_b = client.get("/gladiator", headers=headers_b)

        assert queued.status_code == 200
        assert queued.json()["status"] == "queued"
        assert matched.status_code == 200
        assert matched.json()["status"] == "matched"

        assert notes_a.status_code == 200
        assert notes_b.status_code == 200
        assert len(notes_a.json()["notifications"]) == 1
        assert len(notes_b.json()["notifications"]) == 1
        assert "Random battle complete" in notes_a.json()["notifications"][0]["message"]
        assert "Random battle complete" in notes_b.json()["notifications"][0]["message"]
        assert len(history_a.json()["fights"]) == 1
        assert len(history_b.json()["fights"]) == 1
        assert history_a.json()["fights"][0]["mode"] == "random_pvp"
        assert history_b.json()["fights"][0]["mode"] == "random_pvp"

        wins_losses_a = updated_a.json()["wins"] + updated_a.json()["losses"]
        wins_losses_b = updated_b.json()["wins"] + updated_b.json()["losses"]
        assert wins_losses_a == 1
        assert wins_losses_b == 1

    def test_direct_challenge_flow_lists_and_accepts(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("main.get_db", lambda: _db_context(session)):
            client.post("/gladiator", headers=headers_a, json=_create_payload("Alpha"))
            client.post("/gladiator", headers=headers_b, json=_create_payload("Bravo"))

            roster = client.get("/pvp/gladiators", headers=headers_a)
            assert roster.status_code == 200
            assert len(roster.json()) == 1
            assert roster.json()[0]["name"] == "Bravo"

            send = client.post(
                "/pvp/challenges",
                headers=headers_a,
                json={"target_player_token": "player-b"},
            )
            assert send.status_code == 200

            incoming = client.get("/pvp/challenges", headers=headers_b)
            assert incoming.status_code == 200
            assert len(incoming.json()["challenges"]) == 1
            challenge_id = incoming.json()["challenges"][0]["id"]
            assert incoming.json()["challenges"][0]["challenger_name"] == "Alpha"
            assert incoming.json()["challenges"][0]["challenger_race"] == "Human"
            assert incoming.json()["challenges"][0]["challenger_level"] == 1

            accepted = client.post(f"/pvp/challenges/{challenge_id}/accept", headers=headers_b)
            assert accepted.status_code == 200
            assert "battle_result" in accepted.json()

            notes_a = client.get("/notifications", headers=headers_a)
            notes_b = client.get("/notifications", headers=headers_b)
            history_a = client.get("/history", headers=headers_a)
            history_b = client.get("/history", headers=headers_b)
            fight_id_a = history_a.json()["fights"][0]["id"]
            detail_a = client.get(f"/history/{fight_id_a}", headers=headers_a)
            assert any("Challenge battle complete" in n["message"] for n in notes_a.json()["notifications"])
            assert any("Challenge battle complete" in n["message"] for n in notes_b.json()["notifications"])
            assert history_a.json()["fights"][0]["mode"] == "challenge_pvp"
            assert history_b.json()["fights"][0]["mode"] == "challenge_pvp"
            assert len(detail_a.json()["battle_log"]) > 0

            updated_a = client.get("/gladiator", headers=headers_a)
            updated_b = client.get("/gladiator", headers=headers_b)
            wins_losses_a = updated_a.json()["wins"] + updated_a.json()["losses"]
            wins_losses_b = updated_b.json()["wins"] + updated_b.json()["losses"]
            assert wins_losses_a == 1
            assert wins_losses_b == 1
