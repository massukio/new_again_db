"""Render every page and dialog to PNG (offscreen) for visual checks.

Usage: NEWAGAIN_DATA_DIR=<dir with data> QT_QPA_PLATFORM=offscreen python tools/screenshot.py <out_dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5 import QtWidgets  # noqa: E402

from app import config  # noqa: E402
from app.db import Database  # noqa: E402


def main(out):
    os.makedirs(out, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    from app.ui.customers import CustomerDialog, CustomerInfoDialog
    from app.ui.main_window import MainWindow
    db = Database(config.db_path())
    win = MainWindow(db)
    win.show()

    def settle():
        for _ in range(4):
            app.processEvents()

    for w, h in [(1070, 540), (1280, 760), (1920, 1040), (800, 480)]:
        win.resize(w, h)
        settle()
        win.apply_font_size()
        for i in range(len(win.pages)):
            win.show_page(i)
            settle()
            win.grab().save(os.path.join(out, f"{w}x{h}_page{i}.png"))
    win.resize(1280, 760)
    settle()
    win.apply_font_size()
    win.show_page(0)
    page = win.customers_page
    page.table.selectRow(0)
    settle()
    win.grab().save(os.path.join(out, "main_selected.png"))
    for b in page.charge.items.buttons[:2]:
        b.setChecked(True)
    page.charge.amount.setText("1050")
    settle()
    win.grab().save(os.path.join(out, "main_charge.png"))
    page.charge.clear()
    page.part1.setText("A")
    page.refresh()
    settle()
    win.grab().save(os.path.join(out, "main_search.png"))
    page.reset()
    cust = db.list_customers()
    busiest = max(cust, key=lambda c: db.customer_summary(c["part1"], c["part2"])["visits"]) if cust else None
    for name, make in [("add", lambda: CustomerDialog(db, parent=win)),
                       ("edit", lambda: CustomerDialog(db, customer=busiest, parent=win)),
                       ("info", lambda: CustomerInfoDialog(db, busiest, parent=win))]:
        if busiest is None and name != "add":
            continue
        d = make()
        d.show()
        settle()
        d.grab().save(os.path.join(out, f"{name}.png"))
        d.close()
    print("saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
