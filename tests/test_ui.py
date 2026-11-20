"""Offscreen UI flow tests: the owner's memorized flow must keep working."""
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
    rect = page.table.visualItemRect(page.table.item(1, 0))
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
    assert page.table.item(0, 2).text() == "今天"
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
    assert page.table.rowCount() == 1 and page.table.item(0, 0).text() == "XYZ-5555"


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
    # 客戶資訊: Enter closes, VIP untouched
    info = CustomerInfoDialog(db, c, parent=page)
    info.show()
    QtWidgets.QApplication.setActiveWindow(info)
    vip_before = db.get_customer(c["id"])["vip"]
    QTest.keyClick(info, QtCore.Qt.Key_Return)
    assert info.result() == QtWidgets.QDialog.Accepted and db.get_customer(c["id"])["vip"] == vip_before
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
