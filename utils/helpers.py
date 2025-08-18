def format_phone_number(phone_number):
    """Format phone number with dashes based on length."""
    if '-' in phone_number:
        return phone_number  # Skip formatting if '-' already present
    if len(phone_number) == 10:
        return f"{phone_number[:4]}-{phone_number[4:7]}-{phone_number[7:]}"
    elif len(phone_number) == 7:
        return f"{phone_number[:3]}-{phone_number[3:]}"
    elif len(phone_number) == 9:
        return f"{phone_number[:2]}-{phone_number[2:5]}-{phone_number[5:]}"
    return phone_number