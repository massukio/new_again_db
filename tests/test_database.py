import pytest
from database.database import (
    add_plate_info, get_all_plate_info, update_plate_info,
    delete_plate_info, filter_plate_info, plate_exists,
    plate_and_phone_exists, plate_and_phone_note_exists,
    plate_exists_excluding_original,
)


class TestAddPlateInfo:
    def test_add_basic(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "test")
        data = get_all_plate_info()
        assert len(data) == 1
        assert data[0] == ("ABC-1234", "0912345678", "test", "")

    def test_add_uppercases(self, temp_db):
        add_plate_info("abc", "def", "123", "")
        data = get_all_plate_info()
        assert data[0][0] == "ABC-DEF"

    def test_add_duplicate_ignored(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "first")
        add_plate_info("ABC", "1234", "0912345678", "second")
        assert len(get_all_plate_info()) == 1

    def test_add_same_plate_different_phone(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "")
        add_plate_info("ABC", "1234", "0999999999", "")
        assert len(get_all_plate_info()) == 2


class TestGetAllPlateInfo:
    def test_empty(self, temp_db):
        assert get_all_plate_info() == []

    def test_ordered(self, sample_data):
        data = get_all_plate_info()
        plates = [d[0] for d in data]
        assert plates == sorted(plates)


class TestUpdatePlateInfo:
    def test_update_success(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "old")
        result = update_plate_info("ABC", "1234", "0912345678", "ABC", "1234", "0912345678", "new")
        assert result is True
        data = get_all_plate_info()
        assert data[0][2] == "new"  # note updated

    def test_update_plate_number(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "test")
        result = update_plate_info("ABC", "1234", "0912345678", "XYZ", "9999", "0912345678", "test")
        assert result is True
        data = get_all_plate_info()
        assert data[0][0] == "XYZ-9999"

    def test_update_conflict(self, temp_db):
        add_plate_info("ABC", "1234", "0912345678", "")
        add_plate_info("DEF", "5678", "0999999999", "")
        result = update_plate_info("ABC", "1234", "0912345678", "DEF", "5678", "0999999999", "")
        assert result is False

    def test_update_nonexistent(self, temp_db):
        result = update_plate_info("ABC", "1234", "0912345678", "XYZ", "9999", "0999999999", "")
        assert result is False


class TestDeletePlateInfo:
    def test_delete_specific(self, sample_data):
        initial_count = len(get_all_plate_info())
        delete_plate_info("ABC", "1234", "0912345678")
        assert len(get_all_plate_info()) == initial_count - 1

    def test_delete_nonexistent(self, temp_db):
        # Should not raise
        delete_plate_info("ZZZ", "9999", "0000000000")

    def test_delete_requires_phone(self, sample_data):
        """Ensure delete only removes the specific record, not all with same plate."""
        initial_count = len(get_all_plate_info())
        delete_plate_info("ABC", "1234", "0912345678")
        remaining = get_all_plate_info()
        # ABC-1234 with phone 0934567890 should still exist
        assert len(remaining) == initial_count - 1
        abc_records = [r for r in remaining if r[0] == "ABC-1234"]
        assert len(abc_records) == 1


class TestFilterPlateInfo:
    def test_filter_by_plate_part1(self, sample_data):
        results = filter_plate_info("abc", "", "", "車牌查詢")
        assert len(results) == 2  # ABC-1234 appears twice (different phones)

    def test_filter_by_both_parts(self, sample_data):
        results = filter_plate_info("def", "5678", "", "車牌查詢")
        assert len(results) == 1

    def test_filter_by_phone(self, sample_data):
        results = filter_plate_info("", "", "0912", "電話查詢")
        assert len(results) == 1

    def test_filter_no_match(self, sample_data):
        results = filter_plate_info("ZZZ", "", "", "車牌查詢")
        assert len(results) == 0

    def test_filter_empty_returns_all(self, sample_data):
        results = filter_plate_info("", "", "", "車牌查詢")
        assert len(results) == len(sample_data)


