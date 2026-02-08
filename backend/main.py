# ============================================
# FASTAPI APPLICATION
# ============================================

from contextlib import asynccontextmanager
from collections import defaultdict, deque
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import Receive, Scope, Send
from math import floor
from threading import Lock
import time
import random

from sqlalchemy import inspect, or_, text

from models import (
    GladiatorCreate, GladiatorResponse, StatAllocation,
    EquipmentSlotRequest, ShopInventory
)
from gladiator import Gladiator
from combat import Combat
from races import RACES
from enemies import ENEMIES
from leveling import apply_experience
from database import engine, get_db
from models_db import Base, GladiatorRow, EquipmentRow, GladiatorEquipmentRow
from equipment import (
    initialize_equipment, get_all_equipment, get_shop_inventory,
    get_gladiator_equipment, get_equipped_items, equip_item, unequip_item,
    purchase_equipment, calculate_equipment_bonuses
)

# ============================================
# APP SETUP
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


app = FastAPI(title="Gladiator Arena API", version="1.0.0", lifespan=lifespan)


class StripApiPrefixMiddleware:
    """Allow Firebase /api/* rewrites by stripping the /api prefix."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path == "/api" or path.startswith("/api/"):
                new_path = path[4:] or "/"
                scope = dict(scope)
                scope["path"] = new_path
                if "raw_path" in scope:
                    raw_path = scope["raw_path"]
                    scope["raw_path"] = raw_path[4:] or b"/"
        await self.app(scope, receive, send)


app.add_middleware(StripApiPrefixMiddleware)


DEFAULT_PLAYER_TOKEN = "single-player"
PLAYER_ID_HEADER = "X-Player-ID"


def _init_db():
    attempts = 0
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_equipped_items_column()
            _ensure_player_token_column()
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


def _resolve_player_token(request: Request | None) -> str:
    if request is None:
        return DEFAULT_PLAYER_TOKEN
    header_value = request.headers.get(PLAYER_ID_HEADER, "").strip()
    return header_value or DEFAULT_PLAYER_TOKEN


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
    return gladiator


# List available enemies
@app.get("/enemies")
def get_enemies(request: Request):
    """Get all available enemies."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator = _load_gladiator(db, player_token)
        if gladiator is None:
            return {}
        level = gladiator.level
        return {
            name: data
            for name, data in ENEMIES.items()
            if data.get("min_level", 1) <= level
        }

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Combat is tracked per player token.
current_combat: Combat | None = None
current_combats: dict[str, Combat] = {}

# PVP random queue + notifications are in-memory for a single app instance.
random_battle_queue = deque()
random_battle_notifications = defaultdict(list)
random_battle_lock = Lock()


def _load_gladiator(db, player_token: str = DEFAULT_PLAYER_TOKEN, apply_equipment_bonuses: bool = False) -> Gladiator | None:
    row = _get_gladiator_row(db, player_token)
    if not row:
        return None
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
    if row is None:
        row = _get_gladiator_row(db, player_token)
    if not row:
        row = GladiatorRow(player_token=player_token)
        db.add(row)
    else:
        row.player_token = player_token

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


def _queue_notification(player_token: str, message: str):
    random_battle_notifications[player_token].append(
        {"type": "random_battle", "message": message}
    )


def _run_random_battle(db, challenger_row: GladiatorRow, opponent_row: GladiatorRow):
    challenger = _gladiator_from_row(db, challenger_row, apply_equipment_bonuses=True)
    opponent = _gladiator_from_row(db, opponent_row, apply_equipment_bonuses=True)

    challenger.current_health = challenger.max_health
    opponent.current_health = opponent.max_health

    combat = Combat(challenger, opponent)
    winner = None
    while winner is None:
        round_info = combat.execute_round()
        winner = round_info["winner"]

    if winner == "player":
        challenger.wins += 1
        opponent.losses += 1
        winner_name = challenger.name
        loser_name = opponent.name
    else:
        challenger.losses += 1
        opponent.wins += 1
        winner_name = opponent.name
        loser_name = challenger.name

    _save_gladiator(db, challenger, challenger_row.player_token, row=challenger_row)
    _save_gladiator(db, opponent, opponent_row.player_token, row=opponent_row)

    return {
        "winner_name": winner_name,
        "loser_name": loser_name,
        "rounds": combat.round,
        "challenger_survived": challenger.is_alive(),
        "opponent_survived": opponent.is_alive(),
    }


# ============================================
# GAME ENDPOINTS
# ============================================

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Gladiator Arena API"}


