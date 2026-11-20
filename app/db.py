"""SQLite data layer for 再新洗車資料庫.

Schema (kept compatible with every older version of the app, so backups move
freely between old and new versions)
---------------------------------------------------------------------------
plate_info   : one row per customer = plate (part1-part2) + phone. A plate may
               appear with several phones. note, brand (optional), vip flag.
               UNIQUE(part1, part2, phone_number).
wash_records : one row per paid visit, linked to the plate text
               (plate_part1, plate_part2), amount (integer NT$), wash_date
               'YYYY-MM-DD', note ('一般洗車 - 額外備註').
settings     : key/value (schema_version, font_size, last backup ...). New in 2.0;
               older apps simply ignore it.
services     : selectable service items (name, order, active). New in 2.0;
               deleting only hides. A wash stores the chosen names in its note
               ('泡沫外表洗車、皮椅內裝保養 - 備註'), the same format old versions used.

Old layouts handled by ``_create_schema``: original (plate_info without brand /
vip, no wash_records), 1.1 (brand), 1.1+ (vip, wash_records).

Performance: covering indexes
  idx_wash_plate (plate_part1, plate_part2, wash_date, amount) - a customer's
      history, last visit, totals: index only
  idx_wash_day   (wash_date, amount, plate_part1, plate_part2) - reports: index only
"""
import datetime as _dt
import os
import re
import sqlite3
import tempfile
import time
from typing import List, Optional, Tuple

SCHEMA_VERSION = 2
SQLITE_HEADER = b"SQLite format 3\x00"


class DataError(Exception):
    """User-facing error; message is shown to the user as-is (Chinese)."""


