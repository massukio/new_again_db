"""Offscreen UI flow tests: the owner's memorized flow must keep working."""
import os

import pytest
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtTest import QTest

from app import config
from app.db import Database


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def env(qapp, tmp_path, monkeypatch):
    monkeypatch.setenv("NEWAGAIN_DATA_DIR", str(tmp_path))
    from app.ui import customers, items, widgets
    answers = {"ask": True, "asked": [], "warned": []}

    def fake_ask(parent, text, *a, **k):
        answers["asked"].append(text)
        return answers["ask"]

    def fake_warn(parent, text, *a, **k):
        answers["warned"].append(text)

    for mod in (customers, items, widgets):  # every module that imported ask/warn
        monkeypatch.setattr(mod, "ask", fake_ask, raising=False)
        monkeypatch.setattr(mod, "warn", fake_warn, raising=False)
    db = Database(config.db_path())
    db.add_customer("ABC", "1234", "0912345678", "老客戶", "Toyota")
    db.add_customer("XYZ", "5555", "0922000111")
    db.add_wash("ABC", "1234", 300, "2026-11-01", "一般洗車")
    from app.ui.main_window import MainWindow
    win = MainWindow(db)
    win.resize(1280, 760)
    win.show()
    qapp.processEvents()
    yield win, win.customers_page, db, answers
    for t in win.findChildren(QtCore.QTimer):  # nothing may fire after the db is closed
        t.stop()
    win.close()
    win.deleteLater()
    qapp.processEvents()
    db.close()


def settle(qapp):
    for _ in range(3):
        qapp.processEvents()


