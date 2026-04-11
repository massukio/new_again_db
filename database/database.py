import sqlite3
from contextlib import contextmanager
from core.logger import logger
from config.constants import DATABASE_FILE


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        yield conn
    finally:
        conn.close()


# ── Plate Info CRUD ──────────────────────────────────────────────────────────

def add_plate_info(part1: str, part2: str, phone_number: str, note: str, brand: str = "") -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO plate_info (part1, part2, phone_number, note, brand) VALUES (?, ?, ?, ?, ?)',
                (part1.upper(), part2.upper(), phone_number, note, brand)
            )
            conn.commit()
            logger.info(f"Added plate info: {part1.upper()}-{part2.upper()} phone: {phone_number} brand: {brand}")
        except sqlite3.IntegrityError as e:
            logger.warning(f"Failed to add plate info: {e}")


def get_all_plate_info() -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info ORDER BY part1 ASC, part2 ASC')
        return [(f"{r[0]}-{r[1]}", r[2], r[3], r[4]) for r in cursor.fetchall()]


def update_plate_info(original_part1: str, original_part2: str, original_phone: str,
                      new_part1: str, new_part2: str, new_phone_number: str, new_note: str,
                      new_brand: str = "") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('''
                SELECT COUNT(*) FROM plate_info
                WHERE part1 = ? AND part2 = ? AND phone_number = ?
                AND NOT (part1 = ? AND part2 = ? AND phone_number = ?)
            ''', (new_part1.upper(), new_part2.upper(), new_phone_number,
                  original_part1.upper(), original_part2.upper(), original_phone))
            if cursor.fetchone()[0] > 0:
                conn.rollback()
                return False

            cursor.execute('''
                UPDATE plate_info SET part1 = ?, part2 = ?, phone_number = ?, note = ?, brand = ?
                WHERE part1 = ? AND part2 = ? AND phone_number = ?
            ''', (new_part1.upper(), new_part2.upper(), new_phone_number, new_note, new_brand,
                  original_part1.upper(), original_part2.upper(), original_phone))
            if cursor.rowcount > 0:
                conn.commit()
                return True
            conn.rollback()
            return False
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logger.error(f"Failed to update plate info: {e}")
            return False


def delete_plate_info(part1: str, part2: str, phone_number: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM plate_info WHERE part1 = ? AND part2 = ? AND phone_number = ?',
            (part1.upper(), part2.upper(), phone_number)
        )
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"Deleted plate info: {part1.upper()}-{part2.upper()} phone: {phone_number}")
        else:
            logger.error("Plate info not found in the database.")


def filter_plate_info(part1_filter: str, part2_filter: str, phone_filter: str, search_mode: str) -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        if search_mode == "電話查詢":
            cursor.execute(
                'SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info WHERE phone_number LIKE ?',
                (f"%{phone_filter}%",)
            )
        elif part1_filter and part2_filter:
            cursor.execute(
                'SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info WHERE part1 LIKE ? AND part2 LIKE ?',
                (f"%{part1_filter}%", f"%{part2_filter}%")
            )
        elif part1_filter:
            cursor.execute(
                'SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info WHERE part1 LIKE ?',
                (f"%{part1_filter}%",)
            )
        elif part2_filter:
            cursor.execute(
                'SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info WHERE part2 LIKE ?',
                (f"%{part2_filter}%",)
            )
        else:
            cursor.execute('SELECT part1, part2, phone_number, note, COALESCE(brand, "") FROM plate_info')
        return [(f"{r[0]}-{r[1]}", r[2], r[3], r[4]) for r in cursor.fetchall()]


def plate_exists(part1: str, part2: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM plate_info WHERE part1 = ? AND part2 = ?',
                       (part1.upper(), part2.upper()))
        return cursor.fetchone()[0] > 0


def plate_and_phone_exists(part1: str, part2: str, phone_number: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM plate_info WHERE part1 = ? AND part2 = ? AND phone_number = ?',
                       (part1.upper(), part2.upper(), phone_number))
        return cursor.fetchone()[0] > 0


def plate_and_phone_note_exists(part1: str, part2: str, phone_number: str, note: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM plate_info WHERE part1 = ? AND part2 = ? AND phone_number = ? AND note = ?',
            (part1.upper(), part2.upper(), phone_number, note)
        )
        return cursor.fetchone()[0] > 0