# --------------------------------------------------------------------- helpers
def clean_part(text: str) -> str:
    """Plate half: upper-case letters/digits only."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def clean_phone(text: str) -> str:
    """Phone: digits only (dashes / spaces removed)."""
    return re.sub(r"\D", "", text or "")


def format_phone(phone: str) -> str:
    """0912345678 -> 0912-345-678 (display only; stored as digits)."""
    if not phone or "-" in phone:
        return phone or ""
    if len(phone) == 10:
        return f"{phone[:4]}-{phone[4:7]}-{phone[7:]}"
    if len(phone) == 9:
        return f"{phone[:2]}-{phone[2:5]}-{phone[5:]}"
    if len(phone) == 7:
        return f"{phone[:3]}-{phone[3:]}"
    return phone


def _columns(conn, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _tables(conn) -> set:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create or upgrade the schema in place. Runs on open and after every restore."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS plate_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part1 TEXT NOT NULL,
            part2 TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            note TEXT,
            brand TEXT DEFAULT '',
            vip INTEGER DEFAULT 0,
            UNIQUE(part1, part2, phone_number)
        );
        CREATE TABLE IF NOT EXISTS wash_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_part1 TEXT NOT NULL,
            plate_part2 TEXT NOT NULL,
            amount INTEGER NOT NULL,
            wash_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS services (
            id         INTEGER PRIMARY KEY,
            name       TEXT NOT NULL UNIQUE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            active     INTEGER NOT NULL DEFAULT 1
        );
    """)
    cols = _columns(conn, "plate_info")
    if "brand" not in cols:
        conn.execute("ALTER TABLE plate_info ADD COLUMN brand TEXT DEFAULT ''")
    if "vip" not in cols:
        conn.execute("ALTER TABLE plate_info ADD COLUMN vip INTEGER DEFAULT 0")
    if conn.execute("SELECT value FROM settings WHERE key='services_seeded'").fetchone() is None:
        from app.config import DEFAULT_SERVICES
        if not conn.execute("SELECT 1 FROM services LIMIT 1").fetchone():
            conn.executemany("INSERT OR IGNORE INTO services(name, sort_order) VALUES(?, ?)",
                             [(name, i) for i, name in enumerate(DEFAULT_SERVICES)])
        conn.execute("INSERT INTO settings(key, value) VALUES('services_seeded', '1')")
    conn.executescript("""
        DROP INDEX IF EXISTS idx_wash_date;
        CREATE INDEX IF NOT EXISTS idx_wash_plate ON wash_records(plate_part1, plate_part2, wash_date, amount);
        CREATE INDEX IF NOT EXISTS idx_wash_day ON wash_records(wash_date, amount, plate_part1, plate_part2);
    """)
    conn.execute("INSERT INTO settings(key, value) VALUES('schema_version', ?) "
                 "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(SCHEMA_VERSION),))
    conn.commit()


_CUSTOMER_SELECT = (
    "SELECT p.id, p.part1, p.part2, COALESCE(p.phone_number, '') AS phone, COALESCE(p.note, '') AS note, "
    "COALESCE(p.brand, '') AS brand, COALESCE(p.vip, 0) AS vip, "
    "(SELECT MAX(w.wash_date) FROM wash_records w "
    " WHERE w.plate_part1 = p.part1 AND w.plate_part2 = p.part2) AS last_visit "
    "FROM plate_info p")


# old versions may have stored phones with dashes/spaces: compare digits only
PHONE_DIGITS = "REPLACE(REPLACE(COALESCE(phone_number, ''), '-', ''), ' ', '')"


def _customer(row) -> dict:
    d = dict(row)
    d["phone"] = clean_phone(d["phone"])
    d["plate"] = f"{d['part1']}-{d['part2']}"
    d["vip"] = bool(d["vip"])
    return d


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, timeout=10)
        self.conn.row_factory = sqlite3.Row
        try:
            self.conn.execute("PRAGMA cache_size = -16000")
            self.conn.execute("PRAGMA temp_store = MEMORY")
            _create_schema(self.conn)
        except sqlite3.Error:
            self.conn.close()  # release the file (Windows) before anyone moves it aside
            raise

    def close(self) -> None:
        try:
            self.conn.execute("PRAGMA optimize")
        except sqlite3.Error:
            pass
        self.conn.close()

    # ------------------------------------------------------------------ settings
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.conn:
            self.conn.execute("INSERT INTO settings(key, value) VALUES(?, ?) "
                              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    # ----------------------------------------------------------------- customers
    def list_customers(self, part1: str = "", part2: str = "", phone: str = "") -> List[dict]:
        """All customers, or filtered by plate halves (contains) or by phone (contains)."""
        sql, args = _CUSTOMER_SELECT + " WHERE 1=1", []
        p1, p2, ph = clean_part(part1), clean_part(part2), clean_phone(phone)
        if p1:
            sql += " AND p.part1 LIKE ?"
            args.append(f"%{p1}%")
        if p2:
            sql += " AND p.part2 LIKE ?"
            args.append(f"%{p2}%")
        if ph:
            sql += " AND " + PHONE_DIGITS.replace("phone_number", "p.phone_number") + " LIKE ?"
            args.append(f"%{ph}%")
        sql += " ORDER BY p.part1, p.part2, p.id DESC"  # a plate's newest phone number first
        return [_customer(r) for r in self.conn.execute(sql, args)]

    def plate_phones(self, part1: str, part2: str) -> List[dict]:
        """All phone rows of one plate, newest first (a car can have several numbers)."""
        return [dict(r) for r in self.conn.execute(
            f"SELECT id, {PHONE_DIGITS} AS phone, COALESCE(note, '') AS note FROM plate_info "
            "WHERE part1=? AND part2=? ORDER BY id DESC", (clean_part(part1), clean_part(part2)))]

    def get_customer(self, customer_id: int) -> Optional[dict]:
        row = self.conn.execute(_CUSTOMER_SELECT + " WHERE p.id=?", (customer_id,)).fetchone()
        return _customer(row) if row else None

    def plate_exists(self, part1: str, part2: str, exclude_id: Optional[int] = None) -> bool:
        sql, args = "SELECT 1 FROM plate_info WHERE part1=? AND part2=?", [clean_part(part1), clean_part(part2)]
        if exclude_id is not None:
            sql += " AND id<>?"
            args.append(exclude_id)
        return self.conn.execute(sql + " LIMIT 1", args).fetchone() is not None

    def plate_phone_exists(self, part1: str, part2: str, phone: str,
                           exclude_id: Optional[int] = None) -> bool:
        sql = f"SELECT 1 FROM plate_info WHERE part1=? AND part2=? AND {PHONE_DIGITS}=?"
        args = [clean_part(part1), clean_part(part2), clean_phone(phone)]
        if exclude_id is not None:
            sql += " AND id<>?"
            args.append(exclude_id)
        return self.conn.execute(sql + " LIMIT 1", args).fetchone() is not None

    @staticmethod
    def _validate_customer(part1, part2, phone) -> Tuple[str, str, str]:
        p1, p2, ph = clean_part(part1), clean_part(part2), clean_phone(phone)
        if not p1:
            raise DataError("請輸入車牌前半。")
        if not p2:
            raise DataError("請輸入車牌後半。")
        return p1, p2, ph

    def add_customer(self, part1: str, part2: str, phone: str, note: str = "", brand: str = "") -> int:
        p1, p2, ph = self._validate_customer(part1, part2, phone)
        if self.plate_phone_exists(p1, p2, ph):
            raise DataError("這個車牌和電話已經有資料了。")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO plate_info(part1, part2, phone_number, note, brand, vip) VALUES(?, ?, ?, ?, ?, 0)",
                (p1, p2, ph, (note or "").strip(), brand or ""))
        return cur.lastrowid

    def update_customer(self, customer_id: int, part1: str, part2: str, phone: str,
                        note: str = "", brand: str = "") -> None:
        p1, p2, ph = self._validate_customer(part1, part2, phone)
        old = self.get_customer(customer_id)
        if old is None:
            raise DataError("找不到這筆資料，可能已經被刪除了。")
        plate_changed = (p1, p2) != (old["part1"], old["part2"])
        if plate_changed and self.plate_exists(p1, p2, exclude_id=customer_id):
            raise DataError("這個車牌號碼已經有其他資料了，無法改成這個車牌。")
        if self.plate_phone_exists(p1, p2, ph, exclude_id=customer_id):
            raise DataError("這個車牌和電話已經有資料了。")
        with self.conn:
            self.conn.execute(
                "UPDATE plate_info SET part1=?, part2=?, phone_number=?, note=?, brand=? WHERE id=?",
                (p1, p2, ph, (note or "").strip(), brand or "", customer_id))
            # the wash history follows the plate, unless another customer row still uses the old plate
            if plate_changed and not self.plate_exists(old["part1"], old["part2"]):
                self.conn.execute(
                    "UPDATE wash_records SET plate_part1=?, plate_part2=? WHERE plate_part1=? AND plate_part2=?",
                    (p1, p2, old["part1"], old["part2"]))

    def delete_customer(self, customer_id: int) -> None:
        """Deletes the customer row only; wash records stay so past earnings remain correct."""
        with self.conn:
            self.conn.execute("DELETE FROM plate_info WHERE id=?", (customer_id,))

    def set_vip(self, customer_id: int, vip: bool) -> None:
        with self.conn:
            self.conn.execute("UPDATE plate_info SET vip=? WHERE id=?", (1 if vip else 0, customer_id))

    # ------------------------------------------------------------ service items
    def list_services(self, include_hidden: bool = False) -> List[dict]:
        sql = "SELECT id, name, sort_order, active FROM services"
        if not include_hidden:
            sql += " WHERE active=1"
        return [dict(r) for r in self.conn.execute(sql + " ORDER BY sort_order, id")]

    def add_service(self, name: str) -> int:
        name = (name or "").strip()
        if not name:
            raise DataError("項目名稱不能空白。")
        row = self.conn.execute("SELECT id, active FROM services WHERE name=?", (name,)).fetchone()
        order = self.conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM services").fetchone()[0]
        with self.conn:
            if row is not None:
                if row["active"]:
                    raise DataError(f"「{name}」已經存在了。")
                self.conn.execute("UPDATE services SET active=1, sort_order=? WHERE id=?", (order, row["id"]))
                return row["id"]
            return self.conn.execute("INSERT INTO services(name, sort_order) VALUES(?, ?)",
                                     (name, order)).lastrowid

    def rename_service(self, service_id: int, name: str) -> None:
        name = (name or "").strip()
        if not name:
            raise DataError("項目名稱不能空白。")
        other = self.conn.execute("SELECT id, active FROM services WHERE name=? AND id<>?",
                                  (name, service_id)).fetchone()
        with self.conn:
            if other is not None:
                if other["active"]:
                    raise DataError(f"「{name}」已經存在了。")
                n = 1  # a deleted item has this name: move it out of the way
                while self.conn.execute("SELECT 1 FROM services WHERE name=?", (f"{name}（舊{n}）",)).fetchone():
                    n += 1
                self.conn.execute("UPDATE services SET name=? WHERE id=?", (f"{name}（舊{n}）", other["id"]))
            self.conn.execute("UPDATE services SET name=? WHERE id=?", (name, service_id))

    def hide_service(self, service_id: int) -> None:
        with self.conn:
            self.conn.execute("UPDATE services SET active=0 WHERE id=?", (service_id,))

    def move_service(self, service_id: int, delta: int) -> None:
        ids = [x["id"] for x in self.list_services()]
        if service_id not in ids:
            return
        i, j = ids.index(service_id), ids.index(service_id) + delta
        if 0 <= j < len(ids):
            ids[i], ids[j] = ids[j], ids[i]
            with self.conn:
                self.conn.executemany("UPDATE services SET sort_order=? WHERE id=?",
                                      [(n, sid) for n, sid in enumerate(ids)])

    def count_customers(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM plate_info").fetchone()[0]

    # ---------------------------------------------------------------- wash records
    def add_wash(self, part1: str, part2: str, amount, wash_date: Optional[str] = None,
                 note: str = "") -> int:
        p1, p2 = clean_part(part1), clean_part(part2)
        if not p1 or not p2:
            raise DataError("車牌號碼不完整。")
        try:
            amount = int(str(amount).replace(",", "").replace("，", "").strip())
        except (TypeError, ValueError):
            raise DataError("請輸入金額（只能是數字）。")
        if amount < 0:
            raise DataError("金額不能是負數。")
        wash_date = wash_date or _dt.date.today().isoformat()
        try:
            _dt.date.fromisoformat(wash_date)
        except ValueError:
            raise DataError("日期格式錯誤。")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO wash_records(plate_part1, plate_part2, amount, wash_date, note) VALUES(?, ?, ?, ?, ?)",
                (p1, p2, amount, wash_date, (note or "").strip()))
        return cur.lastrowid

    def delete_wash(self, wash_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM wash_records WHERE id=?", (wash_id,))

    def customer_washes(self, part1: str, part2: str) -> List[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT id, wash_date, amount, COALESCE(note, '') AS note FROM wash_records "
            "WHERE plate_part1=? AND plate_part2=? ORDER BY wash_date DESC, id DESC",
            (clean_part(part1), clean_part(part2)))]

    def customer_summary(self, part1: str, part2: str) -> dict:
        row = self.conn.execute(
            "SELECT COUNT(*) AS visits, COALESCE(SUM(amount), 0) AS total, MIN(wash_date) AS first_visit, "
            "MAX(wash_date) AS last_visit FROM wash_records WHERE plate_part1=? AND plate_part2=?",
            (clean_part(part1), clean_part(part2))).fetchone()
        s = dict(row)
        s["avg"] = round(s["total"] / s["visits"]) if s["visits"] else 0
        return s

    def count_washes(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM wash_records").fetchone()[0]

    # ------------------------------------------------------------------ reports
    def report(self, date_from: str, date_to: str, bucket: str = "day") -> dict:
        """Totals for a period; bucket 'day' or 'month' for the breakdown. Index-only queries."""
        args = (date_from, date_to)
        where = "WHERE wash_date >= ? AND wash_date <= ?"
        t = self.conn.execute(
            f"SELECT COUNT(*) AS visits, COALESCE(SUM(amount), 0) AS total, "
            f"COUNT(DISTINCT plate_part1 || '-' || plate_part2) AS cars FROM wash_records {where}",
            args).fetchone()
        key = "wash_date" if bucket == "day" else "substr(wash_date, 1, 7)"
        buckets = [dict(r) for r in self.conn.execute(
            f"SELECT {key} AS period, COUNT(*) AS visits, SUM(amount) AS total "
            f"FROM wash_records {where} GROUP BY period ORDER BY period", args)]
        return {"visits": t["visits"], "total": t["total"], "cars": t["cars"], "buckets": buckets}

    def report_records(self, date_from: str, date_to: str, limit: int = 300) -> List[dict]:
        """Newest wash records in the period (for the report's list)."""
        return [dict(r) for r in self.conn.execute(
            "SELECT id, plate_part1 || '-' || plate_part2 AS plate, amount, wash_date, COALESCE(note, '') AS note "
            "FROM wash_records WHERE wash_date >= ? AND wash_date <= ? "
            "ORDER BY wash_date DESC, id DESC LIMIT ?", (date_from, date_to, int(limit)))]

    # ------------------------------------------------------------ backup/restore
    def _same_file(self, path: str) -> bool:
        try:
            return os.path.exists(path) and os.path.samefile(path, self.path)
        except OSError:
            return False

    def backup_to(self, dest_path: str) -> None:
        """Write a compact, consistent copy of the whole database (opens in old versions too)."""
        if self._same_file(dest_path):
            raise DataError("不能把備份存在目前正在使用的資料檔上，請換一個位置或檔名。")
        tmp = dest_path + ".tmp"
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
            self.conn.commit()
            self.conn.execute("VACUUM INTO ?", (tmp,))
            os.replace(tmp, dest_path)
        except (OSError, sqlite3.Error) as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            raise DataError(f"無法寫入備份檔：{e}")

    @staticmethod
    def check_backup_file(path: str) -> dict:
        """Validate a backup (.db from any version, or an old .sql dump).
        Returns {"customers": n, "washes": m} or raises DataError."""
        src, tmp = _open_backup_source(path)
        try:
            return _validate_source(src)
        finally:
            src.close()
            _remove(tmp)

    def restore_from(self, path: str) -> None:
        """Replace all current data with a backup, then upgrade it to the current schema."""
        if self._same_file(path):
            raise DataError("這是目前正在使用的資料檔，不需要還原。請選擇備份檔。")
        src, tmp = _open_backup_source(path)
        try:
            _validate_source(src)
            src.backup(self.conn)
        except sqlite3.Error as e:
            raise DataError(f"還原失敗：{e}")
        finally:
            src.close()
            _remove(tmp)
        try:
            _create_schema(self.conn)
        except sqlite3.Error as e:
            raise DataError(f"還原失敗：{e}")


# ------------------------------------------------------------- backup helpers
def _remove(path: Optional[str]) -> None:
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def _uri_path(path: str) -> str:
    from urllib.parse import quote
    p = os.path.abspath(path).replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return quote(p, safe="/:")


def _deny_outside_access(action, arg1, arg2, db_name, trigger):
    """Authorizer for loading .sql dumps: the script may only build its own database."""
    if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and arg2 == "load_extension":
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _open_backup_source(path: str):
    """Open a backup read-only. Old .sql dumps are loaded into a temporary database.
    Returns (connection, temp_path_or_None)."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        raise DataError("無法讀取這個檔案。")
    if head == SQLITE_HEADER:
        try:
            return sqlite3.connect(f"file:{_uri_path(path)}?mode=ro", uri=True), None
        except sqlite3.Error:
            raise DataError("備份檔已損壞或無法讀取，無法還原。")
    # older versions could also back up as an SQL text dump (*.sql)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            script = f.read()
    except (OSError, UnicodeDecodeError):
        raise DataError("這個檔案不是本程式的備份檔。")
    if "CREATE TABLE" not in script.upper() or "PLATE_INFO" not in script.upper():
        raise DataError("這個檔案不是本程式的備份檔。")
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(tmp)
    try:
        conn.set_authorizer(_deny_outside_access)
        conn.executescript(script)
        conn.set_authorizer(None)
        conn.commit()
    except sqlite3.Error:
        conn.close()
        _remove(tmp)
        raise DataError("這個 .sql 備份檔無法讀取，可能已損壞。")
    return conn, tmp


def _validate_source(conn: sqlite3.Connection) -> dict:
    try:
        if "plate_info" not in _tables(conn):
            raise DataError("這個檔案不是本程式的備份檔。")
        if not {"part1", "part2", "phone_number"} <= _columns(conn, "plate_info"):
            raise DataError("這個檔案不是本程式的備份檔。")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise DataError("備份檔已損壞，無法還原。")
        customers = conn.execute("SELECT COUNT(*) FROM plate_info").fetchone()[0]
        washes = (conn.execute("SELECT COUNT(*) FROM wash_records").fetchone()[0]
                  if "wash_records" in _tables(conn) else 0)
        return {"customers": customers, "washes": washes}
    except sqlite3.Error:
        raise DataError("備份檔已損壞或無法讀取，無法還原。")


def open_database(path: str) -> Tuple[Database, Optional[str]]:
    """Open (or create) the database. A file that is not a readable database is moved
    aside as 無法開啟的資料_<time>.db - never deleted - and a fresh one is started.
    Returns (db, moved_aside_path or None)."""
    from app.config import UNREADABLE_PREFIX
    try:
        return Database(path), None
    except sqlite3.OperationalError:
        raise  # locked / read-only / disk problem: NOT corruption - never move the data aside
    except sqlite3.DatabaseError as e:
        if "not a database" not in str(e) and "malformed" not in str(e):
            raise
        stamp = time.strftime("%Y%m%d_%H%M%S")
        aside = os.path.join(os.path.dirname(path), f"{UNREADABLE_PREFIX}{stamp}.db")
        os.replace(path, aside)
        for suffix in ("-journal", "-wal", "-shm"):  # keep companions with their database
            if os.path.exists(path + suffix):
                os.replace(path + suffix, aside + suffix)
        return Database(path), aside
