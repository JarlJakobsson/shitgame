from math import floor
import time

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_

from equipment import get_equipped_items, get_gladiator_equipment
from gladiator import Gladiator
from leveling import apply_experience
from models_db import ChallengeRow, FightHistoryRow, GladiatorEquipmentRow
from races import RACES
from schemas import GladiatorCreate, GladiatorResponse, StatAllocation
import game_runtime as rt


router = APIRouter()


def _build_racial_bonus_map(race_name: str) -> dict[str, float]:
    race_data = RACES.get(race_name, {})
    racial_bonus_map: dict[str, float] = {}
    for entry in race_data.get("racial_bonus", []):
        stat_key = str(entry.get("stat", "")).strip().lower()
        if stat_key == "agility":
            stat_key = "dodge"
        raw_value = str(entry.get("value", "")).replace("%", "").strip()
        try:
            percent = float(raw_value) / 100.0
        except ValueError:
            continue
        racial_bonus_map[stat_key] = percent
    return racial_bonus_map


def _apply_racial_modifier(base_value: int, stat_key: str, racial_bonus_map: dict[str, float]) -> int:
    percent = racial_bonus_map.get(stat_key, 0.0)
    adjusted = base_value + (base_value * percent)
    return max(0, int(floor(adjusted)))


@router.post("/gladiator")
def create_gladiator(gladiator_data: GladiatorCreate, request: Request):
    """Create a new gladiator."""
    player_token = rt._resolve_player_token(request)

    if gladiator_data.race not in RACES:
        raise HTTPException(status_code=400, detail="Invalid race")

    if not gladiator_data.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    stats = {
        "health": gladiator_data.health,
        "strength": gladiator_data.strength,
        "dodge": gladiator_data.dodge,
        "initiative": gladiator_data.initiative,
        "weaponskill": gladiator_data.weaponskill,
        "stamina": gladiator_data.stamina,
    }

    total_points = sum(stats.values())
    if total_points > 150:
        raise HTTPException(status_code=400, detail="Stat points exceed 150")

    if any(value < 0 for value in stats.values()):
        raise HTTPException(status_code=400, detail="Stat points cannot be negative")

    # Racial modifiers affect only point allocation, not flat bonuses from other systems.
    racial_bonus_map = _build_racial_bonus_map(gladiator_data.race)
    stats_with_bonus = {
        key: _apply_racial_modifier(value, key, racial_bonus_map)
        for key, value in stats.items()
    }

    current_gladiator = Gladiator(gladiator_data.name, gladiator_data.race, use_race_stats=True)
    vitality = stats_with_bonus["health"]
    max_health = 1 + int(floor(vitality * 1.5))
    current_gladiator.vitality = vitality
    current_gladiator.max_health = max_health
    current_gladiator.current_health = max_health
    current_gladiator.strength = stats_with_bonus["strength"]
    current_gladiator.dodge = stats_with_bonus["dodge"]
    current_gladiator.initiative = stats_with_bonus["initiative"]
    current_gladiator.weaponskill = stats_with_bonus["weaponskill"]
    current_gladiator.stamina = stats_with_bonus["stamina"]
    current_gladiator.stat_points = max(0, 150 - total_points)

    with rt.get_db() as db:
        existing = rt._get_gladiator_row(db, player_token)
        if existing:
            db.query(ChallengeRow).filter(
                or_(
                    ChallengeRow.challenger_player_token == player_token,
                    ChallengeRow.challenged_player_token == player_token,
                )
            ).delete()
            db.query(FightHistoryRow).filter(
                FightHistoryRow.player_token == player_token
            ).delete()
            db.query(GladiatorEquipmentRow).filter(
                GladiatorEquipmentRow.gladiator_id == existing.id
            ).delete()
            db.delete(existing)
            db.commit()
        rt._save_gladiator(db, current_gladiator, player_token)
    return GladiatorResponse(**current_gladiator.to_dict())


