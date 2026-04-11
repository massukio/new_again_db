import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Provide a temporary database for testing."""
    db_path = str(tmp_path / "test.db")
    config_path = str(tmp_path / "config.json")
    log_dir = str(tmp_path / "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Patch at both the constants module and all modules that imported from it
    monkeypatch.setattr("config.constants.DATABASE_FILE", db_path)
    monkeypatch.setattr("config.constants.CONFIG_FILE", config_path)
    monkeypatch.setattr("config.constants.LOG_DIR", log_dir)
    monkeypatch.setattr("database.database.DATABASE_FILE", db_path)
    monkeypatch.setattr("database.initialize_db.DATABASE_FILE", db_path)

    from database.initialize_db import initialize_database
    initialize_database()
    return db_path


@pytest.fixture
def sample_data(temp_db):
    """Insert sample data and return it."""
    from database.database import add_plate_info
    records = [
        ("ABC", "1234", "0912345678", "常客"),
        ("DEF", "5678", "0923456789", "新客"),
        ("ABC", "1234", "0934567890", "同車不同人"),
        ("GHI", "9012", "", "無電話"),
    ]
    for part1, part2, phone, note in records:
        add_plate_info(part1, part2, phone, note)
    return records