def plate_exists_excluding_original(new_part1: str, new_part2: str, original_part1: str, original_part2: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM plate_info WHERE part1 = ? AND part2 = ? AND NOT (part1 = ? AND part2 = ?)',
            (new_part1.upper(), new_part2.upper(), original_part1.upper(), original_part2.upper())
        )
        return cursor.fetchone()[0] > 0


# ── VIP ──────────────────────────────────────────────────────────────────────

def set_vip_status(part1: str, part2: str, phone: str, is_vip: bool) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE plate_info SET vip = ? WHERE part1 = ? AND part2 = ? AND phone_number = ?',
            (1 if is_vip else 0, part1.upper(), part2.upper(), phone)
        )
        conn.commit()


def get_vip_plates() -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT part1, part2, phone_number, note, COALESCE(brand, "") '
            'FROM plate_info WHERE vip = 1 ORDER BY part1, part2'
        )
        return [(f"{r[0]}-{r[1]}", r[2], r[3], r[4]) for r in cursor.fetchall()]


# ── Plate Stats ──────────────────────────────────────────────────────────────

def get_plate_summary(part1: str, part2: str) -> dict:
    """Get spending summary for a specific plate."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0), COUNT(*), MAX(wash_date),
                   CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(amount), 0) / COUNT(*) ELSE 0 END
            FROM wash_records WHERE plate_part1 = ? AND plate_part2 = ?
        ''', (part1.upper(), part2.upper()))
        total, count, last_visit, avg = cursor.fetchone()
        return {
            "total_spent": total,
            "visit_count": count,
            "last_visit": last_visit or "",
            "avg_spend": avg,
        }


def get_all_plates_with_stats() -> list:
    """Get all plates with last visit date and VIP status."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.part1, p.part2, p.phone_number, p.note, COALESCE(p.brand, ''),
                   COALESCE(p.vip, 0), MAX(w.wash_date) as last_visit
            FROM plate_info p
            LEFT JOIN wash_records w ON p.part1 = w.plate_part1 AND p.part2 = w.plate_part2
            GROUP BY p.part1, p.part2, p.phone_number
            ORDER BY p.part1 ASC, p.part2 ASC
        ''')
        return cursor.fetchall()


# ── Wash Records ─────────────────────────────────────────────────────────────

def add_wash_record(part1: str, part2: str, amount: int, wash_date: str, note: str = "") -> None:
    """Add a wash spending record. wash_date format: YYYY-MM-DD."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO wash_records (plate_part1, plate_part2, amount, wash_date, note) VALUES (?, ?, ?, ?, ?)',
            (part1.upper(), part2.upper(), amount, wash_date, note)
        )
        conn.commit()
        logger.info(f"Added wash record: {part1.upper()}-{part2.upper()} ${amount} on {wash_date}")


def get_wash_records_by_date_range(start_date: str, end_date: str) -> list:
    """Get wash records in date range. Returns [(plate, amount, wash_date, note), ...]."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT plate_part1, plate_part2, amount, wash_date, note
            FROM wash_records
            WHERE wash_date BETWEEN ? AND ?
            ORDER BY wash_date DESC, id DESC
        ''', (start_date, end_date))
        return [(f"{r[0]}-{r[1]}", r[2], r[3], r[4]) for r in cursor.fetchall()]


def get_earnings_summary(start_date: str, end_date: str) -> dict:
    """Get total earnings and record count for date range."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM wash_records
            WHERE wash_date BETWEEN ? AND ?
        ''', (start_date, end_date))
        total, count = cursor.fetchone()
        return {"total": total, "count": count}


def get_plate_spending(part1: str, part2: str, start_date: str = "", end_date: str = "") -> list:
    """Get wash records for a specific plate."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute('''
                SELECT amount, wash_date, note FROM wash_records
                WHERE plate_part1 = ? AND plate_part2 = ? AND wash_date BETWEEN ? AND ?
                ORDER BY wash_date DESC
            ''', (part1.upper(), part2.upper(), start_date, end_date))
        else:
            cursor.execute('''
                SELECT amount, wash_date, note FROM wash_records
                WHERE plate_part1 = ? AND plate_part2 = ?
                ORDER BY wash_date DESC
            ''', (part1.upper(), part2.upper()))
        return cursor.fetchall()


def delete_wash_record(record_id: int) -> None:
    """Delete a wash record by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM wash_records WHERE id = ?', (record_id,))
        if cursor.rowcount > 0:
            conn.commit()
