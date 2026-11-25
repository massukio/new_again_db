"""Make the screenshots of the 使用說明 (assets/manual/*.png), with highlights.

    NEWAGAIN_DATA_DIR=<empty folder> QT_QPA_PLATFORM=offscreen python tools/make_manual.py [out_dir]

Runs the real program on sample data in NEWAGAIN_DATA_DIR (must be empty or a
throw-away folder: sample customers are added). Each picture gets orange boxes with
numbers ①②③ that the text in assets/manual/manual.html refers to. Run it on
Windows for the real fonts (workflows/build-release.md), then check every picture.
"""
import datetime as dt
import os
import random
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: E402

from app import config  # noqa: E402
from app.db import DataError, open_database  # noqa: E402

ORANGE = QtGui.QColor("#E8590C")
SIZE = (1280, 900)  # taller than the reference: same font size, room for every highlighted part


# ------------------------------------------------------------------ drawing
def rect_of(target, root) -> QtCore.QRect:
    if isinstance(target, QtCore.QRect):
        return QtCore.QRect(target)
    if isinstance(target, (list, tuple)):
        r = QtCore.QRect()
        for t in target:
            r = r.united(rect_of(t, root))
        return r
    r = QtCore.QRect(target.mapTo(root, QtCore.QPoint(0, 0)), target.size())
    w = target  # inside a scroll area only the visible part may be boxed
    while w is not None and w is not root:
        area = w.parentWidget()
        if isinstance(area, QtWidgets.QAbstractScrollArea) and w is area.viewport():
            r = r.intersected(QtCore.QRect(w.mapTo(root, QtCore.QPoint(0, 0)), w.size()))
        w = area
    return r


def row_rect(table, row, root) -> QtCore.QRect:
    r = table.visualRect(table.model().index(row, 0))
    left = table.viewport().mapTo(root, QtCore.QPoint(0, r.top()))
    return QtCore.QRect(left, QtCore.QSize(table.viewport().width(), r.height()))


def find_button(root, text):
    for b in root.findChildren(QtWidgets.QPushButton):
        if b.text() == text and b.isVisible():
            return b
    raise LookupError(text)


def settle(app, n=6):
    for _ in range(n):
        app.processEvents()
        QtCore.QThread.msleep(15)


def shot(root, marks, path, crop=None):
    """Grab root, draw a box + number for each (number, target), optionally crop."""
    pm = root.grab()
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    font = QtGui.QFont("Arial")
    font.setPixelSize(22)
    font.setBold(True)
    p.setFont(font)
    radius = 17
    inside = pm.rect().adjusted(3, 3, -3, -3)  # parts that run past the edge: box what is visible
    for number, target in marks:
        r = rect_of(target, root).adjusted(-5, -5, 5, 5).intersected(inside)
        p.setPen(QtGui.QPen(ORANGE, 4))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(r, 10, 10)
    for number, target in marks:  # badges on top of every box
        r = rect_of(target, root).adjusted(-5, -5, 5, 5).intersected(inside)
        cx = min(max(r.left(), radius + 3), pm.width() - radius - 3)
        cy = min(max(r.top(), radius + 3), pm.height() - radius - 3)
        circle = QtCore.QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        p.setPen(QtGui.QPen(QtCore.Qt.white, 3))
        p.setBrush(ORANGE)
        p.drawEllipse(circle)
        p.setPen(QtCore.Qt.white)
        p.drawText(circle, QtCore.Qt.AlignCenter, str(number))
    p.end()
    if crop is not None:
        c = rect_of(crop, root).adjusted(-24, -24, 24, 24).intersected(pm.rect())
        pm = pm.copy(c)
    p = QtGui.QPainter(pm)  # thin frame: the picture must not melt into the white page
    p.setPen(QtGui.QPen(QtGui.QColor("#BDB6AA"), 2))
    p.drawRect(pm.rect().adjusted(1, 1, -1, -1))
    p.end()
    pm.save(path)
    print("saved", os.path.basename(path), pm.width(), "x", pm.height())


