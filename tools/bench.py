"""Large-database benchmark: QT_QPA_PLATFORM=offscreen python tools/bench.py [--customers 3000] [--washes 100000]"""
import argparse
import datetime as dt
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def timed(label, fn, repeat=3):
    best = None
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        el = time.perf_counter() - t
        best = el if best is None else min(best, el)
    print(f"{label:<40} {best * 1000:8.1f} ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=3000)
    ap.add_argument("--washes", type=int, default=100000)
    args = ap.parse_args()
    folder = tempfile.mkdtemp()
    os.environ["NEWAGAIN_DATA_DIR"] = folder
    from app import config
    from app.db import Database
    db = Database(config.db_path())
    rng = random.Random(5)
    cars = []
    with db.conn:
        for i in range(args.customers):
            p1, p2 = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3)), f"{rng.randint(0, 9999):04d}"
            db.conn.execute("INSERT OR IGNORE INTO plate_info(part1, part2, phone_number, note, brand, vip) "
                            "VALUES(?, ?, ?, '', '', 0)", (p1, p2, f"09{rng.randint(10**7, 10**8 - 1)}"))
            cars.append((p1, p2))
        today = dt.date.today()
        db.conn.executemany(
            "INSERT INTO wash_records(plate_part1, plate_part2, amount, wash_date, note) VALUES(?, ?, ?, ?, '一般洗車')",
            [(*rng.choice(cars), rng.randint(4, 30) * 50, (today - dt.timedelta(days=rng.randint(0, 3650))).isoformat())
             for _ in range(args.washes)])
    db.conn.execute("ANALYZE")
    print(f"{args.customers} customers, {args.washes} washes, {os.path.getsize(db.path) / 1e6:.1f} MB")
    p1, p2 = cars[0]
    y0 = today.replace(month=1, day=1).isoformat()
    print("\n-- data --")
    timed("list all customers (+ last visit)", lambda: db.list_customers())
    timed("search plate front 'AB'", lambda: db.list_customers(part1="AB"))
    timed("search phone '0912'", lambda: db.list_customers(phone="0912"))
    timed("customer summary", lambda: db.customer_summary(p1, p2))
    timed("customer washes", lambda: db.customer_washes(p1, p2))
    timed("report month", lambda: db.report(today.replace(day=1).isoformat(), today.isoformat()))
    timed("report year", lambda: db.report(y0, today.isoformat(), "month"))
    timed("report records (300)", lambda: db.report_records(y0, today.isoformat()))
    print("\n-- UI (offscreen) --")
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    from app.ui.main_window import MainWindow
    t = time.perf_counter()
    win = MainWindow(db)
    win.resize(1280, 760)
    win.show()
    app.processEvents()
    print(f"{'main window startup':<40} {(time.perf_counter() - t) * 1000:8.1f} ms")
    for i, (name, _p) in enumerate(win.pages):
        timed(f"open page: {name}", lambda i=i: (win.show_page(i), app.processEvents()), repeat=2)
    win.show_page(0)
    page = win.customers_page

    def type_search():
        page.reset()
        for ch in p1[:2]:
            page.part1.setText(page.part1.text() + ch)
            app.processEvents()
        page.refresh()
        app.processEvents()
    timed("type 2 plate letters + filter", type_search, repeat=2)
    rp = win.report_page
    win.show_page(1)
    timed("report: switch to year", lambda: (rp._set_mode("year"), app.processEvents()), repeat=2)
    win.close()


if __name__ == "__main__":
    main()
