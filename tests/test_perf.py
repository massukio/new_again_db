"""Guard against UI slowdowns with many customers (e.g. styling rows after the
table is filled made 3,000 rows take 17 s instead of 0.05 s)."""
import random
import time

import pytest
from PyQt5 import QtWidgets

from app import config
from app.db import Database


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_customer_list_with_3000_customers_is_fast(qapp, tmp_path, monkeypatch):
    monkeypatch.setenv("NEWAGAIN_DATA_DIR", str(tmp_path))
    db = Database(config.db_path())
    rng = random.Random(1)
    with db.conn:
        db.conn.executemany(
            "INSERT OR IGNORE INTO plate_info(part1, part2, phone_number, note, brand, vip) VALUES(?, ?, ?, '', '', 0)",
            [("".join(rng.choice("ABCDEFGHJKLMN") for _ in range(3)), f"{i:04d}", f"09{rng.randint(10**7, 10**8 - 1)}")
             for i in range(3000)])
        db.conn.executemany(
            "INSERT INTO wash_records(plate_part1, plate_part2, amount, wash_date, note) VALUES(?, ?, 300, '2026-01-01', '')",
            [(r[0], r[1]) for r in db.conn.execute("SELECT part1, part2 FROM plate_info")])
    from app.ui.main_window import MainWindow
    win = MainWindow(db)
    win.resize(1280, 760)
    win.show()
    qapp.processEvents()
    t = time.perf_counter()
    win.customers_page.refresh()
    qapp.processEvents()
    elapsed = time.perf_counter() - t
    assert win.customers_page.table.rowCount() >= 2900
    assert elapsed < 1.5, f"customer list took {elapsed:.2f}s for 3,000 rows (budget 1.5s; normal ~0.05s)"
    for t_ in win.findChildren(type(win.customers_page._timer)):
        t_.stop()
    win.close()
    db.close()