# --------------------------------------------------------------- sample data
MENU = [("泡沫外表洗車", 60, (300, 500)), ("基礎洗車打腊（全套）", 20, (750, 1000)),
        ("深層美容式精緻洗車", 6, (1700, 2000)), ("皮椅內裝保養", 5, (300, 350))]


def sample_data(db):
    rng = random.Random(3)
    today = dt.date.today()
    cars = [("ABC", "1234", "0912345678", "老客戶", "Toyota", 14),
            ("ABC", "5678", "0928111222", "", "Honda", 30),
            ("BKA", "0912", "0935222333", "", "Mazda", 21),
            ("RAA", "8888", "0958333444", "公司車", "Ford", 7)]
    while len(cars) < 60:
        p1 = "".join(rng.choice(string.ascii_uppercase) for _ in range(3))
        cars.append((p1, f"{rng.randint(0, 9999):04d}", f"09{rng.randint(10000000, 99999999)}", "",
                     rng.choice(["Toyota", "Honda", "Nissan", "Mitsubishi", "", ""]),
                     rng.choice([7, 14, 21, 30, 60, None])))
    for p1, p2, phone, note, brand, every in cars:
        try:
            db.add_customer(p1, p2, phone, note, brand)
        except DataError:
            continue
        if every is None:
            continue
        d = today - dt.timedelta(days=rng.randint(1, every))
        while d >= today - dt.timedelta(days=200):
            name, _w, (lo, hi) = rng.choices(MENU, weights=[m[1] for m in MENU])[0]
            db.add_wash(p1, p2, rng.randint(lo // 50, hi // 50) * 50, d.isoformat(), name)
            d -= dt.timedelta(days=max(1, every + rng.randint(-3, 5)))
    db.add_customer("ABC", "1234", "0988777666", "", "Toyota")  # a second phone number
    for p1, p2, amount, name in [("RAA", "8888", 450, "泡沫外表洗車"), ("BKA", "0912", 900, "基礎洗車打腊（全套）")]:
        db.add_wash(p1, p2, amount, today.isoformat(), name)
    stamp = today - dt.timedelta(days=3)
    db.set_setting("last_manual_backup", f"{stamp:%Y/%m/%d} 18:30")
    db.set_setting("last_manual_backup_path", f"E:\\再新洗車備份_{stamp:%Y%m%d}_1830.db")


# -------------------------------------------------------------------- shots
def main(out):
    os.makedirs(out, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Chinese, QtCore.QLocale.Taiwan))
    db, _ = open_database(config.db_path())
    if db.count_customers() == 0:
        sample_data(db)
    from app.ui.main_window import MainWindow
    from app.ui.customers import CustomerDialog, CustomerInfoDialog
    from app.ui.items import ItemManagerDialog
    win = MainWindow(db)
    win.resize(*SIZE)
    win.show()
    settle(app)
    win.apply_font_size()
    settle(app)
    o = lambda name: os.path.join(out, name)  # noqa: E731
    page = win.customers_page
    charge = page.charge

    # 1. the whole window
    win.show_page(0)
    settle(app)
    shot(win, [(i + 1, win.group.button(i)) for i in range(4)]
         + [(5, win.help_btn), (6, page.table), (7, charge)], o("overview.png"))

    # 2. 車牌查詢: type the first half
    page.part1.setText("AB")
    page.refresh(auto_pick=True)
    settle(app)
    shot(win, [(1, page.mode_seg), (2, page.part1), (3, page.part2), (4, find_button(page, "清除")),
               (5, page.count_label), (6, page.table)], o("search_plate.png"))

    # 3. 電話查詢
    page.set_mode("phone")
    page.phone.setText("0912")
    page.refresh(auto_pick=True)
    settle(app)
    shot(win, [(1, page.mode_seg.buttons["phone"]), (2, page.phone), (3, row_rect(page.table, 0, win))],
         o("search_phone.png"))
    page.reset()
    settle(app)

    # 4. a car selected: the header buttons
    page.part1.setText("ABC")
    page.part2.setText("1234")
    page.refresh()
    settle(app)
    page.table.selectRow(0)
    settle(app)
    shot(win, [(1, row_rect(page.table, 0, win)), (2, find_button(page, "＋ 新增")), (3, find_button(page, "修改")),
               (4, find_button(page, "刪除")), (5, find_button(page, "客戶資訊"))], o("actions.png"))

    # 5. 記錄消費 for the selected car
    for b in charge.items.buttons[:2]:
        b.setChecked(True)
    charge.amount.setText("900")
    settle(app)
    shot(win, [(1, charge.who), (2, charge.items), (3, charge.amount), (4, charge.note), (5, charge.save_btn),
               (6, [find_button(charge, "＋ 新增項目"), find_button(charge, "管理項目")])], o("charge.png"))
    charge.clear()

    # 6. 新增資料 dialog
    dlg = CustomerDialog(db, parent=win)
    dlg.resize(900, 800)
    dlg.show()
    settle(app)
    dlg.part1.setText("NEW")
    dlg.part2.setText("2026")
    dlg.phone.setText("0911222333")
    dlg.brands.set_brand("Toyota")
    settle(app)
    shot(dlg, [(1, [dlg.part1, dlg.part2]), (2, dlg.phone), (3, dlg.note), (4, dlg.brands),
               (5, find_button(dlg, "確定")), (6, dlg.cancel_btn)], o("add.png"))
    dlg.close()

    # 7. 修改資料 dialog (change the number)
    c = page.selected_customer()
    dlg = CustomerDialog(db, customer=c, parent=win)
    dlg.resize(900, 800)
    dlg.show()
    settle(app)
    shot(dlg, [(1, dlg.phone), (2, find_button(dlg, "確定")), (3, dlg.cancel_btn)], o("edit.png"))
    dlg.close()

    # 8. 客戶資訊
    info = CustomerInfoDialog(db, c, win)
    info.resize(1000, 800)
    info.show()
    settle(app)
    info.table.selectRow(0)
    settle(app)
    shot(info, [(1, [info.t_total, info.t_visits, info.t_last, info.t_avg]), (2, info.table),
                (3, find_button(info, "刪除選取的消費")), (4, find_button(info, "關閉"))], o("info.png"))
    info.close()

    # 9. 管理服務項目
    im = ItemManagerDialog(db, win)
    im.resize(900, 620)
    im.show()
    settle(app)
    im.manager.list.setCurrentRow(1)
    settle(app)
    shot(im, [(1, im.manager.list), (2, find_button(im, "＋ 新增項目")), (3, find_button(im, "改名")),
              (4, [find_button(im, "往上移"), find_button(im, "往下移")]), (5, find_button(im, "刪除項目")),
              (6, find_button(im, "完成"))], o("items_manage.png"))
    im.close()

    # 10. 營收報表
    win.show_page(1)
    r = win.report_page
    r._set_mode("month") if hasattr(r, "_set_mode") else None
    settle(app, 10)
    tiles = [t.parentWidget() for t in r.tiles.values()]
    shot(win, [(1, r.seg), (2, [r.prev_btn, r.period, r.next_btn]), (3, tiles), (4, r.t_break), (5, r.t_rec)],
         o("report.png"))
    r._step(-1)
    settle(app)
    shot(win, [(1, r.now_btn)], o("report_back.png"), crop=[r.seg, r.now_btn])
    r._now()

    # 11. 備份 / 還原
    win.show_page(2)
    b = win.backup_page
    settle(app, 10)
    shot(win, [(1, find_button(b, "備份資料（存成檔案）")), (2, b.last_backup),
               (3, find_button(b, "選擇備份檔並還原")), (4, find_button(b, "打開資料夾"))], o("backup.png"))

    # 12. 設定
    win.show_page(3)
    s = win.settings_page
    settle(app, 10)
    shot(win, [(1, s.font_seg), (2, s.items)], o("settings.png"))
    print("done:", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "manual"))
