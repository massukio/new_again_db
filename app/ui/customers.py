"""客戶資料: the main screen (search + customer list + actions) and its dialogs.

The search / add / edit / delete flow is the one the owner has memorized from
the old app - keep it:
- search under the list: 車牌查詢 (前半 — 後半) or 電話查詢, filters while typing
- Enter moves to the next box; ESC clears the search and puts the cursor back
- 新增資料 keeps the dialog open after saving so several cars can be entered
- 記錄消費 happens in the right-hand panel for the selected row: tap service
  items, type the amount, 儲存消費 (a search that finds one car selects it)
- 客戶資訊 works on the selected row (double-click = 客戶資訊)
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
from app.ui.items import ItemManagerDialog, add_item_flow, delete_item_flow, rename_item_flow
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


class FlowLayout(QtWidgets.QLayout):
    """Lays widgets out left-to-right and wraps to the next line, like words."""

    def __init__(self, parent=None, spacing: int = 8):
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtCore.QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for it in self._items:
            size = size.expandedTo(it.minimumSize())
        return size

    def _do_layout(self, rect, apply):
        x, y, line_h = rect.x(), rect.y(), 0
        sp = px(self._spacing)
        for it in self._items:
            hint = it.sizeHint()
            if x + hint.width() > rect.right() + 1 and line_h > 0:
                x, y, line_h = rect.x(), y + line_h + sp, 0
            if apply:
                it.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), hint))
            x += hint.width() + sp
            line_h = max(line_h, hint.height())
        return y + line_h - rect.y()


class ChipFlow(QtWidgets.QWidget):
    """Service item chips, each as wide as its name, wrapping like words.
    Same API as ItemGrid (set_items / selected_ids / set_selected / clear, right-click
    rename / delete) so the item flows are shared."""

    rename_requested = pyqtSignal(int, str)
    delete_requested = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.flow = FlowLayout(self)
        self.buttons = []
        sp = self.sizePolicy()
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)

    def set_items(self, items, keep_selection: bool = True):
        selected = set(self.selected_ids()) if keep_selection else set()
        for b in self.buttons:
            self.flow.removeWidget(b)
            b.hide()
            b.setParent(None)
            b.deleteLater()
        self.buttons = []
        for it in items:
            b = button(it["name"], "chip")
            b.setCheckable(True)
            b.setProperty("item_id", it["id"])
            b.setProperty("item_name", it["name"])
            b.setChecked(it["id"] in selected)
            b.setToolTip("按右鍵可以改名或刪除")
            b.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, btn=b: self._menu(btn, pos))
            self.flow.addWidget(b)
            self.buttons.append(b)
        self.updateGeometry()

    def _menu(self, btn, pos):
        iid, name = btn.property("item_id"), btn.property("item_name")
        menu = QtWidgets.QMenu(self)
        menu.addAction(f"修改「{name}」的名稱", lambda: self.rename_requested.emit(iid, name))
        menu.addAction(f"刪除「{name}」", lambda: self.delete_requested.emit(iid, name))
        menu.exec_(btn.mapToGlobal(pos))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow.heightForWidth(width)

    def sizeHint(self):
        w = self.width() if self.width() > 50 else px(300)
        return QtCore.QSize(px(300), self.heightForWidth(w))

    def minimumSizeHint(self):
        return QtCore.QSize(px(120), self.heightForWidth(self.width() if self.width() > 50 else px(300)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()  # new width -> new height; let the scroll area know

    def changeEvent(self, event):  # font size changed via stylesheet
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            QtCore.QTimer.singleShot(0, self.updateGeometry)

    def selected_ids(self):
        return [b.property("item_id") for b in self.buttons if b.isChecked()]

    def set_selected(self, ids):
        ids = set(ids)
        for b in self.buttons:
            b.setChecked(b.property("item_id") in ids)

    def clear(self):
        self.set_selected([])


class CustomerModel(QtCore.QAbstractTableModel):
    """Customer list data for a QTableView. Only the visible rows are ever drawn,
    so refreshing 3,000 customers costs the same as refreshing 15."""

    HEADERS = ["車牌號碼", "電話號碼", "上次來店", "備註"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.cells = []
        self._colors = {}

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.cells = []
        for r in rows:
            text, color = last_visit_text(r["last_visit"])
            self.cells.append((r["plate"], format_phone(r["phone"]), text, r["note"], color))
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.cells)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else 4

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            return self.cells[r][c]
        if role == QtCore.Qt.UserRole:
            return self.rows[r]["id"]
        if role == QtCore.Qt.ForegroundRole and c == 2 and self.cells[r][4]:
            color = self.cells[r][4]
            return self._colors.setdefault(color, QtGui.QBrush(QtGui.QColor(color)))
        if role == QtCore.Qt.ToolTipRole and c == 3 and self.cells[r][3]:
            return self.cells[r][3]
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.HEADERS[section]
        return None


class _BoldColumns(QtWidgets.QStyledItemDelegate):
    """Plate and phone in bold - derived from the view's (stylesheet) font, so it
    follows the 小/中/大/特大 and window-size scaling automatically."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() < 2:
            option.font.setBold(True)


