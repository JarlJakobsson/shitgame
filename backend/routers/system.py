from fastapi import APIRouter, HTTPException, Request

from database import engine
from enemies import ENEMIES
from equipment import initialize_equipment
from models_db import (
    Base,
    ChallengeRow,
    EquipmentRow,
    FightHistoryRow,
    GladiatorEquipmentRow,
    GladiatorRow,
)
from races import RACES
import game_runtime as rt


router = APIRouter()


@router.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Gladiator Arena API"}


@router.get("/races")
def get_races():
    """Get all available races."""
    return {name: data for name, data in RACES.items()}


@router.get("/enemies")
def get_enemies(request: Request):
    """Get all available enemies for the player's level."""
    player_token = rt._resolve_player_token(request)
    with rt.get_db() as db:
        gladiator = rt._load_gladiator(db, player_token)
        if gladiator is None:
            return {}
        level = gladiator.level
        return {
            name: data
            for name, data in ENEMIES.items()
            if data.get("min_level", 1) <= level
        }


@router.post("/init-database")
def init_database():
    """Initialize database tables and sample data."""
    try:
        Base.metadata.create_all(bind=engine)
        with rt.get_db() as db:
            db.query(ChallengeRow).delete()
            db.query(FightHistoryRow).delete()
            db.query(GladiatorEquipmentRow).delete()
            db.commit()
            initialize_equipment(db)
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {e}")


@router.post("/reset-database")
def reset_database():
    """Completely reset the database - remove all gladiators and equipment data."""
    try:
        Base.metadata.create_all(bind=engine)
        with rt.get_db() as db:
            db.query(ChallengeRow).delete()
            db.query(FightHistoryRow).delete()
            db.query(GladiatorEquipmentRow).delete()
            db.query(GladiatorRow).delete()
            db.query(EquipmentRow).delete()
            db.commit()
            initialize_equipment(db)
        return {"message": "Database completely reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {e}")


@router.get("/health")
def health():
    return {"status": "ok"}
