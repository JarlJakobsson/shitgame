from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from models_db import ChallengeRow, FightHistoryRow, GladiatorRow
from schemas import ChallengeCreate
import game_runtime as rt


router = APIRouter()


@router.get("/pvp/gladiators")
def list_pvp_gladiators(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        rows = (
            db.query(GladiatorRow)
            .filter(GladiatorRow.player_token != player_token)
            .order_by(GladiatorRow.level.desc(), GladiatorRow.name.asc())
            .all()
        )
        return [
            {
                "player_token": row.player_token,
                "name": row.name,
                "race": row.race,
                "level": row.level,
                "wins": row.wins,
                "losses": row.losses,
            }
            for row in rows
        ]


@router.post("/pvp/challenges")
def create_pvp_challenge(payload: ChallengeCreate, request: Request):
    player_token = rt._resolve_player_token(request)
    target_token = payload.target_player_token.strip()
    if not target_token:
        raise HTTPException(status_code=400, detail="Target gladiator is required")
    if target_token == player_token:
        raise HTTPException(status_code=400, detail="You cannot challenge yourself")

    with rt.get_db() as db:
        challenger_row = rt._get_gladiator_row(db, player_token)
        if challenger_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")

        challenged_row = rt._get_gladiator_row(db, target_token)
        if challenged_row is None:
            raise HTTPException(status_code=404, detail="Target gladiator not found")
        challenger_name = challenger_row.name
        challenger_level = challenger_row.level
        challenger_race = challenger_row.race
        challenged_name = challenged_row.name

        existing = db.query(ChallengeRow).filter(
            ChallengeRow.challenger_player_token == player_token,
            ChallengeRow.challenged_player_token == target_token,
            ChallengeRow.status == "pending",
        ).first()
        if existing:
            return {"message": "Challenge already sent."}

        challenge = ChallengeRow(
            challenger_player_token=player_token,
            challenged_player_token=target_token,
            status="pending",
        )
        db.add(challenge)
        db.commit()

    with rt.random_battle_lock:
        rt._queue_notification(
            target_token,
            f"New challenge from {challenger_name} (Level {challenger_level}, {challenger_race}).",
            notification_type="challenge",
        )

    return {"message": f"Challenge sent to {challenged_name}."}


@router.get("/pvp/challenges")
def list_incoming_challenges(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        challenge_rows = (
            db.query(ChallengeRow)
            .filter(
                ChallengeRow.challenged_player_token == player_token,
                ChallengeRow.status == "pending",
            )
            .order_by(ChallengeRow.created_at.asc(), ChallengeRow.id.asc())
            .all()
        )
        results = []
        for challenge in challenge_rows:
            challenger_row = rt._get_gladiator_row(db, challenge.challenger_player_token)
            if challenger_row is None:
                continue
            created_at = challenge.created_at.isoformat() if challenge.created_at else None
            results.append(
                {
                    "id": challenge.id,
                    "challenger_player_token": challenge.challenger_player_token,
                    "challenger_name": challenger_row.name,
                    "challenger_race": challenger_row.race,
                    "challenger_level": challenger_row.level,
                    "created_at": created_at,
                }
            )
        return {"challenges": results}


@router.post("/pvp/challenges/{challenge_id}/accept")
def accept_pvp_challenge(challenge_id: int, request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        challenge = db.query(ChallengeRow).filter(
            ChallengeRow.id == challenge_id,
            ChallengeRow.challenged_player_token == player_token,
            ChallengeRow.status == "pending",
        ).first()
        if challenge is None:
            raise HTTPException(status_code=404, detail="Challenge not found")

        challenger_row = rt._get_gladiator_row(db, challenge.challenger_player_token)
        challenged_row = rt._get_gladiator_row(db, player_token)
        if challenger_row is None or challenged_row is None:
            challenge.status = "cancelled"
            challenge.resolved_at = datetime.now(timezone.utc)
            db.commit()
            raise HTTPException(status_code=400, detail="Challenge can no longer be accepted")

        battle_result = rt._run_pvp_battle(db, challenger_row, challenged_row)
        rt._record_fight_history(
            db,
            player_token=challenger_row.player_token,
            mode="challenge_pvp",
            opponent_name=challenged_row.name,
            opponent_race=challenged_row.race,
            opponent_level=challenged_row.level,
            result=battle_result["challenger_result"],
            battle_log=battle_result["battle_log"],
            battle_snapshot=battle_result["challenger_battle_screen"],
        )
        rt._record_fight_history(
            db,
            player_token=challenged_row.player_token,
            mode="challenge_pvp",
            opponent_name=challenger_row.name,
            opponent_race=challenger_row.race,
            opponent_level=challenger_row.level,
            result=battle_result["opponent_result"],
            battle_log=battle_result["battle_log"],
            battle_snapshot=battle_result["opponent_battle_screen"],
        )
        challenge.status = "accepted"
        challenge.resolved_at = datetime.now(timezone.utc)
        challenger_token = challenge.challenger_player_token
        db.commit()

    with rt.random_battle_lock:
        rt._queue_notification(
            challenger_token,
            f"Challenge battle complete: {battle_result['winner_name']} defeated {battle_result['loser_name']} in {battle_result['rounds']} rounds.",
            notification_type="challenge",
        )
        rt._queue_notification(
            player_token,
            f"Challenge battle complete: {battle_result['winner_name']} defeated {battle_result['loser_name']} in {battle_result['rounds']} rounds.",
            notification_type="challenge",
        )

    return {"message": "Challenge accepted.", "battle_result": battle_result}


@router.post("/pvp/random-battle/join")
def join_random_battle(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        challenger_row = rt._get_gladiator_row(db, player_token)
        if challenger_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")

    with rt.random_battle_lock:
        if player_token in rt.random_battle_queue:
            return {"status": "queued", "message": "Already waiting in random battle queue."}

        opponent_token = None
        while rt.random_battle_queue and opponent_token is None:
            queued_token = rt.random_battle_queue.popleft()
            if queued_token != player_token:
                opponent_token = queued_token

        if opponent_token is None:
            rt.random_battle_queue.append(player_token)
            return {"status": "queued", "message": "Joined queue. Waiting for opponent."}

    with rt.get_db() as db:
        challenger_row = rt._get_gladiator_row(db, player_token)
        opponent_row = rt._get_gladiator_row(db, opponent_token)
        if challenger_row is None or opponent_row is None:
            with rt.random_battle_lock:
                if player_token not in rt.random_battle_queue:
                    rt.random_battle_queue.append(player_token)
            return {"status": "queued", "message": "Joined queue. Waiting for opponent."}

        result = rt._run_pvp_battle(db, challenger_row, opponent_row)
        rt._record_fight_history(
            db,
            player_token=challenger_row.player_token,
            mode="random_pvp",
            opponent_name=opponent_row.name,
            opponent_race=opponent_row.race,
            opponent_level=opponent_row.level,
            result=result["challenger_result"],
            battle_log=result["battle_log"],
            battle_snapshot=result["challenger_battle_screen"],
        )
        rt._record_fight_history(
            db,
            player_token=opponent_row.player_token,
            mode="random_pvp",
            opponent_name=challenger_row.name,
            opponent_race=challenger_row.race,
            opponent_level=challenger_row.level,
            result=result["opponent_result"],
            battle_log=result["battle_log"],
            battle_snapshot=result["opponent_battle_screen"],
        )
        db.commit()

    with rt.random_battle_lock:
        rt._queue_notification(
            player_token,
            f"Random battle complete: {result['winner_name']} defeated {result['loser_name']} in {result['rounds']} rounds.",
        )
        rt._queue_notification(
            opponent_token,
            f"Random battle complete: {result['winner_name']} defeated {result['loser_name']} in {result['rounds']} rounds.",
        )

    return {
        "status": "matched",
        "message": "Random battle completed.",
        "battle_result": result,
    }


@router.post("/pvp/random-battle/cancel")
def cancel_random_battle(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.random_battle_lock:
        try:
            rt.random_battle_queue.remove(player_token)
            removed = True
        except ValueError:
            removed = False

    if removed:
        return {"status": "cancelled", "message": "Left random battle queue."}
    return {"status": "not_queued", "message": "You are not currently in random battle queue."}


@router.get("/notifications")
def get_notifications(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.random_battle_lock:
        notifications = list(rt.random_battle_notifications.get(player_token, []))
        rt.random_battle_notifications[player_token] = []
        is_queued = player_token in rt.random_battle_queue
    return {"notifications": notifications, "queued_for_random_battle": is_queued}


@router.get("/history")
def get_fight_history(request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        rows = (
            db.query(FightHistoryRow)
            .filter(FightHistoryRow.player_token == player_token)
            .order_by(FightHistoryRow.id.desc())
            .all()
        )
        return {
            "fights": [
                {
                    "id": row.id,
                    "mode": row.mode,
                    "opponent_name": row.opponent_name,
                    "opponent_race": row.opponent_race,
                    "opponent_level": row.opponent_level,
                    "result": row.result,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]
        }


@router.get("/history/{fight_id}")
def get_fight_history_detail(fight_id: int, request: Request):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        row = (
            db.query(FightHistoryRow)
            .filter(
                FightHistoryRow.id == fight_id,
                FightHistoryRow.player_token == player_token,
            )
            .first()
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Fight not found")
        battle_screen = row.battle_snapshot or {
            "player": {
                "name": "You",
                "race": "Unknown",
                "level": 0,
                "current_health": 0,
                "max_health": 0,
            },
            "opponent": {
                "name": row.opponent_name,
                "race": row.opponent_race,
                "level": row.opponent_level,
                "current_health": 0,
                "max_health": 0,
            },
            "result": row.result,
            "reward_gold": 0,
            "reward_exp": 0,
            "rounds": 0,
            "battle_log": row.battle_log or [],
        }
        return {
            "id": row.id,
            "mode": row.mode,
            "opponent_name": row.opponent_name,
            "opponent_race": row.opponent_race,
            "opponent_level": row.opponent_level,
            "result": row.result,
            "battle_log": row.battle_log or [],
            "battle_screen": battle_screen,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
