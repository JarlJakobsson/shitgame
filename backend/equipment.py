# ============================================
# EQUIPMENT SERVICE
# ============================================

from typing import List, Dict
from sqlalchemy.orm import Session
from models_db import EquipmentRow, GladiatorRow, GladiatorEquipmentRow
from models import Equipment, GladiatorEquipment, EquipmentSlotRequest


# Equipment slots configuration
EQUIPMENT_SLOTS = [
    "weapon", "offhand",
    "head", "shoulders", "chest", "hands", "legs", "feet",
    "cape", "neck", "ring", "amulet", "bracers", "ornament"
]

# Sample equipment data
SAMPLE_EQUIPMENT = [
    # Head Armor
    {"id": 1, "name": "Iron Helmet", "slot": "head", "item_type": "armor", "rarity": "common", "level_requirement": 1, "strength_bonus": 2, "vitality_bonus": 1, "value": 25, "description": "A sturdy iron helmet."},
    {"id": 2, "name": "Steel Crown", "slot": "head", "item_type": "armor", "rarity": "rare", "level_requirement": 5, "strength_bonus": 5, "vitality_bonus": 3, "dodge_bonus": 1, "value": 150, "description": "A crown forged from fine steel."},
    {"id": 3, "name": "Warlord's Helm", "slot": "head", "item_type": "armor", "rarity": "epic", "level_requirement": 10, "strength_bonus": 8, "vitality_bonus": 5, "stamina_bonus": 2, "value": 500, "description": "Ancient helm worn by legendary warlords."},

    # Chest Armor
    {"id": 4, "name": "Leather Vest", "slot": "chest", "item_type": "armor", "rarity": "common", "level_requirement": 1, "vitality_bonus": 3, "stamina_bonus": 1, "value": 30, "description": "Basic leather protection."},
    {"id": 5, "name": "Chain Mail", "slot": "chest", "item_type": "armor", "rarity": "rare", "level_requirement": 4, "vitality_bonus": 6, "dodge_bonus": 2, "value": 200, "description": "Interlinked metal chains provide good protection."},
    {"id": 6, "name": "Plate Armor", "slot": "chest", "item_type": "armor", "rarity": "epic", "level_requirement": 8, "vitality_bonus": 10, "strength_bonus": 3, "value": 600, "description": "Full plate armor of the finest quality."},

    # Weapons
    {"id": 7, "name": "Wooden Sword", "slot": "weapon", "item_type": "weapon", "rarity": "common", "level_requirement": 1, "weaponskill_bonus": 3, "value": 20, "description": "A simple wooden training sword."},
    {"id": 8, "name": "Iron Blade", "slot": "weapon", "item_type": "weapon", "rarity": "rare", "level_requirement": 3, "weaponskill_bonus": 6, "strength_bonus": 2, "value": 180, "description": "Well-crafted iron sword."},
    {"id": 9, "name": "Legendary Sword", "slot": "weapon", "item_type": "weapon", "rarity": "legendary", "level_requirement": 12, "weaponskill_bonus": 12, "strength_bonus": 5, "initiative_bonus": 3, "value": 1200, "description": "A sword of immense power and history."},

    # Accessories
    {"id": 10, "name": "Iron Ring", "slot": "ring", "item_type": "accessory", "rarity": "common", "level_requirement": 1, "strength_bonus": 1, "dodge_bonus": 1, "value": 15, "description": "A simple iron ring."},
    {"id": 11, "name": "Gold Amulet", "slot": "amulet", "item_type": "accessory", "rarity": "rare", "level_requirement": 6, "vitality_bonus": 4, "initiative_bonus": 2, "value": 250, "description": "Golden amulet with protective enchantment."},
    {"id": 12, "name": "Swift Boots", "slot": "feet", "item_type": "armor", "rarity": "rare", "level_requirement": 4, "initiative_bonus": 3, "dodge_bonus": 2, "value": 120, "description": "Light boots that enhance speed."},
    {"id": 13, "name": "Power Gauntlets", "slot": "hands", "item_type": "armor", "rarity": "epic", "level_requirement": 7, "strength_bonus": 6, "weaponskill_bonus": 3, "value": 400, "description": "Gauntlets that enhance physical power."},
    {"id": 14, "name": "Mystic Cape", "slot": "cape", "item_type": "accessory", "rarity": "rare", "level_requirement": 5, "initiative_bonus": 4, "dodge_bonus": 3, "value": 200, "description": "A cape that seems to shimmer with mystical energy."},
    {"id": 15, "name": "Guardian Bracers", "slot": "bracers", "item_type": "armor", "rarity": "epic", "level_requirement": 6, "vitality_bonus": 5, "dodge_bonus": 2, "value": 350, "description": "Bracers that provide excellent defense."},

    # Offhand
    {"id": 16, "name": "Wooden Shield", "slot": "offhand", "item_type": "shield", "rarity": "common", "level_requirement": 1, "vitality_bonus": 2, "dodge_bonus": 1, "value": 25, "description": "A battered wooden shield."},
    {"id": 17, "name": "Iron Buckler", "slot": "offhand", "item_type": "shield", "rarity": "rare", "level_requirement": 4, "vitality_bonus": 4, "dodge_bonus": 2, "initiative_bonus": 1, "value": 140, "description": "A sturdy buckler for tight defenses."},
    {"id": 18, "name": "Runed Tome", "slot": "offhand", "item_type": "focus", "rarity": "epic", "level_requirement": 8, "initiative_bonus": 3, "weaponskill_bonus": 2, "value": 380, "description": "Ancient runes hum with power."},
]


