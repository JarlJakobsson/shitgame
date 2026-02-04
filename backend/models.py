# ============================================
# PYDANTIC MODELS FOR API
# ============================================

from pydantic import BaseModel
from typing import Optional, List


class GladiatorCreate(BaseModel):
    name: str
    race: str
    health: int = 0
    strength: int = 0
    agility: int = 0
    initiative: int = 0
    weaponskill: int = 0
    stamina: int = 0


class GladiatorResponse(BaseModel):
    weaponskill: int
    initiative: int
    name: str
    race: str
    level: int
    experience: int
    current_health: int
    max_health: int
    strength: int
    agility: int
    gold: int
    wins: int
    losses: int
    stamina: int


class CombatRound(BaseModel):
    round: int
    actions: List[str]
    player_health: int
    opponent_health: int
    winner: Optional[str] = None


class BattleResult(BaseModel):
    result: str
    experience_gained: Optional[int] = None
    gold_gained: Optional[int] = None
