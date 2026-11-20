"""客戶資料: the main screen (search + customer list + actions) and its dialogs.

The search / add / edit / delete flow is the one the owner has memorized from
the old app - keep it:
- search under the list: 車牌查詢 (前半 — 後半) or 電話查詢, filters while typing
- Enter moves to the next box; ESC clears the search and puts the cursor back
- 新增資料 keeps the dialog open after saving so several cars can be entered
- 記錄消費 / 客戶資訊 work on the selected row (double-click = 客戶資訊)
- routine actions confirm with a short fading message, not a popup
- no money on this screen (only in 營收報表 and 客戶資訊)
"""
import datetime as _dt
import os
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal

from app import config
from app.brands import BRANDS, brand_logo
from app.db import Database, DataError, format_phone
from app.ui.style import px, sized
from app.ui.widgets import (Card, Segmented, Tile, ask, button, divider, fill_table, fit_to_screen,
                            fmt_date, fmt_money, label, make_table, warn)

PLATE_RE = QtCore.QRegExp("[A-Za-z0-9]{0,4}")
PHONE_RE = QtCore.QRegExp("[0-9]{0,10}")


def last_visit_text(iso: Optional[str]):
    """('3天前', color) for the 上次來店 column."""
    if not iso:
        return "無紀錄", "#9AA0A6"
    try:  # old backups may contain other date spellings; never crash on them
        days = (_dt.date.today() - _dt.date.fromisoformat(str(iso)[:10].replace("/", "-"))).days
    except ValueError:
        return str(iso), None
    if days <= 0:
        return "今天", "#2F7D50"
    if days == 1:
        return "昨天", None
    return f"{days}天前", ("#B3261E" if days >= 30 else None)


def plate_edit(placeholder: str) -> QtWidgets.QLineEdit:
    e = QtWidgets.QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setValidator(QtGui.QRegExpValidator(PLATE_RE, e))
    e.setMaxLength(config.PLATE_PART_MAX)
    e.setAlignment(QtCore.Qt.AlignCenter)
    e.textEdited.connect(lambda t, w=e: _upper(w, t))
    return e


def _upper(w: QtWidgets.QLineEdit, text: str):
    if text != text.upper():
        pos = w.cursorPosition()
        w.setText(text.upper())
        w.setCursorPosition(pos)


def phone_edit(placeholder: str = "電話號碼") -> QtWidgets.QLineEdit:
    e = QtWidgets.QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setValidator(QtGui.QRegExpValidator(PHONE_RE, e))
    e.setMaxLength(config.PHONE_MAX)
    return e