@app.get("/races")
def get_races():
    """Get all available races."""
    return {name: data for name, data in RACES.items()}


@app.post("/gladiator")
def create_gladiator(gladiator_data: GladiatorCreate, request: Request):
    """Create a new gladiator."""
    player_token = _resolve_player_token(request)

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

    # Apply racial bonus percentages (if any) after point allocation
    racial_bonus_map = {}
    race_data = RACES.get(gladiator_data.race, {})
    for entry in race_data.get("racial_bonus", []):
        stat_key = entry.get("stat", "").strip().lower()
        value = entry.get("value", "").replace("%", "").strip()
        try:
            percent = float(value) / 100.0
        except ValueError:
            continue
        racial_bonus_map[stat_key] = percent

    def apply_bonus(base_value, stat_key):
        percent = racial_bonus_map.get(stat_key, 0.0)
        adjusted = base_value + (base_value * percent)
        # Round down so partial points don't count
        return max(0, int(floor(adjusted)))

    stats_with_bonus = {key: apply_bonus(value, key) for key, value in stats.items()}

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
    with get_db() as db:
        existing = _get_gladiator_row(db, player_token)
        if existing:
            db.query(GladiatorEquipmentRow).filter(
                GladiatorEquipmentRow.gladiator_id == existing.id
            ).delete()
            db.delete(existing)
            db.commit()
        _save_gladiator(db, current_gladiator, player_token)
    return GladiatorResponse(**current_gladiator.to_dict())


@app.post("/gladiator/allocate")
def allocate_stat_points(allocation: StatAllocation, request: Request):
    """Allocate unspent stat points from leveling."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        current_gladiator = _load_gladiator(
            db, player_token, apply_equipment_bonuses=True
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

    health_points = points["health"]
    if health_points > 0:
        old_max_health = current_gladiator.max_health
        current_gladiator.vitality += health_points
        current_gladiator.max_health = 1 + int(floor(current_gladiator.vitality * 1.5))
        current_gladiator.current_health += current_gladiator.max_health - old_max_health

    current_gladiator.strength += points["strength"]
    current_gladiator.dodge += points["dodge"]
    current_gladiator.initiative += points["initiative"]
    current_gladiator.weaponskill += points["weaponskill"]
    current_gladiator.stamina += points["stamina"]

    current_gladiator.stat_points -= total_points

    with get_db() as db:
        _save_gladiator(db, current_gladiator, player_token)
    return GladiatorResponse(**current_gladiator.to_dict())


@app.get("/gladiator")
def get_gladiator(request: Request):
    """Get current gladiator stats."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        current_gladiator = _load_gladiator(
            db, player_token, apply_equipment_bonuses=True
        )
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        gladiator_row = _get_gladiator_row(db, player_token)
        equipped_items = get_equipped_items(db, gladiator_row.id) if gladiator_row else {}
        inventory = get_gladiator_equipment(db, gladiator_row.id) if gladiator_row else []
        gladiator_dict = current_gladiator.to_dict()
        gladiator_dict["equipped_items"] = {slot: item.model_dump() for slot, item in equipped_items.items()}
        gladiator_dict["inventory"] = [item.model_dump() for item in inventory]
        return GladiatorResponse(**gladiator_dict)


