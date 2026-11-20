"""Time every user interaction on the real widgets (run on the target PC).

Usage: python tools/profile_ui.py [--customers 150] [--washes 2400] [--offscreen]
Each line is the time from the action until Qt has finished processing it
(layout, styling, painting requests). Compare against workflows/performance.md.
"""
import argparse
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=150)
    ap.add_argument("--washes", type=int, default=2400)
    ap.add_argument("--offscreen", action="store_true")
    args = ap.parse_args()
    if args.offscreen:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["NEWAGAIN_DATA_DIR"] = tempfile.mkdtemp()
    from PyQt5 import QtCore, QtWidgets
    from PyQt5.QtTest import QTest
    app = QtWidgets.QApplication(sys.argv)
    from app import config
    from app.db import Database
    db = Database(config.db_path())
    rng = random.Random(3)
    with db.conn:
        db.conn.executemany(
            "INSERT OR IGNORE INTO plate_info(part1, part2, phone_number, note, brand, vip) VALUES(?, ?, ?, ?, '', 0)",
            [("".join(rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ") for _ in range(3)), f"{i:04d}",
              f"09{rng.randint(10**7, 10**8 - 1)}", rng.choice(["", "", "", "公司車"])) for i in range(args.customers)])
        plates = db.conn.execute("SELECT part1, part2 FROM plate_info").fetchall()
        db.conn.executemany(
            "INSERT INTO wash_records(plate_part1, plate_part2, amount, wash_date, note) VALUES(?, ?, 300, ?, '泡沫外表洗車')",
            [(*rng.choice(plates), f"2026-{rng.randint(1, 11):02d}-{rng.randint(1, 28):02d}") for _ in range(args.washes)])

    def settle():
        for _ in range(3):
            app.processEvents()

    def timed(label, fn, repeat=3):
        best = None
        for _ in range(repeat):
            t = time.perf_counter()
            fn()
            settle()
            el = time.perf_counter() - t
            best = el if best is None else min(best, el)
        print(f"{label:<40} {best * 1000:8.1f} ms")

    from app.ui.main_window import MainWindow
    t = time.perf_counter()
    win = MainWindow(db)
    win.resize(1280, 760)
    win.show()
    settle()
    print(f"{args.customers} customers, {args.washes} washes")
    print(f"{'startup (window shown)':<40} {(time.perf_counter() - t) * 1000:8.1f} ms")
    page = win.customers_page
    rows = page.table.rowCount()

    def click_row():
        r = rng.randrange(min(rows, 12))
        rect = page.table.row_rect(r)
        QTest.mouseClick(page.table.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
    timed("click a row", click_row, repeat=5)
    chips = page.charge.items.buttons
    timed("click a service chip", lambda: chips[rng.randrange(len(chips))].click(), repeat=5)

    def type_char():
        page.reset()
        settle()
        page.part1.setText("A")
        page.refresh(auto_pick=True)  # what the typing pause runs
    timed("type a plate letter (filter)", type_char)
    timed("clear search (ESC)", page.reset)

    def save_charge():
        page.table.selectRow(0)
        page.charge.amount.setText("300")
        page.charge.save()
    timed("save a charge (儲存消費)", save_charge)

    def open_info():
        from app.ui.customers import CustomerInfoDialog
        page.table.selectRow(0)
        d = CustomerInfoDialog(db, page.selected_customer(), parent=page)
        d.show()
        settle()
        d.close()
    timed("open 客戶資訊", open_info)
    timed("switch to 營收報表 and back", lambda: (win.show_page(1), settle(), win.show_page(0)))

    def resize():
        win.resize(1200 if win.width() == 1280 else 1280, 760)
        settle()
        win.apply_font_size(force=True)
    timed("resize window (restyle)", resize)
    win.close()


if __name__ == "__main__":
    main()
