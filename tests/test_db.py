import os
import sqlite3

import pytest

from app import backup, config
from app.db import Database, DataError, format_phone, open_database

ORIGINAL_SCHEMA = """
CREATE TABLE plate_info (id INTEGER PRIMARY KEY AUTOINCREMENT, part1 TEXT NOT NULL, part2 TEXT NOT NULL,
                         phone_number TEXT NOT NULL, note TEXT, UNIQUE(part1, part2, phone_number));
INSERT INTO plate_info(part1, part2, phone_number, note) VALUES ('ABC', '1234', '0912345678', '老客戶');
INSERT INTO plate_info(part1, part2, phone_number, note) VALUES ('DEF', '5678', '0923456789', NULL);
"""

V11_SCHEMA = ORIGINAL_SCHEMA + """
ALTER TABLE plate_info ADD COLUMN brand TEXT DEFAULT '';
ALTER TABLE plate_info ADD COLUMN vip INTEGER DEFAULT 0;
UPDATE plate_info SET brand='Toyota', vip=1 WHERE part1='ABC';
CREATE TABLE wash_records (id INTEGER PRIMARY KEY AUTOINCREMENT, plate_part1 TEXT NOT NULL,
    plate_part2 TEXT NOT NULL, amount INTEGER NOT NULL, wash_date TEXT NOT NULL, note TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now', 'localtime')));
CREATE INDEX idx_wash_date ON wash_records(wash_date);
INSERT INTO wash_records(plate_part1, plate_part2, amount, wash_date, note) VALUES
  ('ABC', '1234', 300, '2026-10-01', '一般洗車'), ('ABC', '1234', 800, '2026-11-01', '美容 - 打蠟');
"""


def make_db(path, script):
    c = sqlite3.connect(str(path))
    c.executescript(script)
    c.commit()
    c.close()


@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "t.db"))
    yield d
    d.close()


# ---------------------------------------------------------------- old databases
@pytest.mark.parametrize("script", [ORIGINAL_SCHEMA, V11_SCHEMA])
def test_opens_old_databases(tmp_path, script):
    p = tmp_path / "database.db"
    make_db(p, script)
    d = Database(str(p))
    rows = d.list_customers()
    assert [r["plate"] for r in rows] == ["ABC-1234", "DEF-5678"]
    assert rows[1]["note"] == "" and rows[1]["brand"] == ""
    if script is V11_SCHEMA:
        assert rows[0]["brand"] == "Toyota" and rows[0]["last_visit"] == "2026-11-01"
        assert d.customer_summary("ABC", "1234") == {"visits": 2, "total": 1100, "first_visit": "2026-10-01",
                                                      "last_visit": "2026-11-01", "avg": 550}
    # works normally after upgrade
    d.add_wash("DEF", "5678", 200)
    assert d.customer_summary("def", "5678")["visits"] == 1
    d.close()
    # the upgraded file still opens with the OLD app's queries (backward compatible)
    c = sqlite3.connect(str(p))
    assert c.execute("SELECT part1, part2, phone_number, note, COALESCE(brand, '') FROM plate_info").fetchall()


def test_unreadable_file_is_set_aside_not_deleted(tmp_path):
    p = tmp_path / "洗車資料.db"
    p.write_bytes(b"this is not a database" * 100)
    d, aside = open_database(str(p))
    assert aside and os.path.exists(aside) and open(aside, "rb").read().startswith(b"this is not")
    assert d.count_customers() == 0
    d.close()


# ------------------------------------------------------------------ customers
def test_customer_rules(db):
    cid = db.add_customer("abc", "1234", "0912-345-678", " 常客 ", "Toyota")
    c = db.get_customer(cid)
    assert (c["plate"], c["phone"], c["note"], c["brand"]) == ("ABC-1234", "0912345678", "常客", "Toyota")
    with pytest.raises(DataError):
        db.add_customer("ABC", "1234", "0912345678")          # same plate + phone
    assert db.plate_exists("abc", "1234")                       # UI asks before adding another phone
    second = db.add_customer("ABC", "1234", "0999999999")
    with pytest.raises(DataError):
        db.add_customer("", "1234", "")
    other = db.add_customer("XYZ", "9", "")
    with pytest.raises(DataError):
        db.update_customer(other, "ABC", "1234", "")            # plate belongs to someone else
    db.update_customer(cid, "ABC", "1234", "0911111111", "改", "")
    assert db.get_customer(cid)["phone"] == "0911111111"
    db.delete_customer(second)
    assert db.get_customer(second) is None
    with pytest.raises(DataError):
        db.update_customer(second, "Q", "1", "")