@app.post("/gladiator/train")
def train_gladiator(request: Request):
    """Train the gladiator."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        current_gladiator = _load_gladiator(db, player_token)
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
        current_gladiator.current_health = current_gladiator.max_health
        apply_experience(current_gladiator, 10)

        _save_gladiator(db, current_gladiator, player_token)
        return GladiatorResponse(**current_gladiator.to_dict())

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"}
    )

@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.post("/combat/start")
async def start_combat(request: Request, enemy_name: str = Query(None)):
    player_token = _resolve_player_token(request)
    print("POST /combat/start called")
    with get_db() as db:
        current_gladiator = _load_gladiator(db, player_token)
        if current_gladiator is None:
            print("No gladiator created")
            raise HTTPException(status_code=404, detail="No gladiator created")

    # Try to get enemy_name from JSON body if not provided as query
    if enemy_name is None:
        try:
            data = await request.json()
            enemy_name = data.get("enemy_name")
        except Exception:
            enemy_name = None

    print(f"Received enemy_name: {enemy_name}")

    # Reset player health
    current_gladiator.current_health = current_gladiator.max_health
    with get_db() as db:
        _save_gladiator(db, current_gladiator, player_token)

    # If enemy_name is provided and valid, use it
    opponent = None
    if enemy_name and enemy_name in ENEMIES:
        required_level = ENEMIES[enemy_name].get("min_level", 1)
        if current_gladiator.level < required_level:
            raise HTTPException(status_code=400, detail="Enemy locked by level")
        from gladiator import Enemy
        enemy_data = ENEMIES[enemy_name]
        opponent = Enemy(enemy_name, enemy_data)
    else:
        # Fallback to random race/difficulty
        opponent_races = list(RACES.keys())
        if not opponent_races:
            print("No races available for opponent selection")
            raise HTTPException(status_code=500, detail="No races available for opponent selection")
        opponent_race = random.choice(opponent_races)
        difficulty = random.choice(["Weak", "Normal", "Strong"])
        opponent = Gladiator(f"{difficulty} {opponent_race}", opponent_race, use_race_stats=True)
        if difficulty == "Weak":
            opponent.strength = int(opponent.strength * 0.8)
            opponent.dodge = int(opponent.dodge * 0.8)
            opponent.max_health = int(opponent.max_health * 0.9)
        elif difficulty == "Strong":
            opponent.strength = int(opponent.strength * 1.2)
            opponent.dodge = int(opponent.dodge * 1.2)
            opponent.max_health = int(opponent.max_health * 1.1)
        opponent.current_health = opponent.max_health

    combat = Combat(current_gladiator, opponent)
    _set_current_combat(player_token, combat)

    print(f"Combat started: player={current_gladiator.name}, opponent={opponent.name}")

    if _get_current_combat(player_token) is None:
        print("Failed to initialize combat")
        raise HTTPException(status_code=500, detail="Failed to initialize combat")

    response = {
        "player": current_gladiator.to_dict(),
        "opponent": opponent.to_dict(),
        "message": f"Combat started! Fighting {opponent.name}"
    }
    print(f"Returning from /combat/start: {response}")
    return response


@app.post("/combat/round")
def execute_combat_round(request: Request):
    """Execute one round of combat."""
    player_token = _resolve_player_token(request)
    combat = _get_current_combat(player_token)
    if combat is None:
        print("No active combat when trying to execute round.")
        raise HTTPException(status_code=400, detail="No active combat. Please start a new combat.")
    
    round_info = combat.execute_round()
    combat.battle_log.append(f"Round {round_info['round']}")
    combat.battle_log.extend(round_info["actions"])
    
    return {
        "round": round_info["round"],
        "actions": round_info["actions"],
        "player_health": combat.player.current_health,
        "opponent_health": combat.opponent.current_health,
        "winner": round_info["winner"]
    }


@app.post("/combat/finish")
def finish_combat(request: Request):
    """Finish combat and award rewards."""
    player_token = _resolve_player_token(request)
    combat = _get_current_combat(player_token)
    if combat is None:
        raise HTTPException(status_code=400, detail="No active combat")
    
    player = combat.player
    opponent = combat.opponent
    
    if player.is_alive():
        # Determine difficulty
        difficulty = "Strong" if "Strong" in opponent.name else ("Weak" if "Weak" in opponent.name else "Normal")
        reward_exp = 60 if difficulty == "Strong" else (45 if difficulty == "Normal" else 30)
        reward_gold = 30 if difficulty == "Strong" else (20 if difficulty == "Normal" else 10)

        apply_experience(player, reward_exp)
        player.gold += reward_gold
        player.wins += 1
        # Add gold/exp to combat log
        if hasattr(combat, "battle_log"):
            combat.battle_log.append(f"You earned {reward_gold} gold and {reward_exp} experience!")
        result = "victory"
    else:
        player.losses += 1
        result = "defeat"

    # Get final battle log
    battle_log = []
    if hasattr(combat, "battle_log"):
        battle_log = combat.battle_log

    with get_db() as db:
        _save_gladiator(db, player, player_token)

    _set_current_combat(player_token, None)

    return {
        "result": result,
        "gladiator": GladiatorResponse(**player.to_dict()),
        "reward_gold": reward_gold if player.is_alive() else 0,
        "reward_exp": reward_exp if player.is_alive() else 0,
        "battle_log": battle_log
    }


@app.post("/pvp/random-battle/join")
def join_random_battle(request: Request):
    player_token = _resolve_player_token(request)
    with get_db() as db:
        challenger_row = _get_gladiator_row(db, player_token)
        if challenger_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")

    with random_battle_lock:
        if player_token in random_battle_queue:
            return {"status": "queued", "message": "Already waiting in random battle queue."}

        opponent_token = None
        while random_battle_queue and opponent_token is None:
            queued_token = random_battle_queue.popleft()
            if queued_token != player_token:
                opponent_token = queued_token

        if opponent_token is None:
            random_battle_queue.append(player_token)
            return {"status": "queued", "message": "Joined queue. Waiting for opponent."}

    with get_db() as db:
        challenger_row = _get_gladiator_row(db, player_token)
        opponent_row = _get_gladiator_row(db, opponent_token)
        if challenger_row is None or opponent_row is None:
            with random_battle_lock:
                if player_token not in random_battle_queue:
                    random_battle_queue.append(player_token)
            return {"status": "queued", "message": "Joined queue. Waiting for opponent."}

        result = _run_random_battle(db, challenger_row, opponent_row)

    with random_battle_lock:
        _queue_notification(
            player_token,
            f"Random battle complete: {result['winner_name']} defeated {result['loser_name']} in {result['rounds']} rounds.",
        )
        _queue_notification(
            opponent_token,
            f"Random battle complete: {result['winner_name']} defeated {result['loser_name']} in {result['rounds']} rounds.",
        )

    return {
        "status": "matched",
        "message": "Random battle completed.",
        "battle_result": result,
    }


@app.get("/notifications")
def get_notifications(request: Request):
    player_token = _resolve_player_token(request)
    with random_battle_lock:
        notifications = list(random_battle_notifications.get(player_token, []))
        random_battle_notifications[player_token] = []
        is_queued = player_token in random_battle_queue
    return {"notifications": notifications, "queued_for_random_battle": is_queued}


@app.get("/equipment")
def get_equipment():
    """Get all available equipment."""
    with get_db() as db:
        equipment = get_all_equipment(db)
        return equipment


@app.get("/equipment/shop")
def get_equipment_shop(request: Request):
    """Get equipment available for purchase."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        shop_items = get_shop_inventory(db, gladiator_row.level, gladiator_row.id)
        return ShopInventory(available_items=shop_items)


