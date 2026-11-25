"""Automatic daily backups kept inside the data folder.

Manual backups (to USB / cloud folder) are done from the UI via
``Database.backup_to``; this module only handles the safety-net copies.
"""
import datetime as _dt
import glob
import os

from app.config import AUTO_BACKUP_KEEP, AUTO_BACKUP_PREFIX, BEFORE_RESTORE_PREFIX
from app.db import Database

AUTO_PREFIX = AUTO_BACKUP_PREFIX


def _prune(folder: str, prefix: str, keep: int) -> None:
    files = sorted(glob.glob(os.path.join(glob.escape(folder), glob.escape(prefix) + "*.db")))
    for old in files[:-keep] if keep > 0 else files:
        try:
            os.remove(old)
        except OSError:
            pass


def daily_auto_backup(db: Database, folder: str, keep: int = AUTO_BACKUP_KEEP) -> str:
    """Create today's auto backup if it does not exist yet. Returns its path."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{AUTO_PREFIX}{_dt.date.today():%Y%m%d}.db")
    if not os.path.exists(path):
        db.backup_to(path)
        _prune(folder, AUTO_PREFIX, keep)
    return path


def safety_backup_before_restore(db: Database, folder: str, keep: int = 10) -> str:
    """Snapshot current data before a restore, so a wrong restore can be undone."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(
        folder, f"{BEFORE_RESTORE_PREFIX}{_dt.datetime.now():%Y%m%d_%H%M%S}.db"
    )
    db.backup_to(path)
    _prune(folder, BEFORE_RESTORE_PREFIX, keep)
    return path