def test_search(db):
    db.add_customer("ABC", "1234", "0912345678")
    db.add_customer("ABD", "5555", "0922000111")
    db.add_customer("XYZ", "1299", "0933000222")
    assert len(db.list_customers()) == 3
    assert [c["plate"] for c in db.list_customers(part1="ab")] == ["ABC-1234", "ABD-5555"]
    assert [c["plate"] for c in db.list_customers(part2="12")] == ["ABC-1234", "XYZ-1299"]
    assert [c["plate"] for c in db.list_customers(part1="a", part2="55")] == ["ABD-5555"]
    assert [c["plate"] for c in db.list_customers(phone="0922-000")] == ["ABD-5555"]


def test_editing_plate_moves_wash_history(db):
    cid = db.add_customer("OLD", "1", "")
    db.add_wash("OLD", "1", 300, "2026-01-01")
    db.update_customer(cid, "NEW", "1", "")
    assert db.customer_summary("NEW", "1")["visits"] == 1
    assert db.customer_summary("OLD", "1")["visits"] == 0
    # with a second customer row still on the plate, history stays with that plate
    a = db.add_customer("SHR", "2", "0911")
    db.add_customer("SHR", "2", "0922")
    db.add_wash("SHR", "2", 100, "2026-01-01")
    with pytest.raises(DataError):
        db.update_customer(a, "SHR", "2", "0922")
    db.update_customer(a, "SHR", "2", "0933")
    assert db.customer_summary("SHR", "2")["visits"] == 1


def test_washes_and_reports(db):
    db.add_wash("ABC", "1234", "1,500", "2026-11-02", "美容 - 打蠟")
    db.add_wash("ABC", "1234", 300, "2026-11-02")
    db.add_wash("XYZ", "9", 200, "2026-11-20")
    db.add_wash("XYZ", "9", 999, "2026-12-01")
    with pytest.raises(DataError):
        db.add_wash("ABC", "1234", "abc")
    with pytest.raises(DataError):
        db.add_wash("ABC", "1234", -1)
    r = db.report("2026-11-01", "2026-11-30")
    assert (r["visits"], r["total"], r["cars"]) == (3, 2000, 2)
    assert [(b["period"], b["visits"], b["total"]) for b in r["buckets"]] == [
        ("2026-11-02", 2, 1800), ("2026-11-20", 1, 200)]
    y = db.report("2026-01-01", "2026-12-31", "month")
    assert [b["period"] for b in y["buckets"]] == ["2026-11", "2026-12"]
    recs = db.report_records("2026-11-01", "2026-11-30")
    assert recs[0]["plate"] == "XYZ-9" and len(recs) == 3
    washes = db.customer_washes("abc", "1234")
    db.delete_wash(washes[0]["id"])
    assert db.customer_summary("ABC", "1234")["visits"] == 1


def test_format_phone():
    assert format_phone("0912345678") == "0912-345-678"
    assert format_phone("") == ""


# ------------------------------------------------------------ backup / restore
def test_backup_restore_roundtrip(db, tmp_path):
    db.add_customer("ABC", "1234", "0912345678")
    db.add_wash("ABC", "1234", 500, "2026-11-01")
    out = str(tmp_path / "再新洗車備份.db")
    db.backup_to(out)
    assert Database.check_backup_file(out) == {"customers": 1, "washes": 1}
    db.add_customer("NEW", "1", "")
    db.restore_from(out)
    assert db.count_customers() == 1 and db.count_washes() == 1
    with pytest.raises(DataError):
        db.backup_to(db.path)
    with pytest.raises(DataError):
        db.restore_from(db.path)