@app.get("/gladiator/equipment")
def get_gladiator_equipment_endpoint(request: Request):
    """Get all equipment owned by the gladiator."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipment = get_gladiator_equipment(db, gladiator_row.id)
        return equipment


@app.get("/gladiator/equipment/equipped")
def get_equipped_items_endpoint(request: Request):
    """Get currently equipped items."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipped = get_equipped_items(db, gladiator_row.id)
        return equipped


@app.post("/equipment/equip")
def equip_item_endpoint(request_data: EquipmentSlotRequest, request: Request):
    """Equip an item to a specific slot."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = equip_item(db, gladiator_row.id, request_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to equip item")
        return {"message": "Item equipped successfully"}


@app.post("/equipment/unequip")
def unequip_item_endpoint(request: Request, slot: str):
    """Unequip an item from a specific slot."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = unequip_item(db, gladiator_row.id, slot)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unequip item")
        return {"message": "Item unequipped successfully"}


@app.post("/equipment/purchase/{equipment_id}")
def purchase_equipment_endpoint(equipment_id: int, request: Request):
    """Purchase equipment from the shop."""
    player_token = _resolve_player_token(request)
    with get_db() as db:
        gladiator_row = _get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = purchase_equipment(db, gladiator_row.id, equipment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to purchase equipment")
        updated_gladiator = _load_gladiator(
            db, player_token, apply_equipment_bonuses=True
        )
        if updated_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        gladiator_dict = updated_gladiator.to_dict()
        equipped_items = get_equipped_items(db, gladiator_row.id)
        inventory = get_gladiator_equipment(db, gladiator_row.id)
        gladiator_dict["equipped_items"] = {slot: item.model_dump() for slot, item in equipped_items.items()}
        gladiator_dict["inventory"] = [item.model_dump() for item in inventory]
        return GladiatorResponse(**gladiator_dict)


@app.post("/init-database")
def init_database():
    """Initialize database tables and sample data."""
    try:
        Base.metadata.create_all(bind=engine)
        with get_db() as db:
            db.query(GladiatorEquipmentRow).delete()
            db.commit()
            initialize_equipment(db)
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {e}")


@app.post("/reset-database")
def reset_database():
    """Completely reset the database - remove all gladiators and equipment data."""
    try:
        Base.metadata.create_all(bind=engine)
        with get_db() as db:
            db.query(GladiatorEquipmentRow).delete()
            db.query(GladiatorRow).delete()
            db.query(EquipmentRow).delete()
            db.commit()
            initialize_equipment(db)
        return {"message": "Database completely reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {e}")



@app.get("/health")
def health():
    return {"status": "ok"}
