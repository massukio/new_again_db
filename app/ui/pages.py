"""營收報表 / 備份還原 / 設定 pages."""
import datetime as _dt
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate, pyqtSignal

from app import backup, config
from app.db import Database, DataError
from app.ui.items import ItemManager
from app.ui.style import sized
from app.ui.widgets import (Card, Segmented, Tile, ask, button, fill_table, fmt_date, fmt_money, info,
                            label, make_table, warn)


def documents_dir() -> str:
    path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation)
    return path or os.path.expanduser("~")


def scrollable(inner: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
    sa = QtWidgets.QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QtWidgets.QFrame.NoFrame)
    sa.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    sa.setWidget(inner)
    return sa


def page_layout(widget, kind=QtWidgets.QVBoxLayout):
    lay = kind(widget)
    sized(lay, "setContentsMargins", 20, 16, 20, 16)
    sized(lay, "setSpacing", 16)
    return lay


class Page(QtWidgets.QWidget):
    data_changed = pyqtSignal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db

    def refresh(self):
        pass


# =================================================================== 營收報表
class ReportPage(Page):
    MODES = [("day", "今日"), ("week", "本週"), ("month", "本月"), ("year", "今年")]
    RECORD_LIMIT = 300

    def __init__(self, db, parent=None):
        super().__init__(db, parent)
        self.mode = "month"
        self.anchor = QDate.currentDate()
        self.follows_today = True
        inner = QtWidgets.QWidget()
        lay = page_layout(inner)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(scrollable(inner))

        bar = Card("")
        row = QtWidgets.QHBoxLayout()
        sized(row, "setSpacing", 10)
        self.seg = Segmented(self.MODES)
        self.seg.changed.connect(self._set_mode)
        row.addWidget(self.seg)
        row.addSpacing(16)
        self.prev_btn = button("‹ 前一天", slot=lambda: self._step(-1))
        self.period = label("", "cardtitle", wrap=False)
        self.period.setAlignment(QtCore.Qt.AlignCenter)
        sized(self.period, "setMinimumWidth", 220)
        self.next_btn = button("後一天 ›", slot=lambda: self._step(1))
        self.now_btn = button("回到今天", "link", self._now)
        for w in (self.prev_btn, self.period, self.next_btn, self.now_btn):
            row.addWidget(w)
        row.addStretch(1)
        bar.add(row)
        lay.addWidget(bar)

        tiles = QtWidgets.QHBoxLayout()
        sized(tiles, "setSpacing", 16)
        self.tiles = {}
        for key, cap in [("total", "總營收"), ("visits", "消費筆數"), ("cars", "來店車輛"), ("avg", "平均每筆")]:
            card = Card("", margins=12)
            t = Tile(cap)
            t.setStyleSheet("background: transparent;")
            card.add(t)
            self.tiles[key] = t
            tiles.addWidget(card, 1)
        lay.addLayout(tiles)

        tables = QtWidgets.QHBoxLayout()
        sized(tables, "setSpacing", 16)
        self.break_card = Card("每日明細")
        self.t_break = make_table(["日期", "筆數", "金額"])
        hh = self.t_break.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        sized(self.t_break, "setMinimumHeight", 260)
        self.break_card.add(self.t_break, 1)
        tables.addWidget(self.break_card, 2)
        rec_card = Card("消費紀錄")
        self.rec_note = label("", "muted", wrap=False)
        rec_card.add_header_widget(self.rec_note)
        self.t_rec = make_table(["日期", "車牌號碼", "金額", "項目 / 備註"])
        hh = self.t_rec.horizontalHeader()
        for c in (0, 1, 2):
            hh.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        sized(self.t_rec, "setMinimumHeight", 260)
        rec_card.add(self.t_rec, 1)
        tables.addWidget(rec_card, 3)
        lay.addLayout(tables, 1)
        self.seg.set_current(self.mode)
        self._sync_labels()

    def _range(self):
        d = self.anchor
        if self.mode == "day":
            return d, d
        if self.mode == "week":
            start = d.addDays(1 - d.dayOfWeek())  # Monday
            return start, start.addDays(6)
        if self.mode == "month":
            return QDate(d.year(), d.month(), 1), QDate(d.year(), d.month(), d.daysInMonth())
        return QDate(d.year(), 1, 1), QDate(d.year(), 12, 31)

    def _set_mode(self, mode):
        self.mode = mode
        self.seg.set_current(mode)
        self._sync_labels()
        self.refresh()

    def _sync_labels(self):
        unit, now = {"day": ("天", "今天"), "week": ("週", "本週"),
                     "month": ("個月", "本月"), "year": ("年", "今年")}[self.mode]
        prefix = "前" if self.mode == "day" else "上"
        nxt = "後" if self.mode == "day" else "下"
        self.prev_btn.setText(f"‹ {prefix}一{unit}")
        self.next_btn.setText(f"{nxt}一{unit} ›")
        self.now_btn.setText(f"回到{now}")

    def _step(self, n):
        self.follows_today = False
        if self.mode == "day":
            self.anchor = self.anchor.addDays(n)
        elif self.mode == "week":
            self.anchor = self.anchor.addDays(7 * n)
        elif self.mode == "month":
            self.anchor = self.anchor.addMonths(n)
        else:
            self.anchor = self.anchor.addYears(n)
        self.refresh()

    def _now(self):
        self.anchor = QDate.currentDate()
        self.follows_today = True
        self.refresh()

    def refresh(self):
        if self.follows_today:
            self.anchor = QDate.currentDate()
        start, end = self._range()
        today = QDate.currentDate()
        self.now_btn.setVisible(not (start <= today <= end))
        if self.mode == "day":
            self.period.setText(fmt_date(start.toString("yyyy-MM-dd")))
        elif self.mode == "week":
            self.period.setText(f"{start.toString('yyyy/MM/dd')} ～ {end.toString('MM/dd')}")
        elif self.mode == "month":
            self.period.setText(f"{start.year()} 年 {start.month()} 月")
        else:
            self.period.setText(f"{start.year()} 年")
        a, b = start.toString("yyyy-MM-dd"), end.toString("yyyy-MM-dd")
        bucket = "month" if self.mode == "year" else "day"
        r = self.db.report(a, b, bucket)
        self.tiles["total"].set(fmt_money(r["total"]))
        self.tiles["visits"].set(f"{r['visits']:,} 筆")
        self.tiles["cars"].set(f"{r['cars']:,} 台")
        self.tiles["avg"].set(fmt_money(round(r["total"] / r["visits"])) if r["visits"] else "—")
        self.break_card.setVisible(self.mode != "day")
        self.break_card.title.setText("每月明細" if bucket == "month" else "每日明細")
        self.t_break.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("月份" if bucket == "month" else "日期"))
        fill_table(self.t_break, [
            (f"{x['period'][5:7].lstrip('0')} 月" if bucket == "month" else fmt_date(x["period"])[5:],
             f"{x['visits']:,}", fmt_money(x["total"])) for x in r["buckets"]], right=(1, 2))
        recs = self.db.report_records(a, b, self.RECORD_LIMIT)
        fill_table(self.t_rec, [(x["wash_date"][5:].replace("-", "/"), x["plate"], fmt_money(x["amount"]), x["note"])
                                for x in recs], right=(2,))
        self.rec_note.setText(f"只顯示最新 {self.RECORD_LIMIT} 筆" if r["visits"] > self.RECORD_LIMIT else "")


