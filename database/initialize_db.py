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
            UNIQUE(part1, part2, phone_number)
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
