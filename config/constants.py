import os
import sys


def _get_app_dir():
    """Get the application directory - works for both dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = _get_app_dir()

# Database configuration
DATABASE_FILE = os.path.join(APP_DIR, "database.db")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
LOG_DIR = os.path.join(APP_DIR, "logs")

# Application constants
APP_NAME = "再新洗車資料庫"
APP_VERSION = "1.1.0"
APP_AUTHOR = "Sukio Lin"

# UI constants
PLATE_MAX_LENGTH = 4
PHONE_MAX_LENGTH = 10
MIN_COLUMN_WIDTH = 150
DEFAULT_FONT_SIZES = {
    "button_font_size": 20,
    "table_font_size": 25,
    "input_font_size": 30,
}
