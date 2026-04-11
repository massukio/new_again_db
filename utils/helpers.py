def format_phone_number(phone_number):
    """Format phone number with dashes based on length."""
    if not phone_number:
        return ""
    if '-' in phone_number:
        return phone_number
    if len(phone_number) == 10:
        return f"{phone_number[:4]}-{phone_number[4:7]}-{phone_number[7:]}"
    elif len(phone_number) == 7:
        return f"{phone_number[:3]}-{phone_number[3:]}"
    elif len(phone_number) == 9:
        return f"{phone_number[:2]}-{phone_number[2:5]}-{phone_number[5:]}"
    return phone_number


def validate_plate_parts(part1, part2):
    """Validate plate parts. Returns error message or None if valid."""
    if not part1 or not part1.strip():
        return "車牌號碼前半部不能為空"
    if not part2 or not part2.strip():
        return "車牌號碼後半部不能為空"
    return None
