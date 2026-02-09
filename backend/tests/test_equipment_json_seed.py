from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from equipment import upsert_equipment_from_json
from models_db import Base, EquipmentRow


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


class TestEquipmentJsonSeed:
    def test_upsert_inserts_and_updates(self):
        session = _make_session()
        try:
            items = [
                {
                    "name": "Bronsyxa",
                    "slot": "weapon",
                    "item_type": "weapon",
                    "rarity": "common",
                    "level_requirement": 11,
                    "stamina_bonus": 7,
                    "value": 110,
                    "description": "Imported from test",
                }
            ]
            first = upsert_equipment_from_json(session, items)
            assert first["inserted"] == 1
            assert first["updated"] == 0
            assert first["skipped"] == 0

            updated_items = [
                {
                    "name": "Bronsyxa",
                    "slot": "weapon",
                    "item_type": "weapon",
                    "rarity": "rare",
                    "level_requirement": 12,
                    "stamina_bonus": 10,
                    "value": 125,
                    "description": "Updated from test",
                }
            ]
            second = upsert_equipment_from_json(session, updated_items)
            assert second["inserted"] == 0
            assert second["updated"] == 1
            assert second["skipped"] == 0

            row = session.query(EquipmentRow).filter(
                EquipmentRow.name == "Bronsyxa",
                EquipmentRow.slot == "weapon",
                EquipmentRow.item_type == "weapon",
            ).first()
            assert row is not None
            assert row.rarity == "rare"
            assert row.level_requirement == 12
            assert row.stamina_bonus == 10
            assert row.value == 125
        finally:
            session.close()

    def test_upsert_maps_weaponskill_requirement_from_metadata(self):
        session = _make_session()
        try:
            items = [
                {
                    "name": "Sea Reaver Axe",
                    "slot": "weapon",
                    "item_type": "weapon",
                    "metadata": {"vf_requirement": 140},
                }
            ]
            result = upsert_equipment_from_json(session, items)
            assert result["inserted"] == 1

            row = session.query(EquipmentRow).filter(
                EquipmentRow.name == "Sea Reaver Axe",
                EquipmentRow.slot == "weapon",
                EquipmentRow.item_type == "weapon",
            ).first()
            assert row is not None
            assert row.weaponskill_requirement == 140
        finally:
            session.close()

    def test_upsert_skips_invalid_entries(self):
        session = _make_session()
        try:
            payload = [
                {"name": "Valid Axe", "slot": "weapon", "item_type": "weapon"},
                {"name": "   ", "slot": "weapon", "item_type": "weapon"},
                "not-a-dict",
            ]
            result = upsert_equipment_from_json(session, payload)  # type: ignore[arg-type]
            assert result["inserted"] == 1
            assert result["updated"] == 0
            assert result["skipped"] == 2
        finally:
            session.close()
