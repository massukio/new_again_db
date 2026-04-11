import sqlite3
from config.constants import DATABASE_FILE


def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plate_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part1 TEXT NOT NULL,
            part2 TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            note TEXT,
            brand TEXT DEFAULT '',
            vip INTEGER DEFAULT 0,
            UNIQUE(part1, part2, phone_number)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wash_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_part1 TEXT NOT NULL,
            plate_part2 TEXT NOT NULL,
            amount INTEGER NOT NULL,
            wash_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_wash_date ON wash_records(wash_date)
    ''')
    conn.commit()
    conn.close()


def migrate_database():
    """Add new columns/tables to existing databases (backward compat)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Add brand column if missing
    cursor.execute("PRAGMA table_info(plate_info)")
    columns = [row[1] for row in cursor.fetchall()]
    if "brand" not in columns:
        cursor.execute("ALTER TABLE plate_info ADD COLUMN brand TEXT DEFAULT ''")

    # Create wash_records table if missing
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wash_records'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE wash_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_part1 TEXT NOT NULL,
                plate_part2 TEXT NOT NULL,
                amount INTEGER NOT NULL,
                wash_date TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wash_date ON wash_records(wash_date)')

    # Add vip column if missing
    cursor.execute("PRAGMA table_info(plate_info)")
    columns = [row[1] for row in cursor.fetchall()]
    if "vip" not in columns:
        cursor.execute("ALTER TABLE plate_info ADD COLUMN vip INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
