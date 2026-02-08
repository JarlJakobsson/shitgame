from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, func
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
    player_token = Column(String, nullable=False, default="single-player", index=True)
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
    last_recovery_tick = Column(Integer, nullable=False, default=0)
    strength = Column(Integer, nullable=False, default=0)
    dodge = Column(Integer, nullable=False, default=0)
    initiative = Column(Integer, nullable=False, default=0)
    weaponskill = Column(Integer, nullable=False, default=0)
    stamina = Column(Integer, nullable=False, default=0)

    stat_points = Column(Integer, nullable=False, default=0)
    equipped_items = Column(MutableDict.as_mutable(JSON), nullable=True)


class ChallengeRow(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    challenger_player_token = Column(String, nullable=False, index=True)
    challenged_player_token = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)


class FightHistoryRow(Base):
    __tablename__ = "fight_history"

    id = Column(Integer, primary_key=True)
    player_token = Column(String, nullable=False, index=True)
    mode = Column(String, nullable=False, default="pve", index=True)
    opponent_name = Column(String, nullable=False)
    opponent_race = Column(String, nullable=False, default="Unknown")
    opponent_level = Column(Integer, nullable=False, default=0)
    result = Column(String, nullable=False, default="defeat", index=True)
    battle_log = Column(JSON, nullable=False, default=list)
    battle_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
