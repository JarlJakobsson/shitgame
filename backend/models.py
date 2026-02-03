# ============================================
# PYDANTIC MODELS FOR API
# ============================================

from pydantic import BaseModel
from typing import Optional, List


class GladiatorCreate(BaseModel):
    name: str
    race: str


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
