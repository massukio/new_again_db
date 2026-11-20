"""Application constants and data-location logic.

Data lives in a 「再新洗車資料」 folder next to the exe so the whole folder
(exe + data) can be copied anywhere. If that folder is not writable (e.g. the
exe was put under Program Files) we fall back to %LOCALAPPDATA%.

Every folder / file the program creates by itself has a Chinese name. Older
versions kept ``database.db`` (+ ``config.json``, ``logs/``) directly next to
the exe; ``database.db`` is moved into the data folder automatically on start-up
(renamed in place, never copied or deleted).
"""
import os
import sys

APP_NAME = "再新洗車資料庫"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Sukio Lin"
APP_CREATED_YEAR = 2025
APP_RELEASE_DATE = "2026-11-20"
APP_LICENSE = "MIT License"
APP_LICENSE_URL = "https://opensource.org/licenses/MIT"

DATA_DIRNAME = "再新洗車資料"             # next to the exe
DB_FILENAME = "洗車資料.db"
AUTO_BACKUP_DIRNAME = "自動備份"
AUTO_BACKUP_PREFIX = "自動備份_"          # 自動備份_20261120.db
BEFORE_RESTORE_PREFIX = "還原前備份_"     # 還原前備份_20261120_235959.db
UNREADABLE_PREFIX = "無法開啟的資料_"     # a damaged database is set aside, never deleted
LOG_FILENAME = "錯誤紀錄.log"
LOCK_FILENAME = "使用中.lock"
FALLBACK_DIRNAME = "再新洗車資料庫"       # under %LOCALAPPDATA%
MANUAL_BACKUP_PREFIX = "再新洗車備份_"    # default name of a manual backup
AUTO_BACKUP_KEEP = 30

# Older versions: database.db directly next to the exe.
LEGACY_DB_FILENAME = "database.db"

PLATE_PART_MAX = 4
PHONE_MAX = 10
WASH_TYPES = ["一般洗車", "精緻洗車", "美容", "其他"]

# UI scaling (same system as the auto-repair app): at REF_WIDTH x REF_HEIGHT
# the base font is REF_FONT_PT; 小/中/大/特大 multiply it. Calibrated on Windows.
REF_WIDTH, REF_HEIGHT, REF_FONT_PT = 1280, 760, 19
SCALE_EXPONENT = 0.7
MIN_FONT_PT, MAX_FONT_PT = 12, 34
FONT_SCALES = {"小": 0.85, "中": 1.0, "大": 1.15, "特大": 1.3}
DEFAULT_FONT_SIZE = "中"


def resource_path(*parts: str) -> str:
    """Path of a bundled file (works from source and from the PyInstaller exe)."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def _rename(old: str, new: str) -> bool:
    """Rename old -> new if old exists and new does not. True if new is now in place."""
    if not os.path.exists(old):
        return os.path.exists(new)
    if os.path.exists(new):
        return True
    try:
        os.rename(old, new)
        return True
    except OSError:
        return False


def _adopt_legacy_database(legacy_dir: str, data_folder: str) -> None:
    """Move the old ``database.db`` (next to the exe) into the data folder.

    The rollback journal moves with it (it is needed to recover after a crash).
    If anything fails the old file stays where it is and ``db_path`` keeps using it.
    """
    old_db = os.path.join(legacy_dir, LEGACY_DB_FILENAME)
    new_db = os.path.join(data_folder, DB_FILENAME)
    if not os.path.exists(old_db) or os.path.exists(new_db):
        return
    if not _rename(old_db, new_db):
        return
    for suffix in ("-journal", "-wal", "-shm"):  # companions must stay with their database
        if os.path.exists(old_db + suffix) and not _rename(old_db + suffix, new_db + suffix):
            for s2 in ("-journal", "-wal", "-shm"):
                _rename(new_db + s2, old_db + s2)
            _rename(new_db, old_db)
            return


def data_dir() -> str:
    override = os.environ.get("NEWAGAIN_DATA_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        _adopt_legacy_database(override, override)
        return override
    preferred = os.path.join(app_dir(), DATA_DIRNAME)
    if _is_writable(preferred):
        _adopt_legacy_database(app_dir(), preferred)
        return preferred
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    fallback = os.path.join(base, FALLBACK_DIRNAME, DATA_DIRNAME)
    os.makedirs(fallback, exist_ok=True)
    return fallback


def db_path() -> str:
    folder = data_dir()
    new = os.path.join(folder, DB_FILENAME)
    if not os.path.exists(new):
        # move failed (file in use?) - keep using the old database, never start empty
        for legacy_dir in {folder, app_dir()}:
            old = os.path.join(legacy_dir, LEGACY_DB_FILENAME)
            if os.path.exists(old):
                return old
    return new


def auto_backup_dir() -> str:
    path = os.path.join(data_dir(), AUTO_BACKUP_DIRNAME)
    os.makedirs(path, exist_ok=True)
    return path
