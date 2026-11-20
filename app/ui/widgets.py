"""Reusable elder-friendly widgets: cards, tiles, message boxes, date picker, item grid."""
from typing import Iterable, List, Optional

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDate, pyqtSignal

from app.ui.style import sized

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


# ------------------------------------------------------------------ basics
def set_role(widget: QtWidgets.QWidget, role: str) -> QtWidgets.QWidget:
    widget.setProperty("role", role)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    return widget


class WrapLabel(QtWidgets.QLabel):
    """Word-wrapped label that always reserves enough height for all its lines."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setWordWrap(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

    def _fit(self):
        if self.width() <= 0:
            return
        h = self.heightForWidth(self.width())
        if h > 0 and h != self.minimumHeight():
            self.setMinimumHeight(h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def setText(self, text):
        super().setText(text)
        QtCore.QTimer.singleShot(0, self._fit)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            QtCore.QTimer.singleShot(0, self._fit)


def label(text: str, role: Optional[str] = None, wrap: Optional[bool] = None) -> QtWidgets.QLabel:
    if wrap is None:
        wrap = role in ("hint", "muted", "info", "empty")
    lb = WrapLabel(text) if wrap else QtWidgets.QLabel(text)
    if role:
        lb.setProperty("role", role)
    return lb


def button(text: str, role: Optional[str] = None, slot=None) -> QtWidgets.QPushButton:
    b = QtWidgets.QPushButton(text)
    if role:
        b.setProperty("role", role)
    b.setCursor(QtCore.Qt.PointingHandCursor)
    b.setFocusPolicy(QtCore.Qt.NoFocus if role in ("item", "nav", "seg", "link") else QtCore.Qt.StrongFocus)
    if slot is not None:
        b.clicked.connect(slot)
    return b


def divider() -> QtWidgets.QFrame:
    f = QtWidgets.QFrame()
    f.setProperty("role", "divider")
    return f


class Card(QtWidgets.QFrame):
    """White rounded panel with an optional title row (title + right-side widgets)."""

    def __init__(self, title: str = "", parent=None, margins: int = 20, spacing: int = 14):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.lay = QtWidgets.QVBoxLayout(self)
        sized(self.lay, "setContentsMargins", margins, margins - 4, margins, margins - 4)
        sized(self.lay, "setSpacing", spacing)
        self.header = QtWidgets.QHBoxLayout()
        self.header.setSpacing(8)
        self.title = label(title, "cardtitle")
        self.header.addWidget(self.title)
        self.header.addStretch(1)
        self.lay.addLayout(self.header)
        if not title:
            self.title.hide()

    def add_header_widget(self, w: QtWidgets.QWidget):
        self.header.addWidget(w)
        return w

    def add(self, w, stretch: int = 0):
        if isinstance(w, QtWidgets.QLayout):
            self.lay.addLayout(w, stretch)
        else:
            self.lay.addWidget(w, stretch)
        return w


class Tile(QtWidgets.QFrame):
    """Small stat tile: caption on top, big value below."""

    def __init__(self, caption: str, parent=None):
        super().__init__(parent)
        self.setProperty("role", "tile")
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 14, 10, 14, 10)
        lay.setSpacing(2)
        self.caption = label(caption, "tilecap")
        self.value = label("", "tileval")
        lay.addWidget(self.caption)
        lay.addWidget(self.value)
        lay.addStretch(1)

    def set(self, value: str):
        self.value.setText(value)


class Segmented(QtWidgets.QFrame):
    """Pill-shaped segmented control. Emits the key of the chosen option."""

    changed = pyqtSignal(str)

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.setProperty("role", "segbar")
        lay = QtWidgets.QHBoxLayout(self)
        sized(lay, "setContentsMargins", 4, 4, 4, 4)
        lay.setSpacing(4)
        self.group = QtWidgets.QButtonGroup(self)
        self.buttons = {}
        for key, text in options:
            b = button(text, "seg")
            b.setCheckable(True)
            b.clicked.connect(lambda _c, k=key: self.changed.emit(k))
            self.group.addButton(b)
            self.buttons[key] = b
            lay.addWidget(b)

    def set_current(self, key: str):
        """Highlight one option; an unknown key (e.g. "") clears the highlight."""
        self.group.setExclusive(False)  # exclusive groups refuse to uncheck the last button
        for k, b in self.buttons.items():
            b.setChecked(k == key)
        self.group.setExclusive(True)


def fit_to_screen(dialog: QtWidgets.QWidget, width: int, height: int):
    """Size a dialog to (width, height) but never larger than the screen it is on."""
    parent = dialog.parentWidget()
    screen = (parent.screen() if parent is not None and hasattr(parent, "screen") else None) \
        or QtWidgets.QApplication.primaryScreen()
    avail = screen.availableGeometry()
    w = min(width, int(avail.width() * 0.96))
    h = min(height, int(avail.height() * 0.92))
    dialog.resize(w, h)
    dialog.move(avail.x() + (avail.width() - w) // 2, avail.y() + (avail.height() - h) // 2)


def fmt_date(iso: str) -> str:
    d = QDate.fromString(iso, "yyyy-MM-dd")
    if not d.isValid():
        return iso
    return f"{d.toString('yyyy/MM/dd')} ({WEEKDAYS[d.dayOfWeek() - 1]})"


def fmt_money(n) -> str:
    try:
        return f"${int(n):,}"
    except (TypeError, ValueError):
        return ""


# ----------------------------------------------------------------- messages
def _box(parent, icon, title, text, buttons):
    box = QtWidgets.QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    created = []
    for t, r in buttons:
        b = box.addButton(t, r)
        b.setCursor(QtCore.Qt.PointingHandCursor)
        created.append(b)
    box.setDefaultButton(created[-1])
    box.exec_()
    return created.index(box.clickedButton()) if box.clickedButton() in created else -1


def info(parent, text: str, title: str = "完成") -> None:
    _box(parent, QtWidgets.QMessageBox.Information, title, text,
         [("知道了", QtWidgets.QMessageBox.AcceptRole)])


def warn(parent, text: str, title: str = "請注意") -> None:
    _box(parent, QtWidgets.QMessageBox.Warning, title, text,
         [("知道了", QtWidgets.QMessageBox.AcceptRole)])


def ask(parent, text: str, title: str = "請確認", yes: str = "是", no: str = "否") -> bool:
    return _box(parent, QtWidgets.QMessageBox.Question, title, text,
                [(no, QtWidgets.QMessageBox.RejectRole),
                 (yes, QtWidgets.QMessageBox.AcceptRole)]) == 1


def ask_text(parent, title: str, prompt: str, text: str = "") -> Optional[str]:
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle(title)
    lay = QtWidgets.QVBoxLayout(dlg)
    sized(lay, "setContentsMargins", 24, 20, 24, 20)
    lay.setSpacing(16)
    lay.addWidget(label(prompt, "field", wrap=True))
    edit = QtWidgets.QLineEdit(text)
    sized(edit, "setMinimumWidth", 420)
    lay.addWidget(edit)
    row = QtWidgets.QHBoxLayout()
    row.addStretch(1)
    row.addWidget(button("取消", slot=dlg.reject))
    row.addWidget(button("確定", "primary", dlg.accept))
    lay.addLayout(row)
    edit.returnPressed.connect(dlg.accept)
    edit.selectAll()
    if dlg.exec_() == QtWidgets.QDialog.Accepted:
        return edit.text().strip()
    return None


# -------------------------------------------------------------- date picking
class CalendarDialog(QtWidgets.QDialog):
    def __init__(self, parent, date: QDate):
        super().__init__(parent)
        self.setWindowTitle("選擇日期")
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 20, 16, 20, 16)
        self.cal = QtWidgets.QCalendarWidget()
        self.cal.setLocale(QtCore.QLocale(QtCore.QLocale.Chinese, QtCore.QLocale.Taiwan))
        self.cal.setGridVisible(False)
        self.cal.setFirstDayOfWeek(QtCore.Qt.Sunday)
        self.cal.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self.cal.setSelectedDate(date)
        sized(self.cal, "setMinimumSize", 520, 380)
        self.cal.activated.connect(lambda _d: self.accept())
        lay.addWidget(self.cal, 1)
        lay.addWidget(label("點一下日期，再按「確定」。", "hint"))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(button("今天", slot=lambda: self.cal.setSelectedDate(QDate.currentDate())))
        row.addStretch(1)
        row.addWidget(button("取消", slot=self.reject))
        row.addWidget(button("確定", "primary", self.accept))
        lay.addLayout(row)

    def selected(self) -> QDate:
        return self.cal.selectedDate()


class DatePicker(QtWidgets.QWidget):
    """[‹ 前一天] [2026/11/20 (五)] [後一天 ›] [今天]"""

    changed = pyqtSignal(str)

    def __init__(self, parent=None, show_today: bool = True):
        super().__init__(parent)
        self._date = QDate.currentDate()
        self.follows_today = True  # False once the user picks another day
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        prev = button("◀", "date", lambda: self.pick(self._date.addDays(-1)))
        prev.setToolTip("前一天")
        lay.addWidget(prev)
        self.btn = button("", "date", self._pick)
        self.btn.setToolTip("點一下可以從月曆選日期")
        lay.addWidget(self.btn)
        nxt = button("▶", "date", lambda: self.pick(self._date.addDays(1)))
        nxt.setToolTip("後一天")
        lay.addWidget(nxt)
        if show_today:
            lay.addWidget(button("今天", "link", lambda: self.pick(QDate.currentDate())))
        lay.addStretch(1)
        self._refresh()

    def _pick(self):
        dlg = CalendarDialog(self, self._date)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.pick(dlg.selected())

    def pick(self, d: QDate):
        """A date chosen by the user."""
        self.follows_today = d == QDate.currentDate()
        self.set_date(d)

    def roll_to_today(self):
        """Called periodically: keep showing today across midnight unless the user chose a day."""
        if self.follows_today and self._date != QDate.currentDate():
            self.set_date(QDate.currentDate())

    def _refresh(self):
        self.btn.setText(fmt_date(self.iso()))

    def set_date(self, d):
        if isinstance(d, str):
            d = QDate.fromString(d, "yyyy-MM-dd")
        if not d.isValid() or d == self._date:
            return
        self._date = d
        self._refresh()
        self.changed.emit(self.iso())

    def iso(self) -> str:
        return self._date.toString("yyyy-MM-dd")


class OptionalDateButton(QtWidgets.QPushButton):
    """A date button that can also be empty ("不限")."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date: Optional[QDate] = None
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.clicked.connect(self._pick)
        sized(self, "setMinimumWidth", 220)
        self._refresh()

    def _pick(self):
        dlg = CalendarDialog(self, self._date or QDate.currentDate())
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.set_date(dlg.selected())

    def _refresh(self):
        self.setText(fmt_date(self.iso()) if self._date else "不限")

    def set_date(self, d: Optional[QDate], emit: bool = True):
        self._date = d if (d is not None and d.isValid()) else None
        self._refresh()
        if emit:
            self.changed.emit()

    def iso(self) -> Optional[str]:
        return self._date.toString("yyyy-MM-dd") if self._date else None


