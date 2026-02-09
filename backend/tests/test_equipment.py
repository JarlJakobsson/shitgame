"""
Unit tests for equipment functionality.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from equipment import (
    SAMPLE_EQUIPMENT,
    calculate_equipment_bonuses,
    equip_item,
    get_all_equipment,
    get_equipped_items,
    get_gladiator_equipment,
    get_shop_inventory,
    initialize_equipment,
    purchase_equipment,
    unequip_item,
)
from schemas import EquipmentSlotRequest
from models_db import Base, EquipmentRow, GladiatorEquipmentRow, GladiatorRow


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _create_gladiator(session, name="TestGladiator", race="Human", level=1, gold=100):
    row = GladiatorRow(name=name, race=race, level=level, gold=gold, equipped_items={})
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


class TestEquipment:
    def test_initialize_equipment_is_idempotent(self, db_session):
        initialize_equipment(db_session)
        initialize_equipment(db_session)

        all_items = get_all_equipment(db_session)
        assert len(all_items) == len(SAMPLE_EQUIPMENT)

    def test_get_all_equipment(self, db_session):
        initialize_equipment(db_session)
        equipment = get_all_equipment(db_session)

        assert len(equipment) == len(SAMPLE_EQUIPMENT)
        assert equipment[0].id > 0
        assert equipment[0].name

    def test_get_shop_inventory_filters_by_level_and_owned(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session, level=1, gold=100)

        level_one_items = get_shop_inventory(
            db_session, gladiator_level=1, gladiator_id=gladiator.id
        )
        assert len(level_one_items) == len(SAMPLE_EQUIPMENT)
        assert any(item.level_requirement > 1 for item in level_one_items)
        assert [item.level_requirement for item in level_one_items] == sorted(
            item.level_requirement for item in level_one_items
        )
        iron_helmet = next((item for item in level_one_items if item.id == 1), None)
        assert iron_helmet is not None
        assert iron_helmet.value == 100  # sell 25 -> buy 100

        db_session.add(GladiatorEquipmentRow(gladiator_id=gladiator.id, equipment_id=1, is_equipped=0))
        db_session.commit()

        after_owning_item = get_shop_inventory(
            db_session, gladiator_level=1, gladiator_id=gladiator.id
        )
        assert 1 not in [item.id for item in after_owning_item]

    def test_purchase_equipment_fails_if_level_requirement_not_met(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session, level=1, gold=10_000)

        ok = purchase_equipment(db_session, gladiator.id, 9)  # level requirement 12
        assert ok is False

    def test_purchase_equipment_fails_if_weaponskill_requirement_not_met(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session, level=20, gold=10_000)

        ws_item = EquipmentRow(
            name="WS Test Axe",
            slot="weapon",
            item_type="weapon",
            rarity="common",
            level_requirement=1,
            weaponskill_requirement=50,
            value=10,
            description="Test requirement item",
        )
        db_session.add(ws_item)
        db_session.commit()

        ok = purchase_equipment(db_session, gladiator.id, ws_item.id)
        assert ok is False

        gladiator.weaponskill = 60
        db_session.commit()

        ok_after_ws = purchase_equipment(db_session, gladiator.id, ws_item.id)
        assert ok_after_ws is True

    def test_get_gladiator_equipment(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session)

        db_session.add(GladiatorEquipmentRow(gladiator_id=gladiator.id, equipment_id=1, is_equipped=0))
        db_session.commit()

        inventory = get_gladiator_equipment(db_session, gladiator.id)
        assert len(inventory) == 1
        assert inventory[0].equipment.id == 1
        assert inventory[0].is_equipped is False

    def test_get_equipped_items(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session)
        gladiator.equipped_items = {"head": 1}
        db_session.commit()

        equipped = get_equipped_items(db_session, gladiator.id)
        assert "head" in equipped
        assert equipped["head"].id == 1

    def test_equip_and_unequip_item(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session)

        db_session.add(GladiatorEquipmentRow(gladiator_id=gladiator.id, equipment_id=1, is_equipped=0))
        db_session.commit()

        equipped_ok = equip_item(
            db_session,
            gladiator.id,
            EquipmentSlotRequest(equipment_id=1, slot="head"),
        )
        assert equipped_ok is True

        db_session.refresh(gladiator)
        assert gladiator.equipped_items["head"] == 1

        unequipped_ok = unequip_item(db_session, gladiator.id, "head")
        assert unequipped_ok is True

        db_session.refresh(gladiator)
        assert "head" not in gladiator.equipped_items

    def test_purchase_equipment_success(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session, gold=100)

        ok = purchase_equipment(db_session, gladiator.id, 1)  # sell 25, buy 100
        assert ok is True

        db_session.refresh(gladiator)
        assert gladiator.gold == 0

        inventory = get_gladiator_equipment(db_session, gladiator.id)
        assert any(item.equipment.id == 1 for item in inventory)

    def test_purchase_equipment_insufficient_gold(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session, gold=100)

        ok = purchase_equipment(db_session, gladiator.id, 9)  # value 1200
        assert ok is False

        db_session.refresh(gladiator)
        assert gladiator.gold == 100

    def test_calculate_equipment_bonuses(self, db_session):
        initialize_equipment(db_session)
        gladiator = _create_gladiator(db_session)

        db_session.add_all(
            [
                GladiatorEquipmentRow(gladiator_id=gladiator.id, equipment_id=1, is_equipped=1),  # +2 str, +1 vit
                GladiatorEquipmentRow(gladiator_id=gladiator.id, equipment_id=7, is_equipped=1),  # +3 ws
            ]
        )
        gladiator.equipped_items = {"head": 1, "weapon": 7}
        db_session.commit()

        bonuses = calculate_equipment_bonuses(db_session, gladiator.id)

        assert bonuses["strength_bonus"] == 2
        assert bonuses["vitality_bonus"] == 1
        assert bonuses["weaponskill_bonus"] == 3
        assert bonuses["stamina_bonus"] == 0
        assert bonuses["dodge_bonus"] == 0
        assert bonuses["initiative_bonus"] == 0
