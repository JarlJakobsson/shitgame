from __future__ import annotations

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


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