# =================================================================== 備份還原
class BackupPage(Page):
    restored = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(db, parent)
        inner = QtWidgets.QWidget()
        lay = page_layout(inner)

        actions = QtWidgets.QHBoxLayout()
        sized(actions, "setSpacing", 16)
        b_card = Card("備份資料")
        b_card.add(label("把全部資料存成一個備份檔。建議存到隨身碟或雲端硬碟（例如 Google 雲端硬碟、"
                         "OneDrive）。電腦壞掉時，可以在新電腦用這個檔案把資料救回來。", "hint"))
        self.last_backup = label("", "info")
        b_card.add(self.last_backup)
        b_card.lay.addStretch(1)
        b_card.add(button("備份資料（存成檔案）", "primary", self._backup))
        actions.addWidget(b_card, 1)

        r_card = Card("從備份檔還原")
        r_card.add(label("換新電腦或資料不見時使用。選擇以前存的備份檔，目前電腦上的資料會被備份檔的內容取代。", "hint"))
        r_card.add(label("舊版程式做的備份檔（.db 或 .sql）也可以還原。還原前，程式會自動先把目前的資料另存一份。", "hint"))
        r_card.lay.addStretch(1)
        r_card.add(button("選擇備份檔並還原", slot=self._restore))
        actions.addWidget(r_card, 1)
        lay.addLayout(actions)

        loc = Card("資料存放位置")
        loc.add_header_widget(button("打開資料夾", "link", self._open_folder))
        self.location = label("", "hint")
        self.location.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        loc.add(self.location)
        lay.addWidget(loc)
        lay.addStretch(1)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(scrollable(inner))

    def refresh(self):
        last = self.db.get_setting("last_manual_backup")
        if last:
            self.last_backup.setText(f"上次備份：{last}\n{self.db.get_setting('last_manual_backup_path', '')}")
        else:
            self.last_backup.setText("還沒有備份過，建議現在備份一次。")
        self.location.setText(
            f"資料檔：{self.db.path}\n"
            f"每天開啟程式時會自動備份到：{config.auto_backup_dir()}（保留最近 {config.AUTO_BACKUP_KEEP} 天）\n"
            f"目前共有 {self.db.count_customers():,} 筆客戶資料、{self.db.count_washes():,} 筆消費紀錄。")

    def _backup(self):
        name = f"{config.MANUAL_BACKUP_PREFIX}{_dt.datetime.now():%Y%m%d_%H%M}.db"
        start = self.db.get_setting("last_manual_backup_dir") or documents_dir()
        if not os.path.isdir(start):
            start = documents_dir()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "選擇備份檔要存在哪裡（可選隨身碟）", os.path.join(start, name), "備份檔 (*.db)")
        if not path:
            return
        if not path.lower().endswith(".db"):
            path += ".db"
        try:
            self.db.backup_to(path)
            Database.check_backup_file(path)
        except DataError as e:
            warn(self, f"備份失敗！\n\n{e}\n\n請確認隨身碟有插好，或換一個位置再試一次。")
            return
        self.db.set_setting("last_manual_backup", _dt.datetime.now().strftime("%Y/%m/%d %H:%M"))
        self.db.set_setting("last_manual_backup_path", path)
        self.db.set_setting("last_manual_backup_dir", os.path.dirname(path))
        self.refresh()
        info(self, f"備份成功！\n\n備份檔存在：\n{path}", "備份成功")

    def _restore(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "選擇要還原的備份檔", self.db.get_setting("last_manual_backup_dir") or documents_dir(),
            "備份檔 (*.db *.sql);;所有檔案 (*.*)")
        if not path:
            return
        try:
            counts = Database.check_backup_file(path)
        except DataError as e:
            warn(self, str(e))
            return
        if not ask(self,
                   f"這個備份檔裡有 {counts['customers']:,} 筆客戶資料、{counts['washes']:,} 筆消費紀錄。\n\n"
                   f"還原後，目前電腦上的 {self.db.count_customers():,} 筆客戶資料、"
                   f"{self.db.count_washes():,} 筆消費紀錄會被取代。\n\n確定要還原嗎？",
                   "還原資料", yes="確定還原", no="取消"):
            return
        try:
            safety = backup.safety_backup_before_restore(self.db, config.auto_backup_dir())
            self.db.restore_from(path)
        except (OSError, DataError) as e:
            warn(self, f"還原失敗！\n\n{e}")
            return
        self.refresh()
        self.restored.emit()
        info(self, f"還原成功！目前共有 {self.db.count_customers():,} 筆客戶資料。\n\n"
                   f"（原本的資料已另存在：{safety}）", "還原成功")

    def _open_folder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.dirname(self.db.path)))


