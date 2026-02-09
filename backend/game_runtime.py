from __future__ import annotations

from collections import defaultdict, deque
from math import floor
from threading import Lock
import time

from sqlalchemy import inspect, or_, text

from combat import Combat
from database import engine, get_db
from equipment import calculate_equipment_bonuses, get_equipped_items, initialize_equipment
from gladiator import Gladiator
from models_db import (
    Base,
    FightHistoryRow,
    GladiatorRow,
)


DEFAULT_PLAYER_TOKEN = "single-player"
PLAYER_ID_HEADER = "X-Player-ID"
RECOVERY_INTERVAL_SECONDS = 60
RECOVERY_HEAL_PERCENT = 0.33


# Combat is tracked per player token.
current_combat: Combat | None = None
current_combats: dict[str, Combat] = {}

# PVP random queue + notifications are in-memory for a single app instance.
random_battle_queue = deque()
random_battle_notifications = defaultdict(list)
random_battle_lock = Lock()


def reset_runtime_state():
    """Reset in-memory runtime state (useful for tests)."""
    global current_combat
    current_combat = None
    current_combats.clear()
    random_battle_queue.clear()
    random_battle_notifications.clear()


def _init_db():
    attempts = 0
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_equipped_items_column()
            _ensure_equipment_columns()
            _ensure_player_token_column()
            _ensure_fight_history_columns()
            _ensure_recovery_columns()
            with get_db() as db:
                initialize_equipment(db)
            return
        except Exception:
            attempts += 1
            if attempts >= 10:
                raise
            time.sleep(1)


def _ensure_equipped_items_column():
    inspector = inspect(engine)
    if "gladiators" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("gladiators")}
    if "equipped_items" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE gladiators ADD COLUMN equipped_items JSON"))


def _ensure_equipment_columns():
    inspector = inspect(engine)
    if "equipment" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("equipment")}
    if "weaponskill_requirement" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE equipment "
                    "ADD COLUMN weaponskill_requirement INTEGER NOT NULL DEFAULT 0"
                )
            )
    if "weapon_subtype" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE equipment "
                    "ADD COLUMN weapon_subtype VARCHAR(120)"
                )
            )
    if "min_damage" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE equipment "
                    "ADD COLUMN min_damage INTEGER NOT NULL DEFAULT 0"
                )
            )
    if "max_damage" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE equipment "
                    "ADD COLUMN max_damage INTEGER NOT NULL DEFAULT 0"
                )
            )


def _ensure_player_token_column():
    inspector = inspect(engine)
    if "gladiators" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("gladiators")}
    if "player_token" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE gladiators ADD COLUMN player_token VARCHAR(120)"))
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE gladiators "
                "SET player_token = :default_token "
                "WHERE player_token IS NULL OR player_token = ''"
            ),
            {"default_token": DEFAULT_PLAYER_TOKEN},
        )


def _ensure_fight_history_columns():
    inspector = inspect(engine)
    if "fight_history" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("fight_history")}
    if "battle_snapshot" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE fight_history ADD COLUMN battle_snapshot JSON"))


def _ensure_recovery_columns():
    inspector = inspect(engine)
    if "gladiators" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("gladiators")}
    if "last_recovery_tick" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE gladiators ADD COLUMN last_recovery_tick INTEGER"))
    current_tick = int(time.time()) // RECOVERY_INTERVAL_SECONDS
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE gladiators "
                "SET last_recovery_tick = :current_tick "
                "WHERE last_recovery_tick IS NULL"
            ),
            {"current_tick": current_tick},
        )


def _resolve_player_token(request) -> str:
    if request is None:
        return DEFAULT_PLAYER_TOKEN
    header_value = request.headers.get(PLAYER_ID_HEADER, "").strip()
    return header_value or DEFAULT_PLAYER_TOKEN


def _get_current_recovery_tick(now_epoch_seconds: int | None = None) -> int:
    if now_epoch_seconds is None:
        now_epoch_seconds = int(time.time())
    return now_epoch_seconds // RECOVERY_INTERVAL_SECONDS


def _seconds_until_next_recovery(now_epoch_seconds: int | None = None) -> int:
    if now_epoch_seconds is None:
        now_epoch_seconds = int(time.time())
    elapsed = now_epoch_seconds % RECOVERY_INTERVAL_SECONDS
    if elapsed == 0:
        return RECOVERY_INTERVAL_SECONDS
    return RECOVERY_INTERVAL_SECONDS - elapsed


def _recovery_heal_amount(max_health: int) -> int:
    return max(1, int(floor(max_health * RECOVERY_HEAL_PERCENT)))


