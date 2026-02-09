import random

from fastapi import APIRouter, HTTPException, Query, Request

from combat import Combat
from enemies import ENEMIES
from gladiator import Enemy, Gladiator
from leveling import apply_experience
from races import RACES
from schemas import GladiatorResponse
import game_runtime as rt


router = APIRouter()


@router.post("/combat/start")
async def start_combat(request: Request, enemy_name: str = Query(None)):
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        current_gladiator = rt._load_gladiator(db, player_token)
        if current_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        if not current_gladiator.is_alive():
            raise HTTPException(
                status_code=400,
                detail="You are too injured to fight. Wait for recovery.",
            )

    # Try to get enemy_name from JSON body if not provided as query.
    if enemy_name is None:
        try:
            data = await request.json()
            enemy_name = data.get("enemy_name")
        except Exception:
            enemy_name = None

    opponent = None
    if enemy_name and enemy_name in ENEMIES:
        required_level = ENEMIES[enemy_name].get("min_level", 1)
        if current_gladiator.level < required_level:
            raise HTTPException(status_code=400, detail="Enemy locked by level")
        enemy_data = ENEMIES[enemy_name]
        opponent = Enemy(enemy_name, enemy_data)
    else:
        # Fallback to a random race opponent.
        opponent_races = list(RACES.keys())
        if not opponent_races:
            raise HTTPException(status_code=500, detail="No races available for opponent selection")
        opponent_race = random.choice(opponent_races)
        opponent = Gladiator(opponent_race, opponent_race, use_race_stats=True)
        opponent.current_health = opponent.max_health

    combat = Combat(current_gladiator, opponent)
    rt._set_current_combat(player_token, combat)
    if rt._get_current_combat(player_token) is None:
        raise HTTPException(status_code=500, detail="Failed to initialize combat")

    return {
        "player": current_gladiator.to_dict(),
        "opponent": opponent.to_dict(),
        "message": f"Combat started! Fighting {opponent.name}",
    }


@router.post("/combat/round")
def execute_combat_round(request: Request):
    """Execute one round of combat."""
    player_token = rt._resolve_player_token(request)
    combat = rt._get_current_combat(player_token)
    if combat is None:
        raise HTTPException(status_code=400, detail="No active combat. Please start a new combat.")

    round_info = combat.execute_round()
    rt._append_round_to_battle_log(combat, round_info)
    return {
        "round": round_info["round"],
        "actions": round_info["actions"],
        "player_health": combat.player.current_health,
        "opponent_health": combat.opponent.current_health,
        "winner": round_info["winner"],
    }


@router.post("/combat/finish")
def finish_combat(request: Request):
    """Finish combat and award rewards."""
    player_token = rt._resolve_player_token(request)
    combat = rt._get_current_combat(player_token)
    if combat is None:
        raise HTTPException(status_code=400, detail="No active combat")

    player = combat.player
    opponent = combat.opponent

    winner = getattr(combat, "winner", None)
    if winner is None:
        if player.is_alive() and not opponent.is_alive():
            winner = "player"
        elif opponent.is_alive() and not player.is_alive():
            winner = "opponent"
        elif player.is_alive():
            winner = "player"
        else:
            winner = "opponent"

    if winner == "player":
        reward_exp = 45
        reward_gold = 20
        apply_experience(player, reward_exp)
        player.gold += reward_gold
        player.wins += 1
        if hasattr(combat, "battle_log"):
            combat.battle_log.append(f"You earned {reward_gold} gold and {reward_exp} experience!")
        result = "victory"
    else:
        reward_exp = 0
        reward_gold = 0
        player.losses += 1
        result = "defeat"

    battle_log = list(getattr(combat, "battle_log", []) or [])

    with rt.get_db() as db:
        rt._save_gladiator(db, player, player_token)
        opponent_race = getattr(opponent, "race", "Unknown") or "Unknown"
        if opponent.name in ENEMIES:
            opponent_level = int(ENEMIES[opponent.name].get("min_level", 0))
        else:
            opponent_level = int(getattr(opponent, "level", 0) or 0)
        battle_screen = rt._build_battle_screen(
            player=player,
            opponent=opponent,
            result=result,
            battle_log=battle_log,
            reward_gold=reward_gold,
            reward_exp=reward_exp,
            rounds=combat.round,
        )
        battle_screen["opponent"]["level"] = opponent_level
        rt._record_fight_history(
            db,
            player_token=player_token,
            mode="pve",
            opponent_name=opponent.name,
            opponent_race=opponent_race,
            opponent_level=opponent_level,
            result=result,
            battle_log=battle_log,
            battle_snapshot=battle_screen,
        )
        db.commit()

    rt._set_current_combat(player_token, None)
    return {
        "result": result,
        "gladiator": GladiatorResponse(**player.to_dict()),
        "reward_gold": reward_gold,
        "reward_exp": reward_exp,
        "battle_log": battle_log,
    }
