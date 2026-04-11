import json
import os
from config.constants import CONFIG_FILE, DEFAULT_FONT_SIZES


def load_font_config():
    """Load font size configuration from config file."""
    config = dict(DEFAULT_FONT_SIZES)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return config


def save_font_config(button_font_size, table_font_size, input_font_size):
    """Save font size configuration to config file."""
    config = {
        "button_font_size": button_font_size,
        "table_font_size": table_font_size,
        "input_font_size": input_font_size,
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
