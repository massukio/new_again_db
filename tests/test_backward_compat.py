"""Test that the refactored app works with existing old databases."""
import sqlite3
import pytest


class TestOldDatabaseCompatibility:
    def test_old_schema_works(self, tmp_path, monkeypatch):
        """Simulate an old database created by the original app and verify it works."""
        db_path = str(tmp_path / "old.db")
        monkeypatch.setattr("config.constants.DATABASE_FILE", db_path)
        monkeypatch.setattr("database.database.DATABASE_FILE", db_path)
        monkeypatch.setattr("database.initialize_db.DATABASE_FILE", db_path)

        # Create DB with the original schema (no brand column, no wash_records)
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE plate_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part1 TEXT NOT NULL,
                part2 TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                note TEXT,
                UNIQUE(part1, part2, phone_number)
            )
        ''')
        conn.execute(
            "INSERT INTO plate_info (part1, part2, phone_number, note) VALUES (?, ?, ?, ?)",
            ("ABC", "1234", "0912345678", "老客戶")
        )
        conn.execute(
            "INSERT INTO plate_info (part1, part2, phone_number, note) VALUES (?, ?, ?, ?)",
            ("DEF", "5678", "0923456789", "")
        )
        conn.commit()
        conn.close()

        # Run migration to add brand column + wash_records table
        from database.initialize_db import migrate_database
        migrate_database()

        from database.database import (
            get_all_plate_info, filter_plate_info, plate_exists,
            plate_and_phone_exists, update_plate_info, delete_plate_info, add_plate_info,
        )

        # Read all — brand should default to ""
        data = get_all_plate_info()
        assert len(data) == 2
        assert data[0] == ("ABC-1234", "0912345678", "老客戶", "")

        # Filter
        results = filter_plate_info("ABC", "", "", "車牌查詢")
        assert len(results) == 1

        # Check existence
        assert plate_exists("ABC", "1234") is True
        assert plate_and_phone_exists("ABC", "1234", "0912345678") is True

        # Add new record with brand
        add_plate_info("GHI", "9012", "0934567890", "新增", "Toyota")
        assert len(get_all_plate_info()) == 3

        # Update
        result = update_plate_info("ABC", "1234", "0912345678", "ABC", "1234", "0912345678", "更新備註")
        assert result is True
        data = get_all_plate_info()
        abc_records = [r for r in data if r[0] == "ABC-1234"]
        assert abc_records[0][2] == "更新備註"

        # Delete
        delete_plate_info("DEF", "5678", "0923456789")
        assert len(get_all_plate_info()) == 2

    def test_old_db_with_empty_notes(self, tmp_path, monkeypatch):
        """Old DBs may have NULL notes."""
        db_path = str(tmp_path / "old2.db")
        monkeypatch.setattr("config.constants.DATABASE_FILE", db_path)
        monkeypatch.setattr("database.database.DATABASE_FILE", db_path)
        monkeypatch.setattr("database.initialize_db.DATABASE_FILE", db_path)

        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE plate_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part1 TEXT NOT NULL,
                part2 TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                note TEXT,
                UNIQUE(part1, part2, phone_number)
            )
        ''')
        conn.execute(
            "INSERT INTO plate_info (part1, part2, phone_number) VALUES (?, ?, ?)",
            ("ABC", "1234", "0912345678")
        )
        conn.commit()
        conn.close()

        from database.initialize_db import migrate_database
        migrate_database()

        from database.database import get_all_plate_info
        data = get_all_plate_info()
        assert len(data) == 1
        assert data[0][0] == "ABC-1234"
        assert data[0][3] == ""  # brand defaults to ""