class TestPlateExists:
    def test_exists(self, sample_data):
        assert plate_exists("ABC", "1234") is True

    def test_not_exists(self, sample_data):
        assert plate_exists("ZZZ", "9999") is False

    def test_case_insensitive(self, sample_data):
        assert plate_exists("abc", "1234") is True


class TestPlateAndPhoneExists:
    def test_exists(self, sample_data):
        assert plate_and_phone_exists("ABC", "1234", "0912345678") is True

    def test_not_exists(self, sample_data):
        assert plate_and_phone_exists("ABC", "1234", "0000000000") is False


class TestPlateAndPhoneNoteExists:
    def test_exists(self, sample_data):
        assert plate_and_phone_note_exists("ABC", "1234", "0912345678", "常客") is True

    def test_not_exists(self, sample_data):
        assert plate_and_phone_note_exists("ABC", "1234", "0912345678", "不存在") is False


class TestPlateExistsExcludingOriginal:
    def test_different_plate_exists(self, sample_data):
        assert plate_exists_excluding_original("DEF", "5678", "ABC", "1234") is True

    def test_same_plate(self, sample_data):
        assert plate_exists_excluding_original("ABC", "1234", "ABC", "1234") is False

    def test_nonexistent(self, sample_data):
        assert plate_exists_excluding_original("ZZZ", "9999", "ABC", "1234") is False


class TestWashRecords:
    def test_add_and_get_summary(self, temp_db):
        from database.database import add_plate_info, add_wash_record, get_plate_summary
        add_plate_info("ABC", "1234", "0912345678", "test")
        add_wash_record("ABC", "1234", 500, "2026-04-12", "一般洗車")
        add_wash_record("ABC", "1234", 800, "2026-04-10", "精緻洗車")
        summary = get_plate_summary("ABC", "1234")
        assert summary["total_spent"] == 1300
        assert summary["visit_count"] == 2
        assert summary["last_visit"] == "2026-04-12"
        assert summary["avg_spend"] == 650

    def test_empty_summary(self, temp_db):
        from database.database import get_plate_summary
        summary = get_plate_summary("ZZZ", "9999")
        assert summary["total_spent"] == 0
        assert summary["visit_count"] == 0
        assert summary["last_visit"] == ""

    def test_earnings_summary(self, temp_db):
        from database.database import add_plate_info, add_wash_record, get_earnings_summary
        add_plate_info("ABC", "1234", "0912345678", "test")
        add_wash_record("ABC", "1234", 500, "2026-04-12")
        add_wash_record("ABC", "1234", 300, "2026-04-12")
        summary = get_earnings_summary("2026-04-12", "2026-04-12")
        assert summary["total"] == 800
        assert summary["count"] == 2


class TestVIP:
    def test_set_and_get_vip(self, temp_db):
        from database.database import add_plate_info, set_vip_status, get_vip_plates
        add_plate_info("ABC", "1234", "0912345678", "test")
        set_vip_status("ABC", "1234", "0912345678", True)
        vips = get_vip_plates()
        assert len(vips) == 1
        assert vips[0][0] == "ABC-1234"

    def test_unset_vip(self, temp_db):
        from database.database import add_plate_info, set_vip_status, get_vip_plates
        add_plate_info("ABC", "1234", "0912345678", "test")
        set_vip_status("ABC", "1234", "0912345678", True)
        set_vip_status("ABC", "1234", "0912345678", False)
        assert len(get_vip_plates()) == 0


class TestPlatesWithStats:
    def test_returns_last_visit(self, temp_db):
        from database.database import add_plate_info, add_wash_record, get_all_plates_with_stats
        add_plate_info("ABC", "1234", "0912345678", "test")
        add_wash_record("ABC", "1234", 500, "2026-04-12")
        rows = get_all_plates_with_stats()
        assert len(rows) == 1
        assert rows[0][6] == "2026-04-12"  # last_visit

    def test_no_wash_records(self, temp_db):
        from database.database import add_plate_info, get_all_plates_with_stats
        add_plate_info("ABC", "1234", "0912345678", "test")
        rows = get_all_plates_with_stats()
        assert len(rows) == 1
        assert rows[0][6] is None  # no last_visit