@router.post("/gladiator/allocate")
def allocate_stat_points(allocation: StatAllocation, request: Request):
    """Allocate unspent stat points from leveling."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        current_gladiator = rt._load_gladiator(
            db, player_token, apply_equipment_bonuses=False
        )
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")

    points = {
        "health": allocation.health,
        "strength": allocation.strength,
        "dodge": allocation.dodge,
        "initiative": allocation.initiative,
        "weaponskill": allocation.weaponskill,
        "stamina": allocation.stamina,
    }

    if any(value < 0 for value in points.values()):
        raise HTTPException(status_code=400, detail="Stat points cannot be negative")

    total_points = sum(points.values())
    if total_points <= 0:
        raise HTTPException(status_code=400, detail="No stat points allocated")

    if total_points > current_gladiator.stat_points:
        raise HTTPException(status_code=400, detail="Not enough stat points")

    # Racial modifiers affect allocated points. Equipment and other sources remain flat.
    racial_bonus_map = _build_racial_bonus_map(current_gladiator.race)
    adjusted_points = {
        key: _apply_racial_modifier(value, key, racial_bonus_map)
        for key, value in points.items()
    }

    health_points = adjusted_points["health"]
    if health_points > 0:
        current_gladiator.vitality += health_points
        current_gladiator.max_health = 1 + int(floor(current_gladiator.vitality * 1.5))
        current_gladiator.current_health = min(
            current_gladiator.current_health,
            current_gladiator.max_health,
        )

    current_gladiator.strength += adjusted_points["strength"]
    current_gladiator.dodge += adjusted_points["dodge"]
    current_gladiator.initiative += adjusted_points["initiative"]
    current_gladiator.weaponskill += adjusted_points["weaponskill"]
    current_gladiator.stamina += adjusted_points["stamina"]
    current_gladiator.stat_points -= total_points

    with rt.get_db() as db:
        rt._save_gladiator(db, current_gladiator, player_token)
    return GladiatorResponse(**current_gladiator.to_dict())


@router.get("/gladiator")
def get_gladiator(request: Request):
    """Get current gladiator stats."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        current_gladiator = rt._load_gladiator(
            db, player_token, apply_equipment_bonuses=True
        )
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        gladiator_row = rt._get_gladiator_row(db, player_token)
        equipped_items = get_equipped_items(db, gladiator_row.id) if gladiator_row else {}
        inventory = get_gladiator_equipment(db, gladiator_row.id) if gladiator_row else []
        gladiator_dict = current_gladiator.to_dict()
        gladiator_dict["equipped_items"] = {
            slot: item.model_dump() for slot, item in equipped_items.items()
        }
        gladiator_dict["inventory"] = [item.model_dump() for item in inventory]
        return GladiatorResponse(**gladiator_dict)


@router.get("/recovery/status")
def get_recovery_status(request: Request):
    player_token = rt._resolve_player_token(request)
    now_epoch_seconds = int(time.time())
    current_tick = rt._get_current_recovery_tick(now_epoch_seconds)
    with rt.get_db() as db:
        row = rt._get_gladiator_row(db, player_token)
        if row is not None and rt._apply_recovery_to_row(row, current_tick):
            db.commit()
    return {
        "name": "recovery",
        "interval_seconds": rt.RECOVERY_INTERVAL_SECONDS,
        "heal_percent": int(rt.RECOVERY_HEAL_PERCENT * 100),
        "seconds_until_next_tick": rt._seconds_until_next_recovery(now_epoch_seconds),
        "server_epoch_seconds": now_epoch_seconds,
    }


@router.post("/gladiator/train")
def train_gladiator(request: Request):
    """Train the gladiator."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        current_gladiator = rt._load_gladiator(db, player_token)
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        if current_gladiator.gold < 10:
            raise HTTPException(status_code=400, detail="Not enough gold to train")

        current_gladiator.gold -= 10
        current_gladiator.strength += 1
        current_gladiator.dodge += 1
        current_gladiator.weaponskill += 1
        current_gladiator.vitality += 3
        current_gladiator.max_health = 1 + int(floor(current_gladiator.vitality * 1.5))
        current_gladiator.current_health = min(
            current_gladiator.current_health,
            current_gladiator.max_health,
        )
        apply_experience(current_gladiator, 10)
        rt._save_gladiator(db, current_gladiator, player_token)
        return GladiatorResponse(**current_gladiator.to_dict())
