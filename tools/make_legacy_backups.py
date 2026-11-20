"""Generate REAL backup files from every old version of the app (test fixtures).

Usage: python tools/make_legacy_backups.py <path to a clone with full history> [out_dir]

For each historical version it extracts that commit's code (git archive), uses
THAT version's own database code to create data, then backs it up exactly the
way that version did (a copy of database.db, and an SQL dump where the version
offered one). Output goes to tests/fixtures/legacy/ and is checked by
tests/test_legacy_backups.py. Re-run only if a new old-version format appears.
"""
import os
import subprocess
import sys
import tempfile

# (commit, label, offered .sql dump?)
VERSIONS = [
    ("fa742e1", "v0_2025-03-02_first", False),   # plate_info without note, UNIQUE(part1, part2)
    ("5f1c239", "v0b_2025-03-02_note", False),   # + note, still UNIQUE(part1, part2)
    ("18177f9", "v1_2025-08_main", True),        # UNIQUE(part1, part2, phone_number), .db or .sql backup
    ("21ad8ae", "v1.1_2026-04", True),           # + brand, vip, wash_records
]

# Runs inside the extracted old code, in a fresh process.
CHILD = r'''
import os, shutil, sqlite3, sys
sys.path.insert(0, os.getcwd())
label, out_dir, with_sql = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
if os.path.exists("database.db"):  # early commits shipped a database.db: never reuse its contents
    os.remove("database.db")
try:
    import db.initialize_db as init_mod, db.database as dbm          # 2025-03 layout
except ImportError:
    import database.initialize_db as init_mod, database.database as dbm
    import config.constants as C
    init_mod.DATABASE_FILE = dbm.DATABASE_FILE = C.DATABASE_FILE = os.path.join(os.getcwd(), "database.db")
init_mod.initialize_database()
if hasattr(init_mod, "migrate_database"):
    init_mod.migrate_database()
add = dbm.add_plate_info
nargs = add.__code__.co_argcount
rows = [("ABC", "1234", "0912345678", "老客戶", "Toyota"),
        ("DEF", "5678", "0923456789", "", "")]
if "18177f9" in label or "v1" in label:
    rows.append(("ABC", "1234", "0988777666", "第二支電話", ""))  # several phones per plate exist from v1
for r in rows:
    add(*r[:nargs])
if hasattr(dbm, "add_wash_record"):
    dbm.add_wash_record("ABC", "1234", 300, "2026-03-01", "一般洗車")
    dbm.add_wash_record("ABC", "1234", 800, "2026-04-01", "美容 - 打蠟")
    dbm.add_wash_record("DEF", "5678", 500, "2026-04-02", "精緻洗車")
if hasattr(dbm, "set_vip_status"):
    dbm.set_vip_status("ABC", "1234", "0912345678", True)
src = "database.db"
shutil.copyfile(src, os.path.join(out_dir, label + ".db"))         # the .db backup of that version
if with_sql:
    conn = sqlite3.connect(src)                                    # the .sql backup of that version
    with open(os.path.join(out_dir, label + ".sql"), "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    conn.close()
print("ok", label)
'''


def main():
    repo = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else
                          os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "legacy"))
    os.makedirs(out, exist_ok=True)
    for commit, label, with_sql in VERSIONS:
        work = tempfile.mkdtemp()
        archive = subprocess.run(["git", "-C", repo, "archive", commit], check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", work], input=archive, check=True)
        res = subprocess.run([sys.executable, "-c", CHILD, label, out, "1" if with_sql else "0"],
                             cwd=work, capture_output=True, text=True)
        print(res.stdout.strip() or res.stderr.strip().splitlines()[-1])
        if res.returncode:
            sys.exit(f"failed for {commit}:\n{res.stderr}")


if __name__ == "__main__":
    main()