class SideColumn(QtWidgets.QScrollArea):
    """Vertical-only scroll area that is always exactly as wide as its content
    (so nothing is clipped at any font size); scrolls only on very short windows."""

    def __init__(self, inner: QtWidgets.QWidget):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.setWidget(inner)
        inner.installEventFilter(self)

    def sizeHint(self):
        w = self.widget().minimumSizeHint().width() + self.verticalScrollBar().sizeHint().width()
        return QtCore.QSize(max(w, px(220)), super().sizeHint().height())

    def minimumSizeHint(self):
        return QtCore.QSize(self.sizeHint().width(), 0)

    def eventFilter(self, obj, event):
        if event.type() in (QtCore.QEvent.LayoutRequest, QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            self.updateGeometry()
        return super().eventFilter(obj, event)


class Toast(QtWidgets.QLabel):
    """Short fading status message instead of a popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_text(self, text: str, warn_style: bool = False, ms: int = 2800):
        self.setProperty("role", "toastwarn" if warn_style else "toast")
        self.style().unpolish(self)
        self.style().polish(self)
        self.setText(text)
        self.show()
        self._timer.start(ms)


# ===================================================================== page
class CustomersPage(QtWidgets.QWidget):
    data_changed = pyqtSignal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.mode = "plate"
        outer = QtWidgets.QHBoxLayout(self)
        sized(outer, "setContentsMargins", 20, 16, 20, 16)
        sized(outer, "setSpacing", 16)

        # ---- left: list + search
        card = Card("客戶資料")
        self.toast = Toast()
        card.add_header_widget(self.toast)
        self.count_label = label("", "muted", wrap=False)
        card.add_header_widget(self.count_label)
        # 備註 is rarely used: a narrow column at the end (full text on hover / in 客戶資訊)
        self.table = make_table(["車牌號碼", "電話號碼", "上次來店", "備註"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        self.table.setTextElideMode(QtCore.Qt.ElideRight)
        self.table.itemSelectionChanged.connect(self._show_selected)
        self.table.doubleClicked.connect(lambda _i: self.show_info())
        sized(self.table, "setMinimumHeight", 200)
        card.add(self.table, 1)

        search = QtWidgets.QHBoxLayout()
        sized(search, "setSpacing", 10)
        self.mode_seg = Segmented([("plate", "車牌查詢"), ("phone", "電話查詢")])
        self.mode_seg.changed.connect(self.set_mode)
        search.addWidget(self.mode_seg)
        self.part1 = plate_edit("前半")
        self.dash = label("—", "dash", wrap=False)
        self.part2 = plate_edit("後半")
        self.phone = phone_edit("輸入電話號碼")
        for w in (self.part1, self.part2, self.phone):
            w.setProperty("role", "search")
            sized(w, "setMinimumWidth", 130)
        search.addWidget(self.part1, 2)
        search.addWidget(self.dash)
        search.addWidget(self.part2, 2)
        search.addWidget(self.phone, 4)
        search.addWidget(button("清除", "link", self.reset))
        card.add(search)
        outer.addWidget(card, 1)

        # ---- right: actions
        actions = Card("")
        actions.add(label("目前選擇", "tilecap", wrap=False))
        self.selected_label = label("", "selected", wrap=False)
        self.selected_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        actions.add(self.selected_label)
        for text, role, slot in [("＋ 新增資料", "primary", self.add_customer),
                                 ("修改資料", "big", self.edit_customer),
                                 ("刪除資料", "bigdanger", self.delete_customer)]:
            actions.add(button(text, role, slot))
        actions.add(divider())
        for text, role, slot in [("記錄消費", "action", self.record_wash),
                                 ("客戶資訊", "big", self.show_info)]:
            actions.add(button(text, role, slot))
        actions.lay.addStretch(1)
        outer.addWidget(SideColumn(actions))

        # typing filters the list (after a short pause)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self.refresh)
        for w in (self.part1, self.part2, self.phone):
            w.textChanged.connect(lambda _t: self._timer.start())
            w.installEventFilter(self)
        self.table.installEventFilter(self)
        self.part1.returnPressed.connect(self.part2.setFocus)
        self.table.setWordWrap(False)  # one line per customer (long notes show as a tooltip)
        self.set_mode("plate", focus=False, load=False)  # MainWindow.show_page loads the list

    # ------------------------------------------------------------ search / keys
    def set_mode(self, mode: str, focus: bool = True, load: bool = True):
        self.mode = mode
        self.mode_seg.set_current(mode)
        plate = mode == "plate"
        for w in (self.part1, self.dash, self.part2):
            w.setVisible(plate)
        self.phone.setVisible(not plate)
        for w in (self.part1, self.part2, self.phone):
            w.blockSignals(True)
            w.clear()
            w.blockSignals(False)
        if load:
            self.refresh()
        if focus:
            (self.part1 if plate else self.phone).setFocus()

    def reset(self):
        """ESC / 清除: empty the search and start again."""
        self.set_mode("plate")

    def focus_search(self):
        """Put the cursor back in the search box (after dialogs / tab switches)."""
        (self.part1 if self.mode == "plate" else self.phone).setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape:
            self.reset()
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.reset()
        else:
            super().keyPressEvent(event)

    # ----------------------------------------------------------------- list
    def refresh(self, select_id: Optional[int] = None):
        self._timer.stop()
        if select_id is None:
            select_id = self.selected_id(quiet=True)
        if self.mode == "plate":
            rows = self.db.list_customers(part1=self.part1.text(), part2=self.part2.text())
        else:
            rows = self.db.list_customers(phone=self.phone.text())
        self.rows = rows
        self.table.clearSelection()
        self.table.horizontalHeader().resizeSection(3, px(150))  # narrow, scales with the UI
        fill_table(self.table, [(("★ " if r["vip"] else "") + r["plate"], format_phone(r["phone"]),
                                 last_visit_text(r["last_visit"])[0], r["note"]) for r in rows],
                   row_data=[r["id"] for r in rows], fit_rows=False)
        bold = QtGui.QFont(self.table.font())
        bold.setBold(True)
        selected_row = -1
        for i, r in enumerate(rows):
            self.table.item(i, 0).setFont(bold)
            self.table.item(i, 1).setFont(bold)  # the number they look up to call
            color = last_visit_text(r["last_visit"])[1]
            if color:
                self.table.item(i, 2).setForeground(QtGui.QColor(color))
            if r["note"]:
                self.table.item(i, 3).setToolTip(r["note"])
            if r["id"] == select_id:
                selected_row = i
        if selected_row >= 0:
            self.table.selectRow(selected_row)
            self.table.scrollToItem(self.table.item(selected_row, 0), QtWidgets.QAbstractItemView.PositionAtCenter)
        self._show_selected()
        total = self.db.count_customers()
        self.count_label.setText(f"共 {len(rows):,} 筆" if len(rows) == total
                                 else f"找到 {len(rows):,} 筆（共 {total:,} 筆）")

    def _show_selected(self):
        cid = self.selected_id(quiet=True)
        c = next((r for r in getattr(self, "rows", []) if r["id"] == cid), None) if cid is not None else None
        if c:
            phone = format_phone(c["phone"]) or "（沒有電話）"
            self.selected_label.setText(f"{c['plate']}\n{phone}")
            self.selected_label.setProperty("empty", False)
        else:
            self.selected_label.setText("還沒有選擇\n請點表格中的一行")
            self.selected_label.setProperty("empty", True)
        self.selected_label.style().unpolish(self.selected_label)
        self.selected_label.style().polish(self.selected_label)

    def selected_id(self, quiet: bool = False) -> Optional[int]:
        row = self.table.currentRow()
        if row < 0 or not self.table.selectionModel().hasSelection() or self.table.item(row, 0) is None:
            if not quiet:
                self.toast.show_text("請先在表格中點一下要處理的車", warn_style=True)
            return None
        return self.table.item(row, 0).data(QtCore.Qt.UserRole)

    def selected_customer(self) -> Optional[dict]:
        cid = self.selected_id()
        return self.db.get_customer(cid) if cid is not None else None

    # --------------------------------------------------------------- actions
    def add_customer(self):
        dlg = CustomerDialog(self.db, parent=self)
        dlg.exec_()
        if dlg.saved_ids:
            self.refresh(select_id=dlg.saved_ids[-1])
            self.data_changed.emit()
        self.focus_search()

    def edit_customer(self):
        c = self.selected_customer()
        if not c:
            return
        dlg = CustomerDialog(self.db, customer=c, parent=self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh(select_id=c["id"])
            self.toast.show_text(f"✓ 已修改 {dlg.saved_plate}")
            self.data_changed.emit()
        self.focus_search()

    def delete_customer(self):
        c = self.selected_customer()
        if not c:
            return
        phone = format_phone(c["phone"]) or "（沒有電話）"
        others = [p for p in self.db.plate_phones(c["part1"], c["part2"]) if p["id"] != c["id"]]
        if others:
            keep = "、".join(format_phone(p["phone"]) or "（沒有電話）" for p in others)
            text = (f"要刪除 {c['plate']} 的電話 {phone} 嗎？\n\n"
                    f"只會刪除這個號碼。\n這台車的其他電話（{keep}）和消費紀錄都會保留。")
        else:
            text = (f"確定要刪除這筆資料嗎？\n\n車牌：{c['plate']}\n電話：{phone}\n\n"
                    f"這台車的消費紀錄會保留在營收報表裡。")
        if ask(self, text, "刪除資料", yes="確定刪除", no="不要刪除"):
            self.db.delete_customer(c["id"])
            self.refresh()
            self.toast.show_text(f"已刪除 {c['plate']} {phone}")
            self.data_changed.emit()
        self.focus_search()

    def record_wash(self):
        c = self.selected_customer()
        if not c:
            return
        dlg = WashDialog(self.db, c, parent=self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh(select_id=c["id"])
            self.toast.show_text(f"✓ {c['plate']} 已記錄 {fmt_money(dlg.amount)}")
            self.data_changed.emit()
        self.focus_search()

    def show_info(self):
        c = self.selected_customer()
        if not c:
            return
        CustomerInfoDialog(self.db, c, parent=self).exec_()
        self.refresh(select_id=c["id"])
        self.data_changed.emit()
        self.focus_search()


# ============================================================== brand chips
class BrandGrid(QtWidgets.QWidget):
    """Optional brand choice: logo chips that wrap (no sideways scrolling).
    Click a chip to choose it, click it again to clear."""

    def __init__(self, parent=None, max_columns: int = 6):
        super().__init__(parent)
        self.max_columns = max_columns
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        sized(self.grid, "setSpacing", 8)
        self.buttons = []
        for name, _file in BRANDS:
            b = button(name, "brand")
            b.setCheckable(True)
            logo = brand_logo(name)
            if logo:
                b.setIcon(QtGui.QIcon(logo))
                b.setIconSize(QtCore.QSize(28, 28))
            b.clicked.connect(lambda checked, btn=b: self._clicked(btn, checked))
            b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            self.buttons.append(b)
        self.columns = 0
        self._relayout()

    def _clicked(self, btn, checked):
        for b in self.buttons:
            if b is not btn:
                b.setChecked(False)

    def _relayout(self):
        cell = max(b.sizeHint().width() for b in self.buttons) + self.grid.spacing()
        width = self.width() if self.width() > 50 else 700
        cols = max(2, min(self.max_columns, width // max(cell, 1)))
        if cols == self.columns:
            return
        self.columns = cols
        for b in self.buttons:
            self.grid.removeWidget(b)
        for i, b in enumerate(self.buttons):
            self.grid.addWidget(b, i // cols, i % cols)
        for c in range(self.max_columns):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            self.columns = 0
            QtCore.QTimer.singleShot(0, self._relayout)

    def brand(self) -> str:
        for b in self.buttons:
            if b.isChecked():
                return b.text()
        return ""

    def set_brand(self, name: str):
        for b in self.buttons:
            b.setChecked(b.text() == name)


# ======================================================== add / edit dialog
class CustomerDialog(QtWidgets.QDialog):
    """新增資料 (stays open for the next car after saving) / 修改資料."""

    def __init__(self, db: Database, customer: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.saved_ids = []
        self.saved_plate = ""
        editing = customer is not None
        self.setWindowTitle("修改資料" if editing else "新增資料")

        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 20, 16, 20, 16)
        sized(lay, "setSpacing", 14)
        card = Card("修改資料" if editing else "新增資料")
        self.status = Toast()
        card.add_header_widget(self.status)

        body = QtWidgets.QWidget()
        form = QtWidgets.QGridLayout(body)
        form.setContentsMargins(0, 0, 10, 0)
        sized(form, "setHorizontalSpacing", 16)
        sized(form, "setVerticalSpacing", 16)
        form.setColumnStretch(1, 1)

        def key(t):
            lb = label(t, "field", wrap=False)
            sized(lb, "setMinimumWidth", 90)
            return lb

        form.addWidget(key("車牌號碼"), 0, 0)
        plate_row = QtWidgets.QHBoxLayout()
        self.part1 = plate_edit("前半")
        self.part2 = plate_edit("後半")
        plate_row.addWidget(self.part1, 1)
        plate_row.addWidget(label("—", "dash", wrap=False))
        plate_row.addWidget(self.part2, 1)
        plate_row.addStretch(1)
        form.addLayout(plate_row, 0, 1)
        form.addWidget(key("電話號碼"), 1, 0)
        phone_row = QtWidgets.QHBoxLayout()
        self.phone = phone_edit("可不填")
        sized(self.phone, "setMaximumWidth", 420)
        phone_row.addWidget(self.phone, 1)
        if editing:
            phone_row.addWidget(label("換號碼：直接改成新的號碼", "muted", wrap=False))
        phone_row.addStretch(1)
        form.addLayout(phone_row, 1, 1)
        form.addWidget(key("備註"), 2, 0)
        self.note = QtWidgets.QLineEdit()
        self.note.setPlaceholderText("可不填")
        form.addWidget(self.note, 2, 1)
        form.addWidget(divider(), 3, 0, 1, 2)
        brand_head = QtWidgets.QHBoxLayout()
        brand_head.addWidget(label("車輛品牌", "field", wrap=False))
        brand_head.addWidget(label("可不選；再點一次可以取消", "muted", wrap=False))
        brand_head.addStretch(1)
        form.addLayout(brand_head, 4, 0, 1, 2)
        self.brands = BrandGrid()
        form.addWidget(self.brands, 5, 0, 1, 2)
        form.setRowStretch(6, 1)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidget(body)
        card.add(scroll, 1)
        lay.addWidget(card, 1)

        row = QtWidgets.QHBoxLayout()
        self.cancel_btn = button("取消", slot=self.reject)
        row.addWidget(self.cancel_btn)
        row.addStretch(1)
        ok = button("確定", "primary", self.save)
        sized(ok, "setMinimumWidth", 220)
        row.addWidget(ok)
        lay.addLayout(row)

        if editing:
            self.part1.setText(customer["part1"])
            self.part2.setText(customer["part2"])
            self.phone.setText(customer["phone"])
            self.note.setText(customer["note"])
            self.brands.set_brand(customer["brand"])
        self.part1.setFocus()
        fit_to_screen(self, 900, 780)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            focus = self.focusWidget()
            order = [self.part1, self.part2, self.phone, self.note]
            if focus in order[:-1]:
                order[order.index(focus) + 1].setFocus()
            else:
                self.save()
        elif event.key() == QtCore.Qt.Key_Escape:
            empty = not any(w.text() for w in (self.part1, self.part2, self.phone, self.note))
            if self.customer is not None or empty:
                self.reject()  # editing: ESC backs out without touching the customer
            else:
                self.clear()  # adding: ESC empties the form (as in the old app)
        else:
            super().keyPressEvent(event)

    def clear(self):
        for w in (self.part1, self.part2, self.phone, self.note):
            w.clear()
        self.brands.set_brand("")
        self.part1.setFocus()

    def save(self):
        p1, p2, phone = self.part1.text(), self.part2.text(), self.phone.text()
        note, brand = self.note.text(), self.brands.brand()
        try:
            if self.customer is None:
                if (self.db.plate_exists(p1, p2) and not self.db.plate_phone_exists(p1, p2, phone)
                        and p1 and p2):
                    existing = "、".join(format_phone(x["phone"]) or "（沒有電話）"
                                         for x in self.db.plate_phones(p1, p2))
                    if not ask(self, f"車牌 {p1.upper()}-{p2.upper()} 已經有電話：{existing}\n\n"
                                     f"要再加一個電話號碼嗎？\n（舊的號碼會保留；不用的號碼可以之後刪除）",
                               "這台車已經有資料", yes="加這個號碼", no="不要"):
                        self.phone.setFocus()  # keep what was typed; usually the phone needs fixing
                        self.phone.selectAll()
                        return
                cid = self.db.add_customer(p1, p2, phone, note, brand)
                self.saved_ids.append(cid)
                self.saved_plate = f"{p1.upper()}-{p2.upper()}"
                self.status.show_text(f"✓ 已新增 {self.saved_plate}，可以繼續輸入下一台")
                self.cancel_btn.setText("關閉")
                self.clear()
            else:
                self.db.update_customer(self.customer["id"], p1, p2, phone, note, brand)
                self.saved_plate = f"{p1.upper()}-{p2.upper()}"
                self.accept()
        except DataError as e:
            warn(self, str(e))


# ============================================================ 記錄消費 dialog
class WashDialog(QtWidgets.QDialog):
    def __init__(self, db: Database, customer: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.amount = 0
        self.setWindowTitle("記錄消費")
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 20, 16, 20, 16)
        sized(lay, "setSpacing", 14)
        card = Card("記錄消費")
        head = QtWidgets.QHBoxLayout()
        head.addWidget(label(customer["plate"], "plate", wrap=False))
        head.addStretch(1)
        head.addWidget(label(f"日期：今天 {fmt_date(_dt.date.today().isoformat())}", "muted", wrap=False))
        card.add(head)
        card.add(label("洗車類型", "field", wrap=False))
        types = QtWidgets.QHBoxLayout()
        self.type_group = QtWidgets.QButtonGroup(self)
        for i, name in enumerate(config.WASH_TYPES):
            b = button(name, "item")
            b.setCheckable(True)
            b.setChecked(i == 0)
            self.type_group.addButton(b)
            types.addWidget(b, 1)
        card.add(types)
        card.add(label("消費金額", "field", wrap=False))
        amt = QtWidgets.QHBoxLayout()
        self.amount_edit = QtWidgets.QLineEdit()
        self.amount_edit.setPlaceholderText("例如 300")
        self.amount_edit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{0,7}"), self.amount_edit))
        amt.addWidget(self.amount_edit, 1)
        amt.addWidget(label("元", "muted", wrap=False))
        card.add(amt)
        card.add(label("備註（可不填）", "field", wrap=False))
        self.note_edit = QtWidgets.QLineEdit()
        self.note_edit.setPlaceholderText("例如 打蠟、內裝清潔")
        card.add(self.note_edit)
        card.lay.addStretch(1)
        lay.addWidget(card, 1)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(button("取消", slot=self.reject))
        row.addStretch(1)
        ok = button("確定", "primary", self.save)
        sized(ok, "setMinimumWidth", 220)
        row.addWidget(ok)
        lay.addLayout(row)
        self.amount_edit.setFocus()
        fit_to_screen(self, 760, 600)

    def wash_type(self) -> str:
        b = self.type_group.checkedButton()
        return b.text() if b else config.WASH_TYPES[0]

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self.focusWidget() is self.amount_edit:
                self.note_edit.setFocus()
            else:
                self.save()
        else:
            super().keyPressEvent(event)  # ESC closes, as before

    def save(self):
        if not self.amount_edit.text().strip():
            self.amount_edit.setFocus()
            warn(self, "請輸入金額。")
            return
        extra = self.note_edit.text().strip()
        note = f"{self.wash_type()} - {extra}" if extra else self.wash_type()
        try:
            self.db.add_wash(self.customer["part1"], self.customer["part2"], self.amount_edit.text(), None, note)
        except DataError as e:
            warn(self, str(e))
            return
        self.amount = int(self.amount_edit.text())
        self.accept()


# ============================================================ 客戶資訊 dialog
class CustomerInfoDialog(QtWidgets.QDialog):
    def __init__(self, db: Database, customer: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.c = customer
        self.setWindowTitle("客戶資訊")
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 20, 16, 20, 16)
        sized(lay, "setSpacing", 14)

        top = Card("")
        head = QtWidgets.QHBoxLayout()
        head.addWidget(label(customer["plate"], "plate", wrap=False))
        self.vip_badge = label("★ VIP", "badge", wrap=False)
        head.addWidget(self.vip_badge)
        head.addStretch(1)
        self.vip_btn = button("", slot=self.toggle_vip)
        head.addWidget(self.vip_btn)
        top.add(head)
        phones = [format_phone(p["phone"]) for p in db.plate_phones(customer["part1"], customer["part2"]) if p["phone"]]
        details = [f"電話 {'、'.join(phones)}" if phones else "沒有電話"]
        if customer["brand"]:
            details.append(customer["brand"])
        if customer["note"]:
            details.append(f"備註：{customer['note']}")
        top.add(label("　·　".join(details), "muted"))
        tiles = QtWidgets.QHBoxLayout()
        sized(tiles, "setSpacing", 10)
        self.t_total, self.t_visits = Tile("累計消費"), Tile("來店次數")
        self.t_last, self.t_avg = Tile("上次來店"), Tile("平均消費")
        for t in (self.t_total, self.t_visits, self.t_last, self.t_avg):
            tiles.addWidget(t, 1)
        top.add(tiles)
        lay.addWidget(top)

        hist = Card("消費紀錄")
        hist.add_header_widget(button("刪除選取的消費", "danger", self.delete_wash))
        self.table = make_table(["日期", "金額", "項目 / 備註"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        sized(self.table, "setMinimumHeight", 160)
        hist.add(self.table, 1)
        hist.add(label("金額打錯時：先點一下那一筆，再按「刪除選取的消費」，然後重新記錄。", "hint"))
        lay.addWidget(hist, 1)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        close = button("關閉", "primary", self.accept)
        sized(close, "setMinimumWidth", 220)
        close.setDefault(True)  # Enter closes; never toggles VIP by accident
        row.addWidget(close)
        lay.addLayout(row)
        self.load()
        close.setFocus()
        fit_to_screen(self, 980, 760)

    def load(self):
        c = self.db.get_customer(self.c["id"]) or self.c
        self.vip = c["vip"]
        self.vip_badge.setVisible(self.vip)
        self.vip_btn.setText("取消 VIP" if self.vip else "☆ 設為 VIP")
        s = self.db.customer_summary(c["part1"], c["part2"])
        self.t_total.set(fmt_money(s["total"]))
        self.t_visits.set(f"{s['visits']} 次")
        self.t_avg.set(fmt_money(s["avg"]) if s["visits"] else "—")
        self.t_last.set(last_visit_text(s["last_visit"])[0])
        washes = self.db.customer_washes(c["part1"], c["part2"])
        fill_table(self.table, [(fmt_date(w["wash_date"]), fmt_money(w["amount"]), w["note"]) for w in washes],
                   right=(1,), row_data=[w["id"] for w in washes])

    def toggle_vip(self):
        self.db.set_vip(self.c["id"], not self.vip)
        self.load()

    def delete_wash(self):
        row = self.table.currentRow()
        if row < 0 or not self.table.selectionModel().hasSelection():
            warn(self, "請先在消費紀錄中點一下要刪除的那一筆。")
            return
        wid = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        text = f"{self.table.item(row, 0).text()}　{self.table.item(row, 1).text()}　{self.table.item(row, 2).text()}"
        if ask(self, f"確定要刪除這筆消費嗎？\n\n{text}", "刪除消費", yes="確定刪除", no="不要刪除"):
            self.db.delete_wash(wid)
            self.load()