# ------------------------------------------------------------------ item grid
class ItemGrid(QtWidgets.QWidget):
    """Big toggle chips, one per service item. Right-click a chip to rename / delete it."""

    rename_requested = pyqtSignal(int, str)
    delete_requested = pyqtSignal(int, str)

    def __init__(self, parent=None, max_columns: int = 5):
        super().__init__(parent)
        self.max_columns = max_columns
        self.columns = 3
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        sized(self.grid, "setSpacing", 10)
        self.buttons: List[QtWidgets.QPushButton] = []

    def set_items(self, items: Iterable[dict], keep_selection: bool = True):
        selected = set(self.selected_ids()) if keep_selection else set()
        for b in self.buttons:
            self.grid.removeWidget(b)
            b.hide()
            b.setParent(None)
            b.deleteLater()
        self.buttons = []
        for it in items:
            b = button(it["name"], "item")
            b.setCheckable(True)
            b.setProperty("item_id", it["id"])
            b.setProperty("item_name", it["name"])
            b.toggled.connect(lambda on, btn=b: self._decorate(btn))
            b.setChecked(it["id"] in selected)
            self._decorate(b)
            b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            b.setToolTip("按右鍵可以改名或刪除")
            b.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, btn=b: self._menu(btn, pos))
            self.buttons.append(b)
        self._relayout(force=True)

    def _best_columns(self) -> int:
        if not self.buttons:
            return self.columns
        cell = max(w.sizeHint().width() for w in self.buttons) + self.grid.spacing()
        width = self.width() if self.width() > 50 else 700
        return max(2, min(self.max_columns, width // max(cell, 1)))

    def _relayout(self, force: bool = False):
        cols = self._best_columns()
        if cols == self.columns and not force:
            return
        self.columns = cols
        for w in self.buttons:
            self.grid.removeWidget(w)
        for i, w in enumerate(self.buttons):
            self.grid.addWidget(w, i // cols, i % cols)
            w.show()
        for c in range(self.max_columns):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)

    def _menu(self, btn, pos):
        iid, name = btn.property("item_id"), btn.property("item_name")
        menu = QtWidgets.QMenu(self)
        menu.addAction(f"修改「{name}」的名稱", lambda: self.rename_requested.emit(iid, name))
        menu.addAction(f"刪除「{name}」", lambda: self.delete_requested.emit(iid, name))
        menu.exec_(btn.mapToGlobal(pos))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def changeEvent(self, event):  # font size changed via stylesheet
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            QtCore.QTimer.singleShot(0, lambda: self._relayout(force=True))

    @staticmethod
    def _decorate(b: QtWidgets.QPushButton):
        name = b.property("item_name")
        b.setText(f"✓ {name}" if b.isChecked() else name)

    def selected_ids(self) -> List[int]:
        return [b.property("item_id") for b in self.buttons if b.isChecked()]

    def set_selected(self, ids: Iterable[int]):
        ids = set(ids)
        for b in self.buttons:
            b.setChecked(b.property("item_id") in ids)

    def clear(self):
        self.set_selected([])


# ---------------------------------------------------------------------- tables
def make_table(headers: List[str]) -> QtWidgets.QTableWidget:
    t = QtWidgets.QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    t.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.setFocusPolicy(QtCore.Qt.NoFocus)
    t.setFrameShape(QtWidgets.QFrame.NoFrame)
    t.verticalHeader().setVisible(False)
    sized(t.verticalHeader(), "setDefaultSectionSize", 46)
    t.horizontalHeader().setHighlightSections(False)
    t.horizontalHeader().setResizeContentsPrecision(300)  # measure column widths from a sample of rows
    t.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    t.setWordWrap(True)
    t.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
    return t


def table_item(text: str, data=None, align_right: bool = False) -> QtWidgets.QTableWidgetItem:
    it = QtWidgets.QTableWidgetItem(text)
    if data is not None:
        it.setData(QtCore.Qt.UserRole, data)
    it.setTextAlignment((QtCore.Qt.AlignRight if align_right else QtCore.Qt.AlignLeft)
                        | QtCore.Qt.AlignVCenter)
    return it


def fill_table(table: QtWidgets.QTableWidget, rows, right=(), row_data=None,
               fit_rows: bool = True) -> None:
    """Fill a table in one go. Column auto-sizing is paused while filling,
    otherwise Qt re-measures whole columns after every cell (very slow)."""
    hh = table.horizontalHeader()
    modes = [hh.sectionResizeMode(c) for c in range(table.columnCount())]
    for c in range(table.columnCount()):
        hh.setSectionResizeMode(c, QtWidgets.QHeaderView.Fixed)
    table.setUpdatesEnabled(False)
    try:
        table.clearContents()
        table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            for c, v in enumerate(values):
                data = row_data[r] if (row_data is not None and c == 0) else None
                table.setItem(r, c, table_item(v, data, align_right=c in right))
    finally:
        for c, m in enumerate(modes):
            hh.setSectionResizeMode(c, m)
        table.setUpdatesEnabled(True)
    if fit_rows:  # skip for one-line rows: measuring every row is slow on big tables
        table.resizeRowsToContents()
