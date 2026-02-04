# ============================================
# FASTAPI APPLICATION
# ============================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random

from models import GladiatorCreate, GladiatorResponse, CombatRound, BattleResult
from gladiator import Gladiator
from combat import Combat
from races import RACES
from enemies import ENEMIES, get_enemy
# ============================================
# GAME ENDPOINTS
# ============================================

app = FastAPI(title="Gladiator Arena API", version="1.0.0")

# List available enemies
@app.get("/enemies")
def get_enemies():
    """Get all available enemies."""
    return {name: data for name, data in ENEMIES.items()}

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (in production, use a database)
current_gladiator: Gladiator = None
current_combat: Combat = None


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
    global current_gladiator
    
    if gladiator_data.race not in RACES:
        raise HTTPException(status_code=400, detail="Invalid race")
    
    if not gladiator_data.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    
    current_gladiator = Gladiator(gladiator_data.name, gladiator_data.race)
    return GladiatorResponse(**current_gladiator.to_dict())


@app.get("/gladiator")
def get_gladiator():
    """Get current gladiator stats."""
    if current_gladiator is None:
        raise HTTPException(status_code=404, detail="No gladiator created")
    
    return GladiatorResponse(**current_gladiator.to_dict())


@app.post("/gladiator/train")
def train_gladiator():
    """Train the gladiator."""
    if current_gladiator.gold < 10:
        raise HTTPException(status_code=400, detail="Not enough gold to train")
    
    current_gladiator.gold -= 10
    current_gladiator.strength += 1
    current_gladiator.agility += 1
    current_gladiator.weaponskill += 1
    current_gladiator.max_health += 5
    current_gladiator.current_health = current_gladiator.max_health
    current_gladiator.experience += 10
    
    return GladiatorResponse(**current_gladiator.to_dict())


from fastapi import Query, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"}
    )

@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.post("/combat/start")
async def start_combat(request: Request, enemy_name: str = Query(None)):
    global current_combat

    print("POST /combat/start called")

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

    # If enemy_name is provided and valid, use it
    opponent = None
    if enemy_name and enemy_name in ENEMIES:
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
        opponent = Gladiator(f"{difficulty} {opponent_race}", opponent_race)
        if difficulty == "Weak":
            opponent.strength = int(opponent.strength * 0.8)
            opponent.agility = int(opponent.agility * 0.8)
            opponent.max_health = int(opponent.max_health * 0.9)
        elif difficulty == "Strong":
            opponent.strength = int(opponent.strength * 1.2)
            opponent.agility = int(opponent.agility * 1.2)
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
        reward_exp = 50 if difficulty == "Strong" else (30 if difficulty == "Normal" else 20)
        reward_gold = 30 if difficulty == "Strong" else (20 if difficulty == "Normal" else 10)

        player.experience += reward_exp
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

    current_combat = None

    return {
        "result": result,
        "gladiator": GladiatorResponse(**player.to_dict()),
        "reward_gold": reward_gold if player.is_alive() else 0,
        "reward_exp": reward_exp if player.is_alive() else 0,
        "battle_log": battle_log
    }




@app.get("/health")
def health():
    return {"status": "ok"}