@pytest.mark.parametrize("script", [ORIGINAL_SCHEMA, V11_SCHEMA])
def test_restore_old_db_backup(db, tmp_path, script):
    old = tmp_path / "20250301_backup_database.db"
    make_db(old, script)
    db.add_customer("CUR", "1", "")
    db.restore_from(str(old))
    assert [c["plate"] for c in db.list_customers()] == ["ABC-1234", "DEF-5678"]
    assert "vip" in {r[1] for r in db.conn.execute("PRAGMA table_info(plate_info)")}
    db.add_wash("ABC", "1234", 100)  # upgraded and usable


@pytest.mark.parametrize("script", [ORIGINAL_SCHEMA, V11_SCHEMA])
def test_restore_old_sql_dump(db, tmp_path, script):
    src = tmp_path / "src.db"
    make_db(src, script)
    c = sqlite3.connect(str(src))
    dump = tmp_path / "20250301_backup.sql"
    with open(dump, "w", encoding="utf-8") as f:  # exactly how the old app wrote .sql backups
        for line in c.iterdump():
            f.write(f"{line}\n")
    c.close()
    info = Database.check_backup_file(str(dump))
    assert info["customers"] == 2
    db.restore_from(str(dump))
    assert [c["plate"] for c in db.list_customers()] == ["ABC-1234", "DEF-5678"]
    if script is V11_SCHEMA:
        assert db.customer_summary("ABC", "1234")["total"] == 1100


def test_restore_rejects_bad_files(db, tmp_path):
    for name, content in [("a.db", b"hello"), ("b.sql", "DROP TABLE x;".encode()),
                          ("c.sql", "CREATE TABLE plate_info(x); ATTACH 'evil.db' AS e;".encode())]:
        p = tmp_path / name
        p.write_bytes(content)
        with pytest.raises(DataError):
            db.restore_from(str(p))
    assert not (tmp_path / "evil.db").exists()
    other = tmp_path / "other.db"
    make_db(other, "CREATE TABLE foo(x);")
    with pytest.raises(DataError):
        db.restore_from(str(other))


def test_auto_backup(db, tmp_path):
    folder = tmp_path / "自動備份"
    folder.mkdir()
    for i in range(5):
        (folder / f"自動備份_2000010{i}.db").write_bytes(b"x")
    p = backup.daily_auto_backup(db, str(folder), keep=3)
    assert os.path.basename(p).startswith("自動備份_") and len(os.listdir(folder)) == 3
    s = backup.safety_backup_before_restore(db, str(folder))
    assert os.path.basename(s).startswith("還原前備份_")


# ---------------------------------------------------------------- file names
def test_old_database_next_to_exe_is_moved_in(tmp_path, monkeypatch):
    make_db(tmp_path / "database.db", V11_SCHEMA)
    (tmp_path / "database.db-journal").write_bytes(b"")
    monkeypatch.delenv("NEWAGAIN_DATA_DIR", raising=False)
    monkeypatch.setattr(config, "app_dir", lambda: str(tmp_path))
    path = config.db_path()
    assert path == str(tmp_path / "再新洗車資料" / "洗車資料.db")
    assert not (tmp_path / "database.db").exists()
    assert (tmp_path / "再新洗車資料" / "洗車資料.db-journal").exists()
    os.remove(tmp_path / "再新洗車資料" / "洗車資料.db-journal")
    d = Database(path)
    assert d.count_customers() == 2
    d.close()
    assert config.auto_backup_dir() == str(tmp_path / "再新洗車資料" / "自動備份")


def test_fresh_install_names(tmp_path, monkeypatch):
    monkeypatch.delenv("NEWAGAIN_DATA_DIR", raising=False)
    monkeypatch.setattr(config, "app_dir", lambda: str(tmp_path))
    assert config.db_path() == str(tmp_path / "再新洗車資料" / "洗車資料.db")


def test_several_numbers_newest_first(db):
    a = db.add_customer("CAR", "1", "0911000000")
    b = db.add_customer("CAR", "1", "0922000000")
    db.add_wash("CAR", "1", 300, "2026-11-01")
    assert [c["phone"] for c in db.list_customers(part1="CAR")] == ["0922000000", "0911000000"]
    assert [p["id"] for p in db.plate_phones("car", "1")] == [b, a]
    db.delete_customer(a)  # old number expired: history stays with the plate
    assert db.customer_summary("CAR", "1")["visits"] == 1
    assert [p["phone"] for p in db.plate_phones("CAR", "1")] == ["0922000000"]


