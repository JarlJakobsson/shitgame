"""
Tests for multiplayer token isolation and random battle queue behavior.
"""

from contextlib import contextmanager
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import game_runtime as runtime
from main import app
from models_db import Base, GladiatorRow


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
        runtime.reset_runtime_state()

    def test_two_players_can_create_and_fetch_separate_gladiators(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("game_runtime.get_db", lambda: _db_context(session)):
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

    def test_unspent_creation_points_are_kept_as_stat_points(self):
        session = _make_session()
        client = TestClient(app)
        headers = {"X-Player-ID": "player-a"}
        payload = {
            "name": "Alpha",
            "race": "Human",
            "health": 10,
            "strength": 10,
            "dodge": 10,
            "initiative": 5,
            "weaponskill": 5,
            "stamina": 10,
        }  # 50 allocated, 100 should remain

        with patch("game_runtime.get_db", lambda: _db_context(session)):
            created = client.post("/gladiator", headers=headers, json=payload)
            fetched = client.get("/gladiator", headers=headers)

        assert created.status_code == 200
        assert fetched.status_code == 200
        assert created.json()["stat_points"] == 100
        assert fetched.json()["stat_points"] == 100

    def test_random_battle_matches_two_queued_players_and_notifies_both(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("game_runtime.get_db", lambda: _db_context(session)):
            client.post("/gladiator", headers=headers_a, json=_create_payload("Alpha"))
            client.post("/gladiator", headers=headers_b, json=_create_payload("Bravo"))

            queued = client.post("/pvp/random-battle/join", headers=headers_a)
            matched = client.post("/pvp/random-battle/join", headers=headers_b)

            notes_a = client.get("/notifications", headers=headers_a)
            notes_b = client.get("/notifications", headers=headers_b)
            history_a = client.get("/history", headers=headers_a)
            history_b = client.get("/history", headers=headers_b)
            detail_a = client.get(f"/history/{history_a.json()['fights'][0]['id']}", headers=headers_a)

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
        assert detail_a.status_code == 200
        assert len(detail_a.json()["battle_screen"]["battle_log"]) > 0

        wins_losses_a = updated_a.json()["wins"] + updated_a.json()["losses"]
        wins_losses_b = updated_b.json()["wins"] + updated_b.json()["losses"]
        assert wins_losses_a == 1
        assert wins_losses_b == 1

    def test_random_battle_queue_can_be_cancelled(self):
        session = _make_session()
        client = TestClient(app)
        headers = {"X-Player-ID": "player-a"}

        with patch("game_runtime.get_db", lambda: _db_context(session)):
            client.post("/gladiator", headers=headers, json=_create_payload("Alpha"))

            queued = client.post("/pvp/random-battle/join", headers=headers)
            status_queued = client.get("/notifications", headers=headers)
            cancelled = client.post("/pvp/random-battle/cancel", headers=headers)
            status_after_cancel = client.get("/notifications", headers=headers)
            cancel_again = client.post("/pvp/random-battle/cancel", headers=headers)

        assert queued.status_code == 200
        assert queued.json()["status"] == "queued"
        assert status_queued.status_code == 200
        assert status_queued.json()["queued_for_random_battle"] is True
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert status_after_cancel.status_code == 200
        assert status_after_cancel.json()["queued_for_random_battle"] is False
        assert cancel_again.status_code == 200
        assert cancel_again.json()["status"] == "not_queued"

    def test_direct_challenge_flow_lists_and_accepts(self):
        session = _make_session()
        client = TestClient(app)
        headers_a = {"X-Player-ID": "player-a"}
        headers_b = {"X-Player-ID": "player-b"}

        with patch("game_runtime.get_db", lambda: _db_context(session)):
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
            assert detail_a.json()["battle_screen"]["player"]["name"] in {"Alpha", "Bravo"}
            assert detail_a.json()["battle_screen"]["opponent"]["name"] in {"Alpha", "Bravo"}

            updated_a = client.get("/gladiator", headers=headers_a)
            updated_b = client.get("/gladiator", headers=headers_b)
            wins_losses_a = updated_a.json()["wins"] + updated_a.json()["losses"]
            wins_losses_b = updated_b.json()["wins"] + updated_b.json()["losses"]
            assert wins_losses_a == 1
            assert wins_losses_b == 1

    def test_recovery_tick_heals_and_combat_start_keeps_current_hp(self):
        session = _make_session()
        client = TestClient(app)
        headers = {"X-Player-ID": "player-a"}
        base_time = 1_700_000_000

        with patch("game_runtime.get_db", lambda: _db_context(session)), patch("game_runtime.time.time", return_value=base_time), patch("routers.gladiator.time.time", return_value=base_time):
            created = client.post("/gladiator", headers=headers, json=_create_payload("Alpha"))
            assert created.status_code == 200
            max_health = created.json()["max_health"]

            row = session.query(GladiatorRow).filter(GladiatorRow.player_token == "player-a").first()
            row.current_health = 5
            row.last_recovery_tick = runtime._get_current_recovery_tick(base_time)
            session.commit()

            started = client.post("/combat/start", headers=headers, json={"enemy_name": "Slime"})
            assert started.status_code == 200
            assert started.json()["player"]["current_health"] == 5

        with patch("game_runtime.get_db", lambda: _db_context(session)), patch("game_runtime.time.time", return_value=base_time + 61), patch("routers.gladiator.time.time", return_value=base_time + 61):
            recovery = client.get("/recovery/status", headers=headers)
            assert recovery.status_code == 200
            updated = client.get("/gladiator", headers=headers)
            assert updated.status_code == 200

        heal_amount = max(1, int(max_health * runtime.RECOVERY_HEAL_PERCENT))
        assert updated.json()["current_health"] == min(max_health, 5 + heal_amount)

    def test_exhausted_player_gets_defeat_and_no_rewards(self):
        session = _make_session()
        client = TestClient(app)
        headers = {"X-Player-ID": "player-a"}
        payload = {
            "name": "Alpha",
            "race": "Human",
            "health": 30,
            "strength": 20,
            "dodge": 20,
            "initiative": 20,
            "weaponskill": 20,
            "stamina": 1,
        }

        with patch("game_runtime.get_db", lambda: _db_context(session)):
            created = client.post("/gladiator", headers=headers, json=payload)
            assert created.status_code == 200
            start = client.post("/combat/start", headers=headers, json={"enemy_name": "Slime"})
            assert start.status_code == 200

            winner = None
            while winner is None:
                round_result = client.post("/combat/round", headers=headers)
                assert round_result.status_code == 200
                winner = round_result.json()["winner"]

            finished = client.post("/combat/finish", headers=headers)
            assert finished.status_code == 200
            assert finished.json()["result"] == "defeat"
            assert finished.json()["reward_gold"] == 0
            assert finished.json()["reward_exp"] == 0