def test_selection_is_visible_and_drives_the_charge_panel(env, qapp):
    win, page, db, _ = env
    assert not page.charge.save_btn.isEnabled() and page.charge.hint.isVisible()
    assert "[role]:disabled" in qapp.styleSheet()  # disabled buttons must look disabled
    rect = page.table.row_rect(1)
    QTest.mouseClick(page.table.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
    settle(qapp)
    assert page.table.selectionModel().isRowSelected(1, QtCore.QModelIndex())
    assert page.charge.who.text() == "XYZ-5555" and page.charge.save_btn.isEnabled()
    assert "item:selected" in qapp.styleSheet() and "background: #0E6E84" in qapp.styleSheet()
    # selection survives a refresh and is still the same customer
    page.refresh()
    assert page.charge.who.text() == "XYZ-5555"


def test_search_one_result_selects_it_and_charge(env, qapp):
    win, page, db, _ = env
    page.set_mode("phone")
    QTest.keyClicks(page.phone, "0922")
    page.refresh(auto_pick=True)  # what the typing pause (debounce timer) calls
    settle(qapp)
    assert page.charge.who.text() == "XYZ-5555"           # found one car -> ready to charge
    ch = page.charge
    names = [b.property("item_name") for b in ch.items.buttons]
    assert names[0] == "泡沫外表洗車"
    ch.items.buttons[0].click()
    ch.items.buttons[5].click()
    QTest.keyClicks(ch.amount, "650")
    ch.amount.setFocus()
    QTest.keyClick(ch.amount, QtCore.Qt.Key_Return)
    ch.note.setText("老客人")  # QTest.keyClicks cannot type Chinese (aborts Qt); set it directly
    ch.save()
    w = db.customer_washes("XYZ", "5555")[0]
    assert w["amount"] == 650 and w["note"] == f"泡沫外表洗車、{names[5]} - 老客人"
    assert page.toast.isVisible() and "已記錄" in page.toast.text()
    assert ch.amount.text() == "" and not ch.items.selected_ids()   # ready for the next car
    assert page.table.cell_text(0, 2) == "今天"
    # amount is required
    ch.save()
    assert db.customer_summary("XYZ", "5555")["visits"] == 1


def test_search_filters_and_esc_resets(env, qapp):
    win, page, db, _ = env
    page.part1.setFocus()
    QTest.keyClicks(page.part1, "ab")
    page.refresh()
    assert page.part1.text() == "AB"  # upper-cased while typing
    assert page.table.rowCount() == 1
    QTest.keyClick(page.part1, QtCore.Qt.Key_Return)
    assert page.part2.hasFocus()
    QTest.keyClick(page.part2, QtCore.Qt.Key_Escape)
    settle(qapp)
    assert page.part1.text() == "" and page.table.rowCount() == 2
    page.set_mode("phone")
    QTest.keyClicks(page.phone, "0922")
    page.refresh()
    assert page.table.rowCount() == 1 and page.table.cell_text(0, 0) == "XYZ-5555"


def test_actions_need_a_selection(env, qapp):
    win, page, db, _ = env
    page.edit_customer()
    assert page.toast.isVisible() and "請先" in page.toast.text()


def test_add_dialog_stays_open_and_rules(env, qapp):
    from app.ui.customers import CustomerDialog
    win, page, db, answers = env
    dlg = CustomerDialog(db, parent=page)
    dlg.show()
    QtWidgets.QApplication.setActiveWindow(dlg)
    for w, t in ((dlg.part1, "new"), (dlg.part2, "1")):
        QTest.keyClicks(w, t)
    dlg.phone.setText("0933")
    dlg.part1.setFocus()
    QTest.keyClick(dlg.part1, QtCore.Qt.Key_Return)
    assert dlg.part2.hasFocus()
    dlg.save()
    assert dlg.isVisible() and dlg.part1.text() == "" and len(dlg.saved_ids) == 1
    assert dlg.cancel_btn.text() == "關閉" and "已新增" in dlg.status.text()
    # same plate + same phone -> refused
    dlg.part1.setText("NEW"); dlg.part2.setText("1"); dlg.phone.setText("0933")
    dlg.save()
    assert answers["warned"] and len(dlg.saved_ids) == 1
    # same plate, other phone -> asks; "不要" keeps what was typed and goes to the phone box
    answers["ask"] = False
    dlg.part1.setText("NEW"); dlg.part2.setText("1"); dlg.phone.setText("0944")
    dlg.save()
    assert answers["asked"] and len(dlg.saved_ids) == 1
    assert dlg.part1.text() == "NEW" and dlg.phone.hasFocus()
    # ...and "加這個號碼" adds the second number
    answers["ask"] = True
    dlg.save()
    assert len(dlg.saved_ids) == 2
    # ESC clears instead of closing (add mode)
    dlg.part1.setText("Q")
    QTest.keyClick(dlg.part1, QtCore.Qt.Key_Escape)
    assert dlg.isVisible() and dlg.part1.text() == ""
    dlg.close()


def test_edit_wash_info_delete(env, qapp):
    from app.ui.customers import CustomerDialog, CustomerInfoDialog
    win, page, db, answers = env
    page.table.selectRow(0)
    c = page.selected_customer()
    assert c["plate"] == "ABC-1234"
    # edit keeps the row selected
    dlg = CustomerDialog(db, customer=c, parent=page)
    dlg.note.setText("改過")
    dlg.save()
    assert dlg.result() == QtWidgets.QDialog.Accepted
    page.refresh(select_id=c["id"])
    assert page.selected_customer()["note"] == "改過"
    # wash via the panel: Enter in the note saves
    page.charge.amount.setText("500")
    QTest.keyClick(page.charge.note, QtCore.Qt.Key_Return)
    assert db.customer_summary("ABC", "1234")["visits"] == 2
    # info: delete a mistaken wash
    info = CustomerInfoDialog(db, c, parent=page)
    info.table.selectRow(0)
    info.delete_wash()
    assert db.customer_summary("ABC", "1234")["visits"] == 1
    info.close()
    # delete customer (confirmed)
    page.table.selectRow(0)
    page.delete_customer()
    assert db.get_customer(c["id"]) is None
    assert page.charge.hint.isVisible() and not page.charge.save_btn.isEnabled()


def test_report_page_and_now_button(env, qapp):
    win, page, db, _ = env
    win.show_page(1)
    rp = win.report_page
    assert not rp.now_btn.isVisible()
    rp._step(-1)
    assert rp.now_btn.isVisible()
    rp._now()
    assert not rp.now_btn.isVisible()


def test_focus_and_escape_rules(env, qapp):
    from app.ui.customers import CustomerDialog, CustomerInfoDialog
    win, page, db, answers = env
    page.table.selectRow(0)
    c = page.selected_customer()
    # ESC in edit backs out and keeps the customer intact
    dlg = CustomerDialog(db, customer=c, parent=page)
    dlg.show()
    QtWidgets.QApplication.setActiveWindow(dlg)
    QTest.keyClick(dlg.part1, QtCore.Qt.Key_Escape)
    assert dlg.result() == QtWidgets.QDialog.Rejected and db.get_customer(c["id"])["plate"] == c["plate"]
    # brand chips cannot take focus (Enter must reach the save logic)
    add = CustomerDialog(db, parent=page)
    assert all(b.focusPolicy() == QtCore.Qt.NoFocus for b in add.brands.buttons)
    assert not any(b.autoDefault() for b in add.findChildren(QtWidgets.QPushButton))
    add.close()
    # 客戶資訊: Enter closes it
    info = CustomerInfoDialog(db, c, parent=page)
    info.show()
    QtWidgets.QApplication.setActiveWindow(info)
    QTest.keyClick(info, QtCore.Qt.Key_Return)
    assert info.result() == QtWidgets.QDialog.Accepted
    # back on the main page the cursor is in the search box
    win.show_page(1)
    win.show_page(0)
    QtWidgets.QApplication.setActiveWindow(win)
    assert page.part1.hasFocus() or QtWidgets.QApplication.focusWidget() in (page.part1, None)


def test_confirm_boxes_default_to_safe_choice(qapp, monkeypatch):
    from app.ui import widgets
    seen = {}

    def fake_exec(box):
        seen["default"] = box.defaultButton().text()
        box.done(0)
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec_", fake_exec)
    widgets.ask(None, "刪除？", yes="確定刪除", no="不要刪除")
    assert seen["default"] == "不要刪除"


def test_items_are_editable_from_the_panel(env, qapp, monkeypatch):
    from app.ui import items
    win, page, db, _ = env
    monkeypatch.setattr(items, "ask_text", lambda *a, **k: "車內除臭")
    monkeypatch.setattr(items, "info", lambda *a, **k: None)
    page.table.selectRow(0)
    page.charge._add_item()
    names = [b.property("item_name") for b in page.charge.items.buttons]
    assert names[-1] == "車內除臭" and page.charge.items.buttons[-1].isChecked()
    sid = page.charge.items.buttons[-1].property("item_id")
    monkeypatch.setattr(items, "ask_text", lambda *a, **k: "除臭殺菌")
    page.charge._rename_item(sid, "車內除臭")
    assert page.charge.items.buttons[-1].property("item_name") == "除臭殺菌"
    page.charge._delete_item(sid, "除臭殺菌")
    assert "除臭殺菌" not in [b.property("item_name") for b in page.charge.items.buttons]


def test_no_vip_marks(env, qapp):
    win, page, db, _ = env
    db.conn.execute("UPDATE plate_info SET vip=1")  # old databases may still have VIP flags
    page.refresh()
    assert all("★" not in page.table.cell_text(i, 0) for i in range(page.table.rowCount()))


def test_selected_chip_keeps_its_size(env, qapp):
    win, page, db, _ = env
    page.table.selectRow(0)
    chip = page.charge.items.buttons[1]
    before_text, before_w = chip.text(), chip.sizeHint().width()
    chip.click()
    qapp.processEvents()
    assert chip.isChecked() and chip.text() == before_text and chip.sizeHint().width() == before_w


def test_items_managed_in_settings_show_in_the_panel(env, qapp, monkeypatch):
    from app.ui import items
    win, page, db, _ = env
    monkeypatch.setattr(items, "ask_text", lambda *a, **k: "引擎室清潔")
    monkeypatch.setattr(items, "info", lambda *a, **k: None)
    win.show_page(3)                                   # 設定
    names = [win.settings_page.items.list.item(i).text() for i in range(win.settings_page.items.list.count())]
    assert names[0] == "泡沫外表洗車" and len(names) == 17
    win.settings_page.items._add()
    win.show_page(0)                                   # back to 客戶資料
    assert "引擎室清潔" in [b.property("item_name") for b in page.charge.items.buttons]


def test_huge_list_is_capped(env, qapp, monkeypatch):
    win, page, db, _ = env
    monkeypatch.setattr(type(page), "MAX_ROWS", 1)
    page.refresh()
    assert page.table.rowCount() == 1 and "只顯示前 1 筆" in page.count_label.text()
    page.part1.setText("XYZ")
    page.refresh()
    assert page.table.rowCount() == 1 and page.count_label.text().startswith("找到 1 筆")


def test_failed_restore_puts_old_data_back(env, qapp, tmp_path, monkeypatch):
    import sqlite3
    from app import db as db_mod
    from app.ui import pages
    win, page, db, _ = env
    other = Database(str(tmp_path / "other.db"))
    other.add_customer("NEW", "0001", "0933000111")
    other.close()
    monkeypatch.setattr(pages.QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(tmp_path / "other.db"), ""))
    monkeypatch.setattr(pages, "ask", lambda *a, **k: True)
    msgs = []
    monkeypatch.setattr(pages, "warn", lambda _p, t, *a, **k: msgs.append(t))
    real, calls = db_mod._create_schema, []

    def flaky(conn):  # the upgrade after the copy fails once
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.IntegrityError("boom")
        real(conn)
    monkeypatch.setattr(db_mod, "_create_schema", flaky)
    win.backup_page._restore()
    assert msgs and "恢復成還原前" in msgs[0]
    assert db.count_customers() == 2


