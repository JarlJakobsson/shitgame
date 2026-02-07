"""
Pytest configuration and shared fixtures for Gladiator Arena tests.
"""

import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import get_db
from models_db import Base
from main import app
from gladiator import Gladiator


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(test_db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_gladiator():
    """Create a mock gladiator for testing."""
    gladiator = Mock(spec=Gladiator)
    gladiator.name = "TestGladiator"
    gladiator.race = "Human"
    gladiator.level = 1
    gladiator.experience = 0
    gladiator.gold = 100
    gladiator.wins = 0
    gladiator.losses = 0
    gladiator.vitality = 30
    gladiator.max_health = 46
    gladiator.current_health = 46
    gladiator.strength = 25
    gladiator.dodge = 20
    gladiator.initiative = 20
    gladiator.weaponskill = 20
    gladiator.stamina = 15
    gladiator.stat_points = 0
    
    # Mock methods
    gladiator.is_alive.return_value = True
    gladiator.to_dict.return_value = {
        "name": gladiator.name,
        "race": gladiator.race,
        "level": gladiator.level,
        "experience": gladiator.experience,
        "gold": gladiator.gold,
        "wins": gladiator.wins,
        "losses": gladiator.losses,
        "vitality": gladiator.vitality,
        "max_health": gladiator.max_health,
        "current_health": gladiator.current_health,
        "strength": gladiator.strength,
        "dodge": gladiator.dodge,
        "initiative": gladiator.initiative,
        "weaponskill": gladiator.weaponskill,
        "stamina": gladiator.stamina,
        "stat_points": gladiator.stat_points,
        "is_alive": True,
    }
    
    return gladiator


@pytest.fixture
def sample_gladiator_data():
    """Sample gladiator creation data for testing."""
    return {
        "name": "TestGladiator",
        "race": "Human",
        "health": 30,
        "strength": 25,
        "dodge": 25,
        "initiative": 25,
        "weaponskill": 25,
        "stamina": 20
    }


@pytest.fixture
def sample_equipment_data():
    """Sample equipment data for testing."""
    return {
        "id": 1,
        "name": "Iron Helmet",
        "slot": "head",
        "item_type": "armor",
        "rarity": "common",
        "level_requirement": 1,
        "strength_bonus": 2,
        "vitality_bonus": 1,
        "stamina_bonus": 0,
        "dodge_bonus": 0,
        "initiative_bonus": 0,
        "weaponskill_bonus": 0,
        "value": 25,
        "description": "A sturdy iron helmet."
    }


@pytest.fixture
def sample_stat_allocation():
    """Sample stat allocation data for testing."""
    return {
        "health": 5,
        "strength": 3,
        "dodge": 2,
        "initiative": 0,
        "weaponskill": 0,
        "stamina": 0
    }


@pytest.fixture
def mock_equipment_row(sample_equipment_data):
    """Create a mock equipment row for testing."""
    from models_db import EquipmentRow
    
    equipment = Mock(spec=EquipmentRow)
    for key, value in sample_equipment_data.items():
        setattr(equipment, key, value)
    
    return equipment


@pytest.fixture
def mock_gladiator_equipment_row():
    """Create a mock gladiator equipment row for testing."""
    from models_db import GladiatorEquipmentRow
    
    gladiator_equipment = Mock(spec=GladiatorEquipmentRow)
    gladiator_equipment.id = 1
    gladiator_equipment.gladiator_id = 1
    gladiator_equipment.equipment_id = 1
    gladiator_equipment.is_equipped = False
    
    return gladiator_equipment


@pytest.fixture
def combat_players():
    """Create two gladiators for combat testing."""
    player = Gladiator("Player", "Human", use_race_stats=True)
    player.strength = 25
    player.vitality = 30
    player.max_health = 46
    player.current_health = 46
    player.dodge = 20
    player.initiative = 20
    player.weaponskill = 20
    player.stamina = 15
    
    opponent = Gladiator("Opponent", "Orc", use_race_stats=True)
    opponent.strength = 20
    opponent.vitality = 35
    opponent.max_health = 53
    opponent.current_health = 53
    opponent.dodge = 15
    opponent.initiative = 15
    opponent.weaponskill = 15
    opponent.stamina = 20
    
    return player, opponent


# Pytest markers for categorizing tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for API endpoints")
    config.addinivalue_line("markers", "slow: Tests that take more than a few seconds")
    config.addinivalue_line("markers", "database: Tests that require database interaction")
    config.addinivalue_line("markers", "equipment: Tests related to equipment functionality")
    config.addinivalue_line("markers", "combat: Tests related to combat system")
    config.addinivalue_line("markers", "gladiator: Tests related to gladiator functionality")


# Helper functions for tests
def create_mock_gladiator_with_equipment():
    """Create a mock gladiator with equipment bonuses applied."""
    gladiator = Mock(spec=Gladiator)
    gladiator.name = "EquippedGladiator"
    gladiator.race = "Human"
    gladiator.level = 1
    gladiator.experience = 0
    gladiator.gold = 75
    gladiator.wins = 0
    gladiator.losses = 0
    
    # Base stats with equipment bonuses
    gladiator.vitality = 34  # 33 base + 1 from helmet
    gladiator.max_health = 52  # 1 + floor(34 * 1.5)
    gladiator.current_health = 52
    gladiator.strength = 29  # 27 base + 2 from helmet
    gladiator.dodge = 27
    gladiator.initiative = 27
    gladiator.weaponskill = 27
    gladiator.stamina = 22
    gladiator.stat_points = 0
    
    gladiator.is_alive.return_value = True
    gladiator.to_dict.return_value = {
        "name": gladiator.name,
        "race": gladiator.race,
        "level": gladiator.level,
        "experience": gladiator.experience,
        "gold": gladiator.gold,
        "wins": gladiator.wins,
        "losses": gladiator.losses,
        "vitality": gladiator.vitality,
        "max_health": gladiator.max_health,
        "current_health": gladiator.current_health,
        "strength": gladiator.strength,
        "dodge": gladiator.dodge,
        "initiative": gladiator.initiative,
        "weaponskill": gladiator.weaponskill,
        "stamina": gladiator.stamina,
        "stat_points": gladiator.stat_points,
        "is_alive": True,
        "equipped_items": {"head": {
            "id": 1,
            "name": "Iron Helmet",
            "slot": "head",
            "strength_bonus": 2,
            "vitality_bonus": 1
        }},
        "inventory": []
    }
    
    return gladiator


def assert_equipment_bonuses_applied(gladiator_dict):
    """Assert that equipment bonuses are properly applied to gladiator stats."""
    # These values should include racial bonuses (Human +10%) and equipment bonuses
    expected_strength = 29  # 25 base + 10% racial + 2 equipment
    expected_vitality = 34   # 30 base + 10% racial + 1 equipment
    expected_max_health = 52  # 1 + floor(34 * 1.5)
    
    assert gladiator_dict["strength"] == expected_strength
    assert gladiator_dict["vitality"] == expected_vitality
    assert gladiator_dict["max_health"] == expected_max_health


def assert_valid_gladiator_response(data):
    """Assert that gladiator response data is valid."""
    required_fields = [
        "name", "race", "level", "experience", "gold", "wins", "losses",
        "vitality", "max_health", "current_health", "strength", "dodge",
        "initiative", "weaponskill", "stamina", "stat_points"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
        assert isinstance(data[field], (int, str)), f"Invalid type for {field}: {type(data[field])}"
    
    assert isinstance(data["name"], str) and len(data["name"]) > 0
    assert isinstance(data["race"], str) and len(data["race"]) > 0
    assert data["level"] >= 1
    assert data["experience"] >= 0
    assert data["gold"] >= 0
    assert data["wins"] >= 0
    assert data["losses"] >= 0
    assert data["vitality"] > 0
    assert data["max_health"] > 0
    assert data["current_health"] >= 0
    assert data["current_health"] <= data["max_health"]
    assert data["strength"] >= 0
    assert data["dodge"] >= 0
    assert data["initiative"] >= 0
    assert data["weaponskill"] >= 0
    assert data["stamina"] >= 0
    assert data["stat_points"] >= 0