def test_legacy_dashed_and_null_phones(tmp_path):
    p = tmp_path / "database.db"
    make_db(p, ORIGINAL_SCHEMA.replace("'0912345678'", "'0912-345-678'"))
    d = Database(str(p))
    c = d.list_customers(part1="ABC")[0]
    assert c["phone"] == "0912345678"                      # edit dialog gets digits, not truncated
    assert d.list_customers(phone="0912345")[0]["plate"] == "ABC-1234"
    assert d.plate_phone_exists("ABC", "1234", "0912345678")
    with pytest.raises(DataError):
        d.add_customer("ABC", "1234", "0912345678")         # same number in another spelling
    d.close()


def test_locked_database_is_not_set_aside(tmp_path):
    p = tmp_path / "洗車資料.db"
    Database(str(p)).close()
    holder = sqlite3.connect(str(p))
    holder.execute("BEGIN EXCLUSIVE")
    import app.db as appdb
    orig = appdb.Database.__init__

    def short_timeout(self, path):
        self.path = path
        self.conn = sqlite3.connect(path, timeout=0.1)
        self.conn.row_factory = sqlite3.Row
        try:
            appdb._create_schema(self.conn)
        except sqlite3.Error:
            self.conn.close()
            raise
    appdb.Database.__init__ = short_timeout
    try:
        with pytest.raises(sqlite3.OperationalError):
            open_database(str(p))
    finally:
        appdb.Database.__init__ = orig
        holder.rollback()
        holder.close()
    assert p.exists() and not list(tmp_path.glob("無法開啟的資料_*"))


def test_service_items(db):
    names = [x["name"] for x in db.list_services()]
    assert names[0] == "泡沫外表洗車" and names[-1] == "其他" and len(names) == 17
    sid = db.add_service("打蠟加購")
    with pytest.raises(DataError):
        db.add_service("打蠟加購")
    with pytest.raises(DataError):
        db.rename_service(sid, "  ")
    db.rename_service(sid, "打蠟")
    db.move_service(sid, -1)
    assert db.list_services()[-2]["name"] == "打蠟"
    db.hide_service(sid)
    assert "打蠟" not in [x["name"] for x in db.list_services()]
    assert db.add_service("打蠟") == sid               # re-adding un-hides
    db.hide_service(sid)
    db.rename_service(db.list_services()[0]["id"], "打蠟")  # hidden name moved aside
    assert "打蠟（舊1）" in [x["name"] for x in db.list_services(include_hidden=True)]


def test_services_seeded_once_and_on_upgrade(tmp_path):
    p = tmp_path / "database.db"
    make_db(p, V11_SCHEMA)
    d = Database(str(p))
    assert len(d.list_services()) == 17                 # an upgraded old database gets the price list
    d.hide_service(d.list_services()[0]["id"])
    d.close()
    d = Database(str(p))
    assert len(d.list_services()) == 16                 # not re-seeded on the next start
    d.close()


def test_uri_path_handles_network_paths():
    from app.db import _uri_path
    assert _uri_path("//NAS/share/x.db").startswith("////NAS/share/")  # file:////NAS/... (no URI authority)
    assert not _uri_path("/tmp/a b.db").startswith("//")


def test_rotation_with_glob_chars_in_folder(db, tmp_path):
    folder = tmp_path / "[洗車] 資料"  # [ ] are glob patterns and valid on Windows
    folder.mkdir()
    for i in range(5):
        (folder / f"{config.AUTO_BACKUP_PREFIX}2025010{i}.db").write_bytes(b"")
    backup.daily_auto_backup(db, str(folder), keep=3)
    assert len(os.listdir(folder)) == 3


def test_bad_backup_copy_never_replaces_a_good_one(db, tmp_path, monkeypatch):
    dest = tmp_path / "備份.db"
    db.backup_to(str(dest))
    good = dest.read_bytes()

    def broken(_path):
        raise DataError("備份檔已損壞，無法還原。")
    monkeypatch.setattr(Database, "check_backup_file", staticmethod(broken))
    with pytest.raises(DataError):
        db.backup_to(str(dest))
    assert dest.read_bytes() == good
    assert not os.path.exists(str(dest) + ".tmp")