class CustomerTable(QtWidgets.QTableView):
    """The customer list. Columns 0-2 are sized once from the longest values
    (cheap); 備註 takes the rest. Never use per-cell items here (slow on Windows)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_ = CustomerModel(self)
        self.setModel(self.model_)
        self.setItemDelegate(_BoldColumns(self))
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setTextElideMode(QtCore.Qt.ElideRight)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setVisible(False)
        sized(self.verticalHeader(), "setDefaultSectionSize", 46)
        hh = self.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        for c in (0, 1, 2):
            hh.setSectionResizeMode(c, QtWidgets.QHeaderView.Fixed)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

    def set_rows(self, rows):
        self.model_.set_rows(rows)
        self.fit_columns()

    def fit_columns(self):
        """Width of plate / phone / last visit = their longest value (measured on a
        handful of the longest strings, not on every row)."""
        bold = QtGui.QFont(self.font())
        bold.setBold(True)
        header_fm = QtGui.QFontMetrics(self.horizontalHeader().font())
        pad = px(34)
        for c in (0, 1, 2):
            fm = QtGui.QFontMetrics(bold if c < 2 else self.font())
            texts = sorted({cells[c] for cells in self.model_.cells}, key=len, reverse=True)[:12]
            width = max([fm.horizontalAdvance(t) for t in texts] +
                        [header_fm.horizontalAdvance(CustomerModel.HEADERS[c])])
            self.horizontalHeader().resizeSection(c, width + pad)

    def changeEvent(self, event):  # font size changed via stylesheet
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            QtCore.QTimer.singleShot(0, self.fit_columns)

    # small helpers used by the page, tools and tests
    def rowCount(self):
        return self.model_.rowCount()

    def cell_text(self, row, col):
        return self.model_.cells[row][col]

    def row_id(self, row):
        return self.model_.rows[row]["id"]

    def row_rect(self, row):
        return self.visualRect(self.model_.index(row, 0))


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
        self.rows = []
        outer = QtWidgets.QHBoxLayout(self)
        sized(outer, "setContentsMargins", 20, 16, 20, 16)
        sized(outer, "setSpacing", 16)

        # ---- left: list (actions in its title row) + search
        card = Card("")  # the 客戶資料 tab already names this page; keep the room for the buttons
        self.count_label = label("", "muted", wrap=False)
        card.header.insertWidget(0, self.count_label)
        self.toast = Toast()
        card.header.insertWidget(1, self.toast)
        for text, role, slot in [("＋ 新增", "primary", self.add_customer),
                                 ("修改", None, self.edit_customer),
                                 ("刪除", "danger", self.delete_customer),
                                 ("客戶資訊", None, self.show_info)]:
            b = button(text, role, slot)
            if role == "primary":
                b.setProperty("role", "primarysmall")
            card.add_header_widget(b)

        # plate / phone / last visit always fully visible; 備註 (rarely used) gets what is left
        self.table = CustomerTable()
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._selection_changed())
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
            sized(w, "setMinimumWidth", 110)
        search.addWidget(self.part1, 2)
        search.addWidget(self.dash)
        search.addWidget(self.part2, 2)
        search.addWidget(self.phone, 4)
        search.addWidget(button("清除", "link", self.reset))
        card.add(search)
        outer.addWidget(card, 3)

        # ---- right: quick 記錄消費 for the selected car
        self.charge = ChargePanel(db)
        self.charge.saved.connect(self._charged)
        self.charge.items_changed.connect(self.data_changed.emit)
        outer.addWidget(self.charge, 2)

        self._timer = QtCore.QTimer(self)  # filter after a short pause in typing
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)  # short pause: the list is cheap to refresh now
        self._timer.timeout.connect(lambda: self.refresh(auto_pick=True))
        for w in (self.part1, self.part2, self.phone):
            w.textChanged.connect(lambda _t: self._timer.start())
            w.installEventFilter(self)
        self.table.installEventFilter(self)
        self.part1.returnPressed.connect(self.part2.setFocus)
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
            self.focus_search()

    def reset(self):
        """ESC / 清除: empty the search and start again."""
        self.set_mode("plate")

    def focus_search(self):
        """Put the cursor back in the search box (after dialogs / saving / tab switches)."""
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

    def _searching(self) -> bool:
        return bool(self.part1.text() or self.part2.text() or self.phone.text())

    # ----------------------------------------------------------------- list
    def refresh(self, select_id: Optional[int] = None, auto_pick: bool = False, force: bool = True):
        """Reload the list. force=False (tab switches) skips it when neither the
        search nor the data changed since the last load."""
        self._timer.stop()
        key = (self.mode, self.part1.text(), self.part2.text(), self.phone.text(), self.db.conn.total_changes)
        if not force and key == getattr(self, "_loaded_key", None):
            return
        self._loaded_key = key
        if select_id is None:
            select_id = self.selected_id(quiet=True)
        if self.mode == "plate":
            rows = self.db.list_customers(part1=self.part1.text(), part2=self.part2.text())
        else:
            rows = self.db.list_customers(phone=self.phone.text())
        self.rows = rows
        if auto_pick and len(rows) == 1 and self._searching():
            select_id = rows[0]["id"]  # a search that finds one car selects it: ready to charge
        self.table.blockSignals(True)
        self.table.selectionModel().blockSignals(True)
        self.table.set_rows(rows)
        selected_row = next((i for i, r in enumerate(rows) if r["id"] == select_id), -1)
        if selected_row >= 0:
            self.table.selectRow(selected_row)
            self.table.scrollTo(self.table.model_.index(selected_row, 0),
                                QtWidgets.QAbstractItemView.PositionAtCenter)
        self.table.selectionModel().blockSignals(False)
        self.table.blockSignals(False)
        self._selection_changed()
        total = self.db.count_customers()
        self.count_label.setText(f"共 {len(rows):,} 筆" if len(rows) == total
                                 else f"找到 {len(rows):,} 筆（共 {total:,} 筆）")

    def _selection_changed(self):
        cid = self.selected_id(quiet=True)
        self.charge.set_customer(next((r for r in self.rows if r["id"] == cid), None) if cid else None)

    def selected_id(self, quiet: bool = False) -> Optional[int]:
        sel = self.table.selectionModel().selectedRows()
        row = sel[0].row() if sel else -1
        if row < 0 or row >= self.table.rowCount():
            if not quiet:
                self.toast.show_text("請先在表格中點一下要處理的車", warn_style=True)
            return None
        return self.table.row_id(row)

    def selected_customer(self) -> Optional[dict]:
        cid = self.selected_id()
        return self.db.get_customer(cid) if cid is not None else None

    # --------------------------------------------------------------- actions
    def _charged(self, customer: dict, amount: int):
        self.refresh(select_id=customer["id"])
        self.toast.show_text(f"✓ {customer['plate']} 已記錄 {fmt_money(amount)}")
        self.data_changed.emit()
        self.focus_search()

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

    def show_info(self):
        c = self.selected_customer()
        if not c:
            return
        CustomerInfoDialog(self.db, c, parent=self).exec_()
        self.refresh(select_id=c["id"])
        self.data_changed.emit()
        self.focus_search()


# ============================================================ 記錄消費 panel
class ChargePanel(Card):
    """Record a wash for the selected car right on the main screen:
    tap service items, type the amount, 儲存消費."""

    saved = pyqtSignal(dict, int)
    items_changed = pyqtSignal()

    def __init__(self, db: Database, parent=None):
        super().__init__("記錄消費", parent)
        self.db = db
        self.customer = None
        self.who = label("", "chargeplate", wrap=False)
        self.header.insertWidget(1, self.who)

        self.hint = label("請先在左邊點一台車", "empty")
        self.add(self.hint)

        head = QtWidgets.QHBoxLayout()
        head.addWidget(label("服務項目", "field", wrap=False))
        head.addStretch(1)
        head.addWidget(button("＋ 新增項目", "link", self._add_item))
        head.addWidget(button("管理項目", "link", self._manage_items))
        self.add(head)
        self.items = ChipFlow()
        self.items.rename_requested.connect(self._rename_item)
        self.items.delete_requested.connect(self._delete_item)
        holder = QtWidgets.QWidget()
        hl = QtWidgets.QVBoxLayout(holder)
        hl.setContentsMargins(0, 0, 6, 0)
        hl.addWidget(self.items)
        hl.addStretch(1)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        self.add(scroll, 1)

        form = QtWidgets.QGridLayout()
        sized(form, "setHorizontalSpacing", 10)
        sized(form, "setVerticalSpacing", 10)
        form.addWidget(label("金額", "field", wrap=False), 0, 0)
        amt = QtWidgets.QHBoxLayout()
        self.amount = QtWidgets.QLineEdit()
        self.amount.setPlaceholderText("輸入金額")
        self.amount.setProperty("role", "search")
        self.amount.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{0,7}"), self.amount))
        amt.addWidget(self.amount, 1)
        amt.addWidget(label("元", "muted", wrap=False))
        form.addLayout(amt, 0, 1)
        form.addWidget(label("備註", "field", wrap=False), 1, 0)
        self.note = QtWidgets.QLineEdit()
        self.note.setProperty("role", "small")
        self.note.setPlaceholderText("可不填")
        form.addWidget(self.note, 1, 1)
        form.setColumnStretch(1, 1)
        self.add(form)
        self.save_btn = button("儲存消費", "primary", self.save)
        self.add(self.save_btn)
        self.amount.returnPressed.connect(self.note.setFocus)
        self.note.returnPressed.connect(self.save)
        self.reload_items()
        self.set_customer(None)

    # ------------------------------------------------------------------ state
    def set_customer(self, customer: Optional[dict]):
        changed = (customer or {}).get("id") != (self.customer or {}).get("id")
        self.customer = customer
        on = customer is not None
        self.who.setText(customer["plate"] if on else "")
        self.who.setVisible(on)
        self.hint.setVisible(not on)
        for w in (self.items, self.amount, self.note, self.save_btn):
            w.setEnabled(on)
        if changed:
            self.clear()

    def clear(self):
        self.items.clear()
        self.amount.clear()
        self.note.clear()

    def reload_items(self, keep_selection: bool = True):
        self.items.set_items(self.db.list_services(), keep_selection=keep_selection)

    # ------------------------------------------------------------- items
    def _after_items_changed(self, select_id=None):
        selected = self.items.selected_ids() + ([select_id] if select_id else [])
        self.reload_items(keep_selection=False)
        self.items.set_selected(selected)
        self.items_changed.emit()

    def _add_item(self):
        new_id = add_item_flow(self, self.db)
        if new_id is not None:
            self._after_items_changed(new_id if self.customer else None)

    def _rename_item(self, item_id, name):
        if rename_item_flow(self, self.db, item_id, name):
            self._after_items_changed()

    def _delete_item(self, item_id, name):
        if delete_item_flow(self, self.db, item_id, name):
            self._after_items_changed()

    def _manage_items(self):
        dlg = ItemManagerDialog(self.db, self)
        dlg.manager.changed.connect(self._after_items_changed)
        dlg.exec_()

    # ------------------------------------------------------------------ save
    def save(self):
        if self.customer is None:
            return
        if not self.amount.text().strip():
            self.amount.setFocus()
            warn(self, "請輸入金額。")
            return
        names = [b.property("item_name") for b in self.items.buttons if b.isChecked()]
        extra = self.note.text().strip()
        note = "、".join(names)
        if extra:
            note = f"{note} - {extra}" if note else extra
        try:
            self.db.add_wash(self.customer["part1"], self.customer["part2"], self.amount.text(), None, note)
        except DataError as e:
            warn(self, str(e))
            return
        amount = int(self.amount.text())
        customer = self.customer
        self.clear()
        self.saved.emit(customer, amount)


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
        head.addStretch(1)
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
        close.setDefault(True)  # Enter closes the dialog
        row.addWidget(close)
        lay.addLayout(row)
        self.load()
        close.setFocus()
        fit_to_screen(self, 980, 760)

    def load(self):
        c = self.db.get_customer(self.c["id"]) or self.c
        s = self.db.customer_summary(c["part1"], c["part2"])
        self.t_total.set(fmt_money(s["total"]))
        self.t_visits.set(f"{s['visits']} 次")
        self.t_avg.set(fmt_money(s["avg"]) if s["visits"] else "—")
        self.t_last.set(last_visit_text(s["last_visit"])[0])
        washes = self.db.customer_washes(c["part1"], c["part2"])
        fill_table(self.table, [(fmt_date(w["wash_date"]), fmt_money(w["amount"]), w["note"]) for w in washes],
                   right=(1,), row_data=[w["id"] for w in washes])

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
