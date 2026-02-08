from fastapi import APIRouter, HTTPException, Request

from equipment import (
    equip_item,
    get_all_equipment,
    get_equipped_items,
    get_gladiator_equipment,
    get_shop_inventory,
    purchase_equipment,
    unequip_item,
)
from schemas import EquipmentSlotRequest, GladiatorResponse, ShopInventory
import game_runtime as rt


router = APIRouter()


@router.get("/equipment")
def get_equipment():
    """Get all available equipment."""
    with rt.get_db() as db:
        equipment = get_all_equipment(db)
        return equipment


@router.get("/equipment/shop")
def get_equipment_shop(request: Request):
    """Get equipment available for purchase."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        shop_items = get_shop_inventory(db, gladiator_row.level, gladiator_row.id)
        return ShopInventory(available_items=shop_items)


@router.get("/gladiator/equipment")
def get_gladiator_equipment_endpoint(request: Request):
    """Get all equipment owned by the gladiator."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipment = get_gladiator_equipment(db, gladiator_row.id)
        return equipment


@router.get("/gladiator/equipment/equipped")
def get_equipped_items_endpoint(request: Request):
    """Get currently equipped items."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        equipped = get_equipped_items(db, gladiator_row.id)
        return equipped


@router.post("/equipment/equip")
def equip_item_endpoint(request_data: EquipmentSlotRequest, request: Request):
    """Equip an item to a specific slot."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = equip_item(db, gladiator_row.id, request_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to equip item")
        return {"message": "Item equipped successfully"}


@router.post("/equipment/unequip")
def unequip_item_endpoint(request: Request, slot: str):
    """Unequip an item from a specific slot."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = unequip_item(db, gladiator_row.id, slot)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unequip item")
        return {"message": "Item unequipped successfully"}


@router.post("/equipment/purchase/{equipment_id}")
def purchase_equipment_endpoint(equipment_id: int, request: Request):
    """Purchase equipment from the shop."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator_row = rt._get_gladiator_row(db, player_token)
        if gladiator_row is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        success = purchase_equipment(db, gladiator_row.id, equipment_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to purchase equipment")
        updated_gladiator = rt._load_gladiator(
            db, player_token, apply_equipment_bonuses=True
        )
        if updated_gladiator is None:
            raise HTTPException(status_code=404, detail="No gladiator created")
        gladiator_dict = updated_gladiator.to_dict()
        equipped_items = get_equipped_items(db, gladiator_row.id)
        inventory = get_gladiator_equipment(db, gladiator_row.id)
        gladiator_dict["equipped_items"] = {
            slot: item.model_dump() for slot, item in equipped_items.items()
        }
        gladiator_dict["inventory"] = [item.model_dump() for item in inventory]
        return GladiatorResponse(**gladiator_dict)
