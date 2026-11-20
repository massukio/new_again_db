"""Service item (服務項目) management: add / rename / delete / reorder.

The same flows are used from the entry form (buttons + right-click menu),
the 「管理項目」 dialog. Items are stored permanently in the
database; deleting only hides an item so old records keep its name."""
from typing import Optional

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal

from app.db import Database, DataError
from app.ui.style import sized
from app.ui.widgets import Card, ask, ask_text, button, fit_to_screen, info, label, warn


def add_item_flow(parent, db: Database) -> Optional[int]:
    name = ask_text(parent, "新增項目",
                    "請輸入新的項目名稱：\n（新增後會一直保留，以後不用再新增）")
    if not name:
        return None
    try:
        new_id = db.add_service(name)
    except DataError as e:
        warn(parent, str(e))
        return None
    info(parent, f"已新增「{name}」。\n\n以後每次都會出現在服務項目中。", "新增成功")
    return new_id


def rename_item_flow(parent, db: Database, item_id: int, old_name: str) -> bool:
    name = ask_text(parent, "修改項目名稱", f"「{old_name}」要改成：", old_name)
    if not name or name == old_name:
        return False
    try:
        db.rename_service(item_id, name)
    except DataError as e:
        warn(parent, str(e))
        return False
    return True


def delete_item_flow(parent, db: Database, item_id: int, name: str) -> bool:
    if not ask(parent, f"確定要刪除項目「{name}」嗎？\n\n以前紀錄上的「{name}」不會被刪掉。",
               "刪除項目", yes="確定刪除", no="不要刪除"):
        return False
    db.hide_service(item_id)
    return True


class ItemManager(QtWidgets.QWidget):
    """List of items with 新增 / 改名 / 往上移 / 往下移 / 刪除 buttons."""

    changed = pyqtSignal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(label("先點一下清單中的項目，再按右邊的按鈕。刪除的項目不會影響以前的紀錄。", "hint"))
        row = QtWidgets.QHBoxLayout()
        self.list = QtWidgets.QListWidget()
        sized(self.list, "setMinimumHeight", 300)
        sized(self.list, "setMinimumWidth", 260)
        sized(self.list, "setMaximumWidth", 500)
        self.list.itemDoubleClicked.connect(lambda _i: self._rename())
        row.addWidget(self.list)
        btns = QtWidgets.QVBoxLayout()
        for text, role, slot in [("＋ 新增項目", None, self._add), ("改名", None, self._rename),
                                 ("往上移", None, lambda: self._move(-1)),
                                 ("往下移", None, lambda: self._move(1)),
                                 ("刪除項目", "danger", self._delete)]:
            b = button(text, role, slot)
            sized(b, "setMinimumWidth", 200)
            btns.addWidget(b)
        btns.addStretch(1)
        row.addLayout(btns)
        row.addStretch(1)
        lay.addLayout(row)
        self.refresh()

    def refresh(self, select_id=None):
        if select_id is None and self.list.currentItem():
            select_id = self.list.currentItem().data(QtCore.Qt.UserRole)
        self.list.clear()
        for it in self.db.list_services():
            li = QtWidgets.QListWidgetItem(it["name"])
            li.setData(QtCore.Qt.UserRole, it["id"])
            self.list.addItem(li)
            if it["id"] == select_id:
                self.list.setCurrentItem(li)

    def _current(self):
        li = self.list.currentItem()
        if li is None:
            warn(self, "請先在清單中點一下要處理的項目。")
            return None
        return li.data(QtCore.Qt.UserRole), li.text()

    def _add(self):
        iid = add_item_flow(self, self.db)
        if iid is not None:
            self.refresh(iid)
            self.changed.emit()

    def _rename(self):
        cur = self._current()
        if cur and rename_item_flow(self, self.db, *cur):
            self.refresh(cur[0])
            self.changed.emit()

    def _move(self, delta):
        cur = self._current()
        if cur:
            self.db.move_service(cur[0], delta)
            self.refresh(cur[0])
            self.changed.emit()

    def _delete(self):
        cur = self._current()
        if cur and delete_item_flow(self, self.db, *cur):
            self.refresh()
            self.changed.emit()


class ItemManagerDialog(QtWidgets.QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理服務項目")
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 20, 16, 20, 16)
        card = Card("管理服務項目")
        self.manager = ItemManager(db)
        card.add(self.manager, 1)
        lay.addWidget(card, 1)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(button("完成", "primary", self.accept))
        lay.addLayout(row)
        fit_to_screen(self, 760, 640)
