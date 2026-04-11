from utils.helpers import format_phone_number, validate_plate_parts


class TestFormatPhoneNumber:
    def test_10_digits(self):
        assert format_phone_number("0912345678") == "0912-345-678"

    def test_7_digits(self):
        assert format_phone_number("1234567") == "123-4567"

    def test_9_digits(self):
        assert format_phone_number("123456789") == "12-345-6789"

    def test_already_formatted(self):
        assert format_phone_number("0912-345-678") == "0912-345-678"

    def test_empty_string(self):
        assert format_phone_number("") == ""

    def test_none(self):
        assert format_phone_number(None) == ""

    def test_short_number(self):
        assert format_phone_number("123") == "123"


class TestValidatePlateParts:
    def test_valid(self):
        assert validate_plate_parts("ABC", "1234") is None

    def test_empty_part1(self):
        assert validate_plate_parts("", "1234") is not None

    def test_empty_part2(self):
        assert validate_plate_parts("ABC", "") is not None

    def test_whitespace_part1(self):
        assert validate_plate_parts("  ", "1234") is not None

    def test_none_part1(self):
        assert validate_plate_parts(None, "1234") is not None