def initialize_equipment(db: Session) -> None:
    """Initialize or update the equipment table with sample data."""
    existing = {row.id: row for row in db.query(EquipmentRow).all()}

    for item_data in SAMPLE_EQUIPMENT:
        row = existing.get(item_data["id"])
        if row is None:
            db.add(EquipmentRow(**item_data))
            continue

        for key, value in item_data.items():
            setattr(row, key, value)

    db.commit()

    # Migrate legacy weapon slots stored as "hands".
    db.query(EquipmentRow).filter(
        EquipmentRow.item_type == "weapon",
        EquipmentRow.slot == "hands",
    ).update({EquipmentRow.slot: "weapon"})
    db.commit()


def get_all_equipment(db: Session) -> List[Equipment]:
    """Get all available equipment."""
    equipment_rows = db.query(EquipmentRow).all()
    return [Equipment(
        id=row.id,
        name=row.name,
        slot=row.slot,
        item_type=row.item_type,
        rarity=row.rarity,
        level_requirement=row.level_requirement,
        strength_bonus=row.strength_bonus,
        vitality_bonus=row.vitality_bonus,
        stamina_bonus=row.stamina_bonus,
        dodge_bonus=row.dodge_bonus,
        initiative_bonus=row.initiative_bonus,
        weaponskill_bonus=row.weaponskill_bonus,
        value=row.value,
        description=row.description
    ) for row in equipment_rows]


def get_shop_inventory(db: Session, gladiator_level: int, gladiator_id: int) -> List[Equipment]:
    """Get equipment available for purchase based on gladiator level."""
    all_equipment = db.query(EquipmentRow).filter(
        EquipmentRow.level_requirement <= gladiator_level
    ).all()

    gladiator = db.query(GladiatorRow).filter(GladiatorRow.id == gladiator_id).first()
    if not gladiator:
        equipment_rows = all_equipment
    else:
        owned_equipment_ids = db.query(GladiatorEquipmentRow.equipment_id).filter(
            GladiatorEquipmentRow.gladiator_id == gladiator.id
        ).all()
        owned_ids = set(eq_id[0] for eq_id in owned_equipment_ids)
        equipment_rows = [equipment for equipment in all_equipment if equipment.id not in owned_ids]

    return [Equipment(
        id=row.id,
        name=row.name,
        slot=row.slot,
        item_type=row.item_type,
        rarity=row.rarity,
        level_requirement=row.level_requirement,
        strength_bonus=row.strength_bonus,
        vitality_bonus=row.vitality_bonus,
        stamina_bonus=row.stamina_bonus,
        dodge_bonus=row.dodge_bonus,
        initiative_bonus=row.initiative_bonus,
        weaponskill_bonus=row.weaponskill_bonus,
        value=row.value,
        description=row.description
    ) for row in equipment_rows]


def get_gladiator_equipment(db: Session, gladiator_id: int) -> List[GladiatorEquipment]:
    """Get all equipment owned by a gladiator."""
    equipment_items = db.query(GladiatorEquipmentRow).filter(
        GladiatorEquipmentRow.gladiator_id == gladiator_id
    ).all()

    result = []
    for item in equipment_items:
        equipment = item.equipment
        gladiator_equipment = GladiatorEquipment(
            id=item.id,
            equipment=Equipment(
                id=equipment.id,
                name=equipment.name,
                slot=equipment.slot,
                item_type=equipment.item_type,
                rarity=equipment.rarity,
                level_requirement=equipment.level_requirement,
                strength_bonus=equipment.strength_bonus,
                vitality_bonus=equipment.vitality_bonus,
                stamina_bonus=equipment.stamina_bonus,
                dodge_bonus=equipment.dodge_bonus,
                initiative_bonus=equipment.initiative_bonus,
                weaponskill_bonus=equipment.weaponskill_bonus,
                value=equipment.value,
                description=equipment.description
            ),
            is_equipped=bool(item.is_equipped)
        )
        result.append(gladiator_equipment)

    return result