def test_restore_reloads_list_and_clears_chips(env, qapp, tmp_path, monkeypatch):
    from app.ui import pages
    win, page, db, _ = env
    page.table.selectRow(0) if hasattr(page.table, "selectRow") else None
    settle(qapp)
    if page.charge.items.buttons:
        page.charge.items.buttons[0].setChecked(True)
    other = Database(str(tmp_path / "other.db"))
    other.add_customer("NEW", "0001", "0933000111")
    other.close()
    monkeypatch.setattr(pages.QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(tmp_path / "other.db"), ""))
    monkeypatch.setattr(pages, "ask", lambda *a, **k: True)
    monkeypatch.setattr(pages, "info", lambda *a, **k: None)
    win.backup_page._restore()
    win.show_page(0)
    settle(qapp)
    assert [r["plate"] for r in page.rows] == ["NEW-0001"]
    assert page.charge.items.selected_ids() == []


def test_enter_on_focused_cancel_does_not_save(env, qapp):
    from app.ui.customers import CustomerDialog
    win, page, db, _ = env
    before = db.count_customers()
    dlg = CustomerDialog(db, parent=page)
    dlg.show()
    QtWidgets.QApplication.setActiveWindow(dlg)
    dlg.part1.setText("ENT"); dlg.part2.setText("1"); dlg.phone.setText("0955")
    dlg.cancel_btn.setFocus()
    QTest.keyClick(dlg.cancel_btn, QtCore.Qt.Key_Return)
    assert db.count_customers() == before and not dlg.isVisible()