# ======================================================================= 設定
class SettingsPage(Page):
    font_size_changed = pyqtSignal(str)

    def __init__(self, db, parent=None):
        super().__init__(db, parent)
        inner = QtWidgets.QWidget()
        cols = page_layout(inner, QtWidgets.QHBoxLayout)
        font_card = Card("字體大小")
        font_card.add(label("字體會跟著視窗大小自動調整。覺得太小或太大，可以在這裡再調整。", "hint"))
        self.font_seg = Segmented([(n, n) for n in config.FONT_SCALES])
        self.font_seg.changed.connect(self.font_size_changed.emit)
        fs = QtWidgets.QHBoxLayout()
        fs.addWidget(self.font_seg)
        fs.addStretch(1)
        font_card.add(fs)
        left = QtWidgets.QVBoxLayout()
        sized(left, "setSpacing", 16)
        left.addWidget(font_card)
        items_card = Card("服務項目")  # same items as the chips in 記錄消費
        self.items = ItemManager(db)
        items_card.add(self.items)
        left.addWidget(items_card)
        left.addStretch(1)
        cols.addLayout(left, 3)

        about_card = Card("關於本程式")
        about = QtWidgets.QLabel(
            f"{config.APP_NAME}\n"
            f"版本：{config.APP_VERSION}（{config.APP_RELEASE_DATE}）\n"
            f"作者：{config.APP_AUTHOR}\n"
            f"建立年份：{config.APP_CREATED_YEAR}\n"
            f"授權：{config.APP_LICENSE}\n"
            f"Copyright © {config.APP_CREATED_YEAR} {config.APP_AUTHOR}\n\n"
            f"本程式以 MIT 授權釋出，詳見：\n{config.APP_LICENSE_URL}")
        about.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        about.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        about_card.add(about)
        right = QtWidgets.QVBoxLayout()
        right.addWidget(about_card)
        right.addStretch(1)
        cols.addLayout(right, 2)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(scrollable(inner))

    def refresh(self):
        self.font_seg.set_current(self.font_size_name())
        self.items.refresh()

    def font_size_name(self) -> str:
        name = self.db.get_setting("font_size")
        return name if name in config.FONT_SCALES else config.DEFAULT_FONT_SIZE