def get_equipped_items(db: Session, gladiator_id: int) -> Dict[str, Equipment]:
    """Get currently equipped items for a gladiator."""
    gladiator = db.query(GladiatorRow).filter(GladiatorRow.id == gladiator_id).first()
    if not gladiator or not gladiator.equipped_items:
        return {}

    equipped_items = {}
    for slot, equipment_id in gladiator.equipped_items.items():
        equipment = db.query(EquipmentRow).filter(EquipmentRow.id == equipment_id).first()
        if equipment:
            equipped_items[slot] = Equipment(
                id=equipment.id,
                name=equipment.name,
                slot=equipment.slot,
                item_type=equipment.item_type,
                rarity=equipment.rarity,
                level_requirement=equipment.level_requirement,
                strength_bonus=equipment.strength_bonus,
                vitality_bonus=equipment.vitality_bonus,
                stamina_bonus=equipment.stamina_bonus,
                dodge_bonus=equipment.dodge_bonus,
                initiative_bonus=equipment.initiative_bonus,
                weaponskill_bonus=equipment.weaponskill_bonus,
                value=equipment.value,
                description=equipment.description
            )

    return equipped_items


def equip_item(db: Session, gladiator_id: int, request: EquipmentSlotRequest) -> bool:
    """Equip an item to a specific slot."""
    if request.slot not in EQUIPMENT_SLOTS:
        return False

    gladiator_equipment = db.query(GladiatorEquipmentRow).filter(
        GladiatorEquipmentRow.gladiator_id == gladiator_id,
        GladiatorEquipmentRow.equipment_id == request.equipment_id
    ).first()

    if not gladiator_equipment:
        return False

    equipment = db.query(EquipmentRow).filter(EquipmentRow.id == request.equipment_id).first()
    if not equipment or equipment.slot != request.slot:
        return False

    gladiator = db.query(GladiatorRow).filter(GladiatorRow.id == gladiator_id).first()
    if not gladiator:
        return False

    if not gladiator.equipped_items:
        gladiator.equipped_items = {}

    current_equipped_id = gladiator.equipped_items.get(request.slot)
    if current_equipped_id:
        current_item = db.query(GladiatorEquipmentRow).filter(
            GladiatorEquipmentRow.gladiator_id == gladiator_id,
            GladiatorEquipmentRow.equipment_id == current_equipped_id
        ).first()
        if current_item:
            current_item.is_equipped = 0

    gladiator_equipment.is_equipped = 1
    gladiator.equipped_items[request.slot] = request.equipment_id
    gladiator.equipped_items = dict(gladiator.equipped_items)

    db.commit()
    return True


def unequip_item(db: Session, gladiator_id: int, slot: str) -> bool:
    """Unequip an item from a specific slot."""
    if slot not in EQUIPMENT_SLOTS:
        return False

    gladiator = db.query(GladiatorRow).filter(GladiatorRow.id == gladiator_id).first()
    if not gladiator or not gladiator.equipped_items:
        return False

    equipped_id = gladiator.equipped_items.get(slot)
    if not equipped_id:
        return False

    gladiator_equipment = db.query(GladiatorEquipmentRow).filter(
        GladiatorEquipmentRow.gladiator_id == gladiator_id,
        GladiatorEquipmentRow.equipment_id == equipped_id
    ).first()

    if gladiator_equipment:
        gladiator_equipment.is_equipped = 0

    del gladiator.equipped_items[slot]
    gladiator.equipped_items = dict(gladiator.equipped_items)

    db.commit()
    return True


def purchase_equipment(db: Session, gladiator_id: int, equipment_id: int) -> bool:
    """Purchase equipment for a gladiator."""
    equipment = db.query(EquipmentRow).filter(EquipmentRow.id == equipment_id).first()
    if not equipment:
        return False

    gladiator = db.query(GladiatorRow).filter(GladiatorRow.id == gladiator_id).first()
    if not gladiator or gladiator.gold < equipment.value:
        return False

    existing = db.query(GladiatorEquipmentRow).filter(
        GladiatorEquipmentRow.gladiator_id == gladiator_id,
        GladiatorEquipmentRow.equipment_id == equipment_id
    ).first()

    if existing:
        return False

    gladiator.gold -= equipment.value

    gladiator_equipment = GladiatorEquipmentRow(
        gladiator_id=gladiator_id,
        equipment_id=equipment_id,
        is_equipped=0
    )

    db.add(gladiator_equipment)
    db.commit()
    return True


def calculate_equipment_bonuses(db: Session, gladiator_id: int) -> Dict[str, int]:
    """Calculate total stat bonuses from equipped items."""
    equipped_items = get_equipped_items(db, gladiator_id)

    bonuses = {
        "strength_bonus": 0,
        "vitality_bonus": 0,
        "stamina_bonus": 0,
        "dodge_bonus": 0,
        "initiative_bonus": 0,
        "weaponskill_bonus": 0,
    }

    for equipment in equipped_items.values():
        bonuses["strength_bonus"] += equipment.strength_bonus
        bonuses["vitality_bonus"] += equipment.vitality_bonus
        bonuses["stamina_bonus"] += equipment.stamina_bonus
        bonuses["dodge_bonus"] += equipment.dodge_bonus
        bonuses["initiative_bonus"] += equipment.initiative_bonus
        bonuses["weaponskill_bonus"] += equipment.weaponskill_bonus

    return bonuses