def _apply_recovery_to_row(row: GladiatorRow, target_tick: int) -> bool:
    if row.last_recovery_tick is None:
        row.last_recovery_tick = target_tick
        return True

    if row.last_recovery_tick >= target_tick:
        return False

    ticks_elapsed = target_tick - row.last_recovery_tick
    if row.current_health < row.max_health:
        heal_per_tick = _recovery_heal_amount(row.max_health)
        row.current_health = min(
            row.max_health,
            row.current_health + (heal_per_tick * ticks_elapsed),
        )
    row.last_recovery_tick = target_tick
    return True


def _get_gladiator_row(db, player_token: str) -> GladiatorRow | None:
    row = db.query(GladiatorRow).filter(GladiatorRow.player_token == player_token).first()
    if row is not None:
        return row
    if player_token != DEFAULT_PLAYER_TOKEN:
        return None
    legacy_row = db.query(GladiatorRow).filter(
        or_(GladiatorRow.player_token.is_(None), GladiatorRow.player_token == "")
    ).first()
    if legacy_row is None:
        return None
    legacy_row.player_token = DEFAULT_PLAYER_TOKEN
    db.commit()
    db.refresh(legacy_row)
    return legacy_row


def _gladiator_from_row(db, row: GladiatorRow, apply_equipment_bonuses: bool) -> Gladiator:
    gladiator = Gladiator(row.name, row.race, use_race_stats=True)
    gladiator.apply_persisted_stats({
        "name": row.name,
        "race": row.race,
        "level": row.level,
        "experience": row.experience,
        "gold": row.gold,
        "wins": row.wins,
        "losses": row.losses,
        "vitality": row.vitality,
        "max_health": row.max_health,
        "current_health": row.current_health,
        "strength": row.strength,
        "dodge": row.dodge,
        "initiative": row.initiative,
        "weaponskill": row.weaponskill,
        "stamina": row.stamina,
        "stat_points": row.stat_points,
    })
    if apply_equipment_bonuses:
        bonuses = calculate_equipment_bonuses(db, row.id)
        gladiator.strength += bonuses["strength_bonus"]
        gladiator.vitality += bonuses["vitality_bonus"]
        gladiator.stamina += bonuses["stamina_bonus"]
        gladiator.dodge += bonuses["dodge_bonus"]
        gladiator.initiative += bonuses["initiative_bonus"]
        gladiator.weaponskill += bonuses["weaponskill_bonus"]
        if bonuses["vitality_bonus"] > 0:
            gladiator.max_health = 1 + int(floor(gladiator.vitality * 1.5))

    # Attach equipped weapon damage profile for combat calculations.
    equipped_items = get_equipped_items(db, row.id)
    weapon = equipped_items.get("weapon")
    if weapon:
        weapon_min = max(0, int(getattr(weapon, "min_damage", 0) or 0))
        weapon_max = max(weapon_min, int(getattr(weapon, "max_damage", 0) or 0))
        gladiator.weapon_min_damage = weapon_min
        gladiator.weapon_max_damage = weapon_max
    else:
        gladiator.weapon_min_damage = 0
        gladiator.weapon_max_damage = 0

    return gladiator


def _load_gladiator(db, player_token: str = DEFAULT_PLAYER_TOKEN, apply_equipment_bonuses: bool = False) -> Gladiator | None:
    row = _get_gladiator_row(db, player_token)
    if not row:
        return None
    recovery_tick = _get_current_recovery_tick()
    if _apply_recovery_to_row(row, recovery_tick):
        db.commit()
        db.refresh(row)
    return _gladiator_from_row(db, row, apply_equipment_bonuses)


def _get_current_combat(player_token: str) -> Combat | None:
    if player_token == DEFAULT_PLAYER_TOKEN:
        return current_combat
    return current_combats.get(player_token)


def _set_current_combat(player_token: str, combat: Combat | None):
    global current_combat
    if combat is None:
        current_combats.pop(player_token, None)
        if player_token == DEFAULT_PLAYER_TOKEN:
            current_combat = None
        return
    current_combats[player_token] = combat
    if player_token == DEFAULT_PLAYER_TOKEN:
        current_combat = combat


def _save_gladiator(
    db,
    gladiator: Gladiator,
    player_token: str = DEFAULT_PLAYER_TOKEN,
    row: GladiatorRow | None = None,
):
    current_tick = _get_current_recovery_tick()
    if row is None:
        row = _get_gladiator_row(db, player_token)
    if not row:
        row = GladiatorRow(player_token=player_token)
        row.last_recovery_tick = current_tick
        db.add(row)
    else:
        row.player_token = player_token
        if row.last_recovery_tick is None:
            row.last_recovery_tick = current_tick

    row.name = gladiator.name
    row.race = gladiator.race
    row.level = gladiator.level
    row.experience = gladiator.experience
    row.gold = gladiator.gold
    row.wins = gladiator.wins
    row.losses = gladiator.losses
    row.vitality = gladiator.vitality
    row.max_health = gladiator.max_health
    row.current_health = gladiator.current_health
    row.strength = gladiator.strength
    row.dodge = gladiator.dodge
    row.initiative = gladiator.initiative
    row.weaponskill = gladiator.weaponskill
    row.stamina = gladiator.stamina
    row.stat_points = gladiator.stat_points

    db.commit()
    db.refresh(row)
    return row


