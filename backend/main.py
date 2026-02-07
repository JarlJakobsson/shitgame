# ============================================
# FASTAPI APPLICATION
# ============================================

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import Receive, Scope, Send
from math import floor
import time
import random

from sqlalchemy import inspect, text

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

def _init_db():
    attempts = 0
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_equipped_items_column()
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


# List available enemies
@app.get("/enemies")
def get_enemies():
    """Get all available enemies."""
    with get_db() as db:
        gladiator = _load_gladiator(db)
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

# Combat remains in-memory per instance. Gladiator is persisted.
current_combat: Combat | None = None


def _load_gladiator(db, apply_equipment_bonuses: bool = False) -> Gladiator | None:
    row = db.query(GladiatorRow).first()
    if not row:
        return None
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


def _save_gladiator(db, gladiator: Gladiator):
    row = db.query(GladiatorRow).first()
    if not row:
        row = GladiatorRow()
        db.add(row)

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
def create_gladiator(gladiator_data: GladiatorCreate):
    """Create a new gladiator."""
    with get_db() as db:
        db.query(GladiatorEquipmentRow).delete()
        existing = db.query(GladiatorRow).first()
        if existing:
            db.delete(existing)
        db.commit()

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
        _save_gladiator(db, current_gladiator)
    return GladiatorResponse(**current_gladiator.to_dict())


@app.post("/gladiator/allocate")
def allocate_stat_points(allocation: StatAllocation):
    """Allocate unspent stat points from leveling."""
    with get_db() as db:
        current_gladiator = _load_gladiator(db, apply_equipment_bonuses=True)
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
        _save_gladiator(db, current_gladiator)
    return GladiatorResponse(**current_gladiator.to_dict())


@app.get("/gladiator")
def get_gladiator():
    """Get current gladiator stats."""
    with get_db() as db:
        current_gladiator = _load_gladiator(db, apply_equipment_bonuses=True)
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        gladiator_row = db.query(GladiatorRow).first()
        equipped_items = get_equipped_items(db, gladiator_row.id) if gladiator_row else {}
        inventory = get_gladiator_equipment(db, gladiator_row.id) if gladiator_row else []
        gladiator_dict = current_gladiator.to_dict()
        gladiator_dict["equipped_items"] = {slot: item.model_dump() for slot, item in equipped_items.items()}
        gladiator_dict["inventory"] = [item.model_dump() for item in inventory]
        return GladiatorResponse(**gladiator_dict)


@app.post("/gladiator/train")
def train_gladiator():
    """Train the gladiator."""
    with get_db() as db:
        current_gladiator = _load_gladiator(db)
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

        _save_gladiator(db, current_gladiator)
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
    global current_combat

    print("POST /combat/start called")
    with get_db() as db:
        current_gladiator = _load_gladiator(db)
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
        _save_gladiator(db, current_gladiator)

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

    current_combat = Combat(current_gladiator, opponent)

    print(f"Combat started: player={current_gladiator.name}, opponent={opponent.name}")

    if current_combat is None:
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
def execute_combat_round():
    """Execute one round of combat."""
    if current_combat is None:
        print("No active combat when trying to execute round.")
        raise HTTPException(status_code=400, detail="No active combat. Please start a new combat.")
    
    round_info = current_combat.execute_round()
    current_combat.battle_log.append(f"Round {round_info['round']}")
    current_combat.battle_log.extend(round_info["actions"])
    
    return {
        "round": round_info["round"],
        "actions": round_info["actions"],
        "player_health": current_combat.player.current_health,
        "opponent_health": current_combat.opponent.current_health,
        "winner": round_info["winner"]
    }


@app.post("/combat/finish")
def finish_combat():
    global current_combat
    """Finish combat and award rewards."""
    if current_combat is None:
        raise HTTPException(status_code=400, detail="No active combat")
    
    player = current_combat.player
    opponent = current_combat.opponent
    
    if player.is_alive():
        # Determine difficulty
        difficulty = "Strong" if "Strong" in opponent.name else ("Weak" if "Weak" in opponent.name else "Normal")
        reward_exp = 60 if difficulty == "Strong" else (45 if difficulty == "Normal" else 30)
        reward_gold = 30 if difficulty == "Strong" else (20 if difficulty == "Normal" else 10)

        apply_experience(player, reward_exp)
        player.gold += reward_gold
        player.wins += 1
        # Add gold/exp to combat log
        if hasattr(current_combat, "battle_log"):
            current_combat.battle_log.append(f"You earned {reward_gold} gold and {reward_exp} experience!")
        result = "victory"
    else:
        player.losses += 1
        result = "defeat"

    # Get final battle log
    battle_log = []
    if hasattr(current_combat, "battle_log"):
        battle_log = current_combat.battle_log

    with get_db() as db:
        _save_gladiator(db, player)

    current_combat = None

    return {
        "result": result,
        "gladiator": GladiatorResponse(**player.to_dict()),
        "reward_gold": reward_gold if player.is_alive() else 0,
        "reward_exp": reward_exp if player.is_alive() else 0,
        "battle_log": battle_log
    }


@app.get("/equipment")
def get_equipment():
    """Get all available equipment."""
    with get_db() as db:
        equipment = get_all_equipment(db)
        return equipment


@app.get("/equipment/shop")
def get_equipment_shop():
    """Get equipment available for purchase."""
    with get_db() as db:
        gladiator = _load_gladiator(db)
        if gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        shop_items = get_shop_inventory(db, gladiator.level)
        return ShopInventory(available_items=shop_items)


@app.get("/gladiator/equipment")
def get_gladiator_equipment_endpoint():
    """Get all equipment owned by the gladiator."""
    with get_db() as db:
        gladiator_row = db.query(GladiatorRow).first()
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipment = get_gladiator_equipment(db, gladiator_row.id)
        return equipment


@app.get("/gladiator/equipment/equipped")
def get_equipped_items_endpoint():
    """Get currently equipped items."""
    with get_db() as db:
        gladiator_row = db.query(GladiatorRow).first()
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipped = get_equipped_items(db, gladiator_row.id)
        return equipped


@app.post("/equipment/equip")
def equip_item_endpoint(request: EquipmentSlotRequest):
    """Equip an item to a specific slot."""
    with get_db() as db:
        gladiator_row = db.query(GladiatorRow).first()
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = equip_item(db, gladiator_row.id, request)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to equip item")
        return {"message": "Item equipped successfully"}


@app.post("/equipment/unequip")
def unequip_item_endpoint(slot: str):
    """Unequip an item from a specific slot."""
    with get_db() as db:
        gladiator_row = db.query(GladiatorRow).first()
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = unequip_item(db, gladiator_row.id, slot)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unequip item")
        return {"message": "Item unequipped successfully"}


@app.post("/equipment/purchase/{equipment_id}")
def purchase_equipment_endpoint(equipment_id: int):
    """Purchase equipment from the shop."""
    with get_db() as db:
        gladiator_row = db.query(GladiatorRow).first()
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = purchase_equipment(db, gladiator_row.id, equipment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to purchase equipment")
        updated_gladiator = _load_gladiator(db, apply_equipment_bonuses=True)
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
