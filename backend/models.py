# ============================================
# PYDANTIC MODELS FOR API
# ============================================

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Equipment(BaseModel):
    id: int
    name: str
    slot: str
    item_type: str
    rarity: str
    level_requirement: int
    strength_bonus: int = 0
    vitality_bonus: int = 0
    stamina_bonus: int = 0
    dodge_bonus: int = 0
    initiative_bonus: int = 0
    weaponskill_bonus: int = 0
    value: int = 10
    description: Optional[str] = None


class GladiatorEquipment(BaseModel):
    id: int
    equipment: Equipment
    is_equipped: bool


class GladiatorCreate(BaseModel):
    name: str
    race: str
    health: int = 0
    strength: int = 0
    dodge: int = 0
    initiative: int = 0
    weaponskill: int = 0
    stamina: int = 0


class StatAllocation(BaseModel):
    health: int = 0
    strength: int = 0
    dodge: int = 0
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
    dodge: int
    gold: int
    wins: int
    losses: int
    stamina: int
    stat_points: int
    vitality: int
    equipped_items: Optional[Dict[str, Any]] = None
    inventory: Optional[List[GladiatorEquipment]] = None


class EquipmentSlotRequest(BaseModel):
    equipment_id: int
    slot: str


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


class ShopInventory(BaseModel):
    available_items: List[Equipment]
