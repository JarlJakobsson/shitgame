from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class EquipmentRow(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slot = Column(String, nullable=False)
    item_type = Column(String, nullable=False)
    rarity = Column(String, nullable=False, default="common")
    level_requirement = Column(Integer, nullable=False, default=1)

    strength_bonus = Column(Integer, nullable=False, default=0)
    vitality_bonus = Column(Integer, nullable=False, default=0)
    stamina_bonus = Column(Integer, nullable=False, default=0)
    dodge_bonus = Column(Integer, nullable=False, default=0)
    initiative_bonus = Column(Integer, nullable=False, default=0)
    weaponskill_bonus = Column(Integer, nullable=False, default=0)

    value = Column(Integer, nullable=False, default=10)
    description = Column(String, nullable=True)


class GladiatorEquipmentRow(Base):
    __tablename__ = "gladiator_equipment"

    id = Column(Integer, primary_key=True)
    gladiator_id = Column(Integer, ForeignKey("gladiators.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    is_equipped = Column(Integer, nullable=False, default=0)

    gladiator = relationship("GladiatorRow", backref="equipment_items")
    equipment = relationship("EquipmentRow")


class GladiatorRow(Base):
    __tablename__ = "gladiators"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    race = Column(String, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    experience = Column(Integer, nullable=False, default=0)
    gold = Column(Integer, nullable=False, default=100)
    wins = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)

    vitality = Column(Integer, nullable=False, default=0)
    max_health = Column(Integer, nullable=False, default=1)
    current_health = Column(Integer, nullable=False, default=1)
    strength = Column(Integer, nullable=False, default=0)
    dodge = Column(Integer, nullable=False, default=0)
    initiative = Column(Integer, nullable=False, default=0)
    weaponskill = Column(Integer, nullable=False, default=0)
    stamina = Column(Integer, nullable=False, default=0)

    stat_points = Column(Integer, nullable=False, default=0)
    equipped_items = Column(MutableDict.as_mutable(JSON), nullable=True)
