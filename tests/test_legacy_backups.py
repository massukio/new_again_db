"""Real backup files made by every old version of the app (tests/fixtures/legacy,
generated with tools/make_legacy_backups.py from the old code itself).
Whatever the file is called, if it follows one of our schemas it must restore."""
import os
import shutil

import pytest

from app import config
from app.db import Database

HERE = os.path.dirname(__file__)
LEGACY = os.path.join(HERE, "fixtures", "legacy")
FILES = sorted(f for f in os.listdir(LEGACY) if f.endswith((".db", ".sql")))

EXPECTED = {  # label -> (customers by plate, washes)
    "v0_2025-03-02_first": ({"ABC-1234": 1, "DEF-5678": 1}, 0),
    "v0b_2025-03-02_note": ({"ABC-1234": 1, "DEF-5678": 1}, 0),
    "v1_2025-08_main": ({"ABC-1234": 2, "DEF-5678": 1}, 0),
    "v1.1_2026-04": ({"ABC-1234": 2, "DEF-5678": 1}, 3),
}


def label_of(name):
    return os.path.splitext(name)[0]


def test_every_old_version_is_covered():
    assert {label_of(f) for f in FILES} == set(EXPECTED)
    assert len(FILES) == 6  # 4 .db + 2 .sql


def check_restored(db, label):
    by_plate, washes = EXPECTED[label]
    rows = db.list_customers()
    counts = {}
    for r in rows:
        counts[r["plate"]] = counts.get(r["plate"], 0) + 1
    assert counts == by_plate
    assert db.count_washes() == washes
    abc = [r for r in rows if r["plate"] == "ABC-1234" and r["phone"] == "0912345678"][0]
    if label != "v0_2025-03-02_first":
        assert abc["note"] == "老客戶"
    if label.startswith("v1.1"):
        assert abc["brand"] == "Toyota"
        assert db.customer_summary("ABC", "1234")["total"] == 1100
    # fully usable after the upgrade: another phone for an existing plate, a wash, an edit
    db.add_customer("DEF", "5678", "0955000111", "新號碼")
    db.add_wash("DEF", "5678", 350, None, "泡沫外表洗車")
    db.update_customer(abc["id"], "ABC", "1234", "0912345678", "改備註", "")
    assert db.get_customer(abc["id"])["note"] == "改備註"
    assert len(db.list_services()) > 0


@pytest.mark.parametrize("name", FILES)
@pytest.mark.parametrize("rename", [False, True])
def test_restore_old_backup(tmp_path, name, rename):
    src = os.path.join(LEGACY, name)
    if rename:  # any file name / extension must work: content decides
        src = shutil.copy(src, tmp_path / "隨便取的名字.bak")
    db = Database(str(tmp_path / "current.db"))
    db.add_customer("CUR", "1", "")
    info = Database.check_backup_file(str(src))
    assert info["customers"] == sum(EXPECTED[label_of(name)][0].values())
    db.restore_from(str(src))
    check_restored(db, label_of(name))
    db.close()


@pytest.mark.parametrize("name", [f for f in FILES if f.endswith(".db")])
def test_old_database_next_to_exe(tmp_path, monkeypatch, name):
    shutil.copy(os.path.join(LEGACY, name), tmp_path / "database.db")
    monkeypatch.delenv("NEWAGAIN_DATA_DIR", raising=False)
    monkeypatch.setattr(config, "app_dir", lambda: str(tmp_path))
    db = Database(config.db_path())
    assert db.path.endswith(os.path.join("再新洗車資料", "洗車資料.db"))
    check_restored(db, label_of(name))
    db.close()