def test_charge_toast_shows_no_money(env, qapp):
    win, page, db, _ = env
    page.table.selectRow(0)
    settle(qapp)
    page.charge.amount.setText("450")
    page.charge.save()
    assert "$" not in page.toast.text() and "450" not in page.toast.text()


def test_restore_drops_selection_and_typed_charge(env, qapp, tmp_path, monkeypatch):
    from app.ui import pages
    win, page, db, _ = env
    page.table.selectRow(0)
    settle(qapp)
    page.charge.amount.setText("999")
    other = Database(str(tmp_path / "other.db"))  # same ids, other cars
    other.add_customer("OTH", "0001", "0933000111")
    other.add_customer("OTH", "0002", "0933000222")
    other.close()
    monkeypatch.setattr(pages.QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(tmp_path / "other.db"), ""))
    monkeypatch.setattr(pages, "ask", lambda *a, **k: True)
    monkeypatch.setattr(pages, "info", lambda *a, **k: None)
    win.backup_page._restore()
    win.show_page(0)
    settle(qapp)
    assert page.charge.customer is None and page.charge.amount.text() == ""
    assert not page.charge.save_btn.isEnabled()


def test_list_rebuilds_on_a_new_day(env, qapp, monkeypatch):
    import datetime as real_dt
    from app.ui import customers
    win, page, db, _ = env
    win.show_page(1)
    calls = []
    orig = page.table.set_rows
    monkeypatch.setattr(page.table, "set_rows", lambda rows: (calls.append(1), orig(rows)))

    import types
    tomorrow = real_dt.date.today() + real_dt.timedelta(days=1)

    class Tomorrow(real_dt.date):
        @classmethod
        def today(cls):
            return tomorrow
    fake = types.SimpleNamespace(**{k: getattr(real_dt, k) for k in dir(real_dt) if not k.startswith("__")})
    fake.date = Tomorrow
    monkeypatch.setattr(customers, "_dt", fake)  # only this module sees tomorrow
    win.show_page(0)
    assert calls  # same search, no data change, but a new day: 「N天前」 must be rebuilt