def _queue_notification(
    player_token: str,
    message: str,
    notification_type: str = "random_battle",
):
    random_battle_notifications[player_token].append(
        {"type": notification_type, "message": message}
    )


def _append_round_to_battle_log(combat: Combat, round_info: dict):
    combat.battle_log.append(f"Round {round_info['round']}")
    combat.battle_log.extend(round_info["actions"])


def _simulate_full_combat(combat: Combat):
    winner = None
    while winner is None:
        round_info = combat.execute_round()
        _append_round_to_battle_log(combat, round_info)
        winner = round_info["winner"]
    return winner


def _build_battle_screen(
    player,
    opponent,
    result: str,
    battle_log: list[str] | None,
    reward_gold: int = 0,
    reward_exp: int = 0,
    rounds: int = 0,
):
    return {
        "player": {
            "name": player.name,
            "race": getattr(player, "race", "Unknown") or "Unknown",
            "level": int(getattr(player, "level", 0) or 0),
            "current_health": int(player.current_health),
            "max_health": int(player.max_health),
        },
        "opponent": {
            "name": opponent.name,
            "race": getattr(opponent, "race", "Unknown") or "Unknown",
            "level": int(getattr(opponent, "level", 0) or 0),
            "current_health": int(opponent.current_health),
            "max_health": int(opponent.max_health),
        },
        "result": result,
        "reward_gold": int(reward_gold),
        "reward_exp": int(reward_exp),
        "rounds": int(rounds),
        "battle_log": list(battle_log or []),
    }


def _record_fight_history(
    db,
    player_token: str,
    mode: str,
    opponent_name: str,
    opponent_race: str,
    opponent_level: int,
    result: str,
    battle_log: list[str] | None,
    battle_snapshot: dict | None = None,
):
    row = FightHistoryRow(
        player_token=player_token,
        mode=mode,
        opponent_name=opponent_name,
        opponent_race=opponent_race or "Unknown",
        opponent_level=max(0, int(opponent_level)),
        result=result,
        battle_log=list(battle_log or []),
        battle_snapshot=battle_snapshot,
    )
    db.add(row)
    return row


def _run_pvp_battle(db, challenger_row: GladiatorRow, opponent_row: GladiatorRow):
    recovery_tick = _get_current_recovery_tick()
    challenger_recovered = _apply_recovery_to_row(challenger_row, recovery_tick)
    opponent_recovered = _apply_recovery_to_row(opponent_row, recovery_tick)
    if challenger_recovered or opponent_recovered:
        db.commit()
        db.refresh(challenger_row)
        db.refresh(opponent_row)

    challenger = _gladiator_from_row(db, challenger_row, apply_equipment_bonuses=True)
    opponent = _gladiator_from_row(db, opponent_row, apply_equipment_bonuses=True)

    combat = Combat(challenger, opponent)
    winner = _simulate_full_combat(combat)

    if winner == "player":
        challenger.wins += 1
        opponent.losses += 1
        winner_name = challenger.name
        loser_name = opponent.name
        challenger_result = "victory"
        opponent_result = "defeat"
    else:
        challenger.losses += 1
        opponent.wins += 1
        winner_name = opponent.name
        loser_name = challenger.name
        challenger_result = "defeat"
        opponent_result = "victory"

    _save_gladiator(db, challenger, challenger_row.player_token, row=challenger_row)
    _save_gladiator(db, opponent, opponent_row.player_token, row=opponent_row)

    challenger_battle_screen = _build_battle_screen(
        player=challenger,
        opponent=opponent,
        result=challenger_result,
        battle_log=combat.battle_log,
        reward_gold=0,
        reward_exp=0,
        rounds=combat.round,
    )
    opponent_battle_screen = _build_battle_screen(
        player=opponent,
        opponent=challenger,
        result=opponent_result,
        battle_log=combat.battle_log,
        reward_gold=0,
        reward_exp=0,
        rounds=combat.round,
    )

    return {
        "winner_name": winner_name,
        "loser_name": loser_name,
        "rounds": combat.round,
        "challenger_survived": challenger.is_alive(),
        "opponent_survived": opponent.is_alive(),
        "challenger_result": challenger_result,
        "opponent_result": opponent_result,
        "battle_log": list(combat.battle_log),
        "challenger_battle_screen": challenger_battle_screen,
        "opponent_battle_screen": opponent_battle_screen,
    }