def test_manual_is_complete():
    """Every picture exists, every link has its target, every page has a chapter."""
    import os
    import re
    from app.ui import manual
    from app.ui.main_window import MainWindow
    html = manual.manual_html()
    names = set(re.findall(r'<a name="([^"]+)"', html))
    for img in manual.image_names(html):
        assert os.path.exists(os.path.join(manual.MANUAL_DIR, img)), img
    for link in re.findall(r'<a href="#([^"]+)"', html):
        assert link in names, link
    assert set(MainWindow.MANUAL_ANCHORS) <= names and "toc" in names


def test_manual_opens_at_the_current_page_and_saves_pdf(env, qapp, tmp_path, monkeypatch):
    from app.ui import manual
    win, page, db, _ = env
    win.resize(1070, 540)
    settle(qapp)
    assert win.header.sizeHint().width() <= win.width()  # no tab or help button cut off
    win.show_page(2)
    win.open_manual()
    dlg = win._manual
    for _ in range(20):
        qapp.processEvents()
        QtCore.QThread.msleep(10)
    assert dlg.isVisible() and not dlg.isModal()
    assert dlg.view.verticalScrollBar().value() > 0  # at chapter 九 (備份), not at the top
    win.open_manual()
    assert win._manual is dlg
    out = tmp_path / "說明.pdf"
    monkeypatch.setattr(manual.QtWidgets.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out), ""))
    monkeypatch.setattr(manual, "ask", lambda *a, **k: False)
    dlg.save_pdf()
    assert out.exists() and out.stat().st_size > 100_000  # text + pictures
    dlg.close()


def test_edit_dialog_shows_the_whole_phone_number(env, qapp):
    from app.ui.customers import CustomerDialog
    win, page, db, _ = env
    win.resize(1280, 900)
    win.apply_font_size()  # the real size for this window (the resize timer has not run yet)
    page.table.selectRow(0)
    settle(qapp)
    dlg = CustomerDialog(db, customer=page.selected_customer(), parent=page)
    dlg.show()
    settle(qapp)
    fm = dlg.phone.fontMetrics()
    assert dlg.phone.width() > fm.horizontalAdvance(dlg.phone.text())
    dlg.close()


def test_chip_grid_relayout_never_runs_after_it_is_gone(qapp):
    """A font change schedules a relayout; closing the window first must not crash."""
    import sys
    from PyQt5 import QtCore, QtWidgets
    from app.ui.widgets import ItemGrid
    errors = []
    old, sys.excepthook = sys.excepthook, lambda *a: errors.append(a[1])
    try:
        holder = QtWidgets.QWidget()
        grid = ItemGrid(holder)
        grid.set_items([{"id": 1, "name": "機油"}, {"id": 2, "name": "電瓶"}])
        holder.setStyleSheet("QPushButton { font-size: 30pt; }")  # like 設定 → 字體大小
        from PyQt5 import sip
        sip.delete(holder)  # the window is gone before the relayout runs
        for _ in range(5):
            qapp.processEvents()
    finally:
        sys.excepthook = old
    assert not errors, errors


def test_release_zip_is_one_folder_with_exe_and_manual(tmp_path):
    """The zip users get: a folder with the exe and ONE html manual (pictures inside)."""
    import importlib.util
    import zipfile
    from app import config as cfg
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("make_release", os.path.join(root, "tools", "make_release.py"))
    mr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr)
    exe = tmp_path / f"{cfg.APP_NAME}.exe"
    exe.write_bytes(b"MZ fake exe")
    out = mr.pack(str(exe), str(tmp_path))
    folder = f"{cfg.APP_NAME}_{cfg.APP_VERSION}"
    with zipfile.ZipFile(out) as z:
        assert z.namelist() == [f"{folder}/{cfg.APP_NAME}.exe", f"{folder}/使用說明書.html"]
        assert all(i.flag_bits & 0x800 for i in z.infolist())  # Chinese names show right in Windows
        html = z.read(f"{folder}/使用說明書.html").decode("utf-8")
    import re
    srcs = re.findall(r'<img src="([^"]+)"', html)
    assert srcs and all(s.startswith("data:image/png;base64,") for s in srcs)  # no outside files needed
    assert '<a name="toc">' in html
