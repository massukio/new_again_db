from PyQt5 import QtCore, QtGui, QtWidgets

from app import config
from app.db import Database
from app.ui.customers import CustomersPage
from app.ui.pages import BackupPage, ReportPage, SettingsPage
from app.ui.style import base_font_for, build_stylesheet, set_scale, sized
from app.ui.widgets import button


class IconMark(QtWidgets.QWidget):
    """The app icon, drawn smoothly at whatever size the UI scale gives it."""

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.pix = QtGui.QPixmap(path)

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        if not self.pix.isNull():
            p.drawPixmap(self.rect(), self.pix)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle(config.APP_NAME)
        central = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QtWidgets.QFrame()
        header.setProperty("role", "header")
        nav = QtWidgets.QHBoxLayout(header)
        sized(nav, "setContentsMargins", 20, 10, 20, 10)
        sized(nav, "setSpacing", 6)
        icon_png = config.resource_path("assets", "app.png")
        if QtCore.QFile.exists(icon_png):
            mark = IconMark(icon_png)
            sized(mark, "setFixedSize", 44, 44)
        else:
            mark = QtWidgets.QLabel("洗")
            mark.setProperty("role", "brandmark")
        nav.addWidget(mark)
        nav.addSpacing(6)
        brand = QtWidgets.QLabel(config.APP_NAME)
        brand.setProperty("role", "brand")
        nav.addWidget(brand)
        nav.addSpacing(24)

        self.stack = QtWidgets.QStackedWidget()
        self.group = QtWidgets.QButtonGroup(self)
        self.group.setExclusive(True)
        self.customers_page = CustomersPage(db)
        self.report_page = ReportPage(db)
        self.backup_page = BackupPage(db)
        self.settings_page = SettingsPage(db)
        self.pages = [("客戶資料", self.customers_page), ("營收報表", self.report_page),
                      ("備份 / 還原", self.backup_page), ("設定", self.settings_page)]
        for i, (title, page) in enumerate(self.pages):
            b = button(title, "nav")
            b.setCheckable(True)
            self.group.addButton(b, i)
            nav.addWidget(b)
            self.stack.addWidget(page)
        nav.addStretch(1)
        self.group.buttonClicked[int].connect(self.show_page)
        root.addWidget(header)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self._base_pt = None
        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self.apply_font_size)
        self.setMinimumSize(640, 420)

        self.backup_page.restored.connect(self._on_restored)
        self.settings_page.font_size_changed.connect(self.set_font_size)
        self.apply_font_size()
        self.show_page(0)
        self.customers_page.part1.setFocus()

    def show_page(self, index: int):
        """Switch page. Pages refresh when shown, so they are never stale."""
        self.group.button(index).setChecked(True)
        self.stack.setCurrentIndex(index)
        self.pages[index][1].refresh()

    def _on_restored(self):
        self.apply_font_size(force=True)  # the backup may carry another font size
        self.stack.currentWidget().refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start()

    def apply_font_size(self, force: bool = False):
        """Pick the font size from the window size and the user's 小/中/大/特大 choice."""
        if self.isVisible():
            w, h = self.width(), self.height()
        else:
            geo = QtWidgets.QApplication.primaryScreen().availableGeometry()
            w, h = geo.width(), geo.height()
        factor = config.FONT_SCALES[self.settings_page.font_size_name()]
        base = base_font_for(w, h, factor)
        if base == self._base_pt and not force:
            return
        self._base_pt = base
        set_scale(base / config.REF_FONT_PT)
        QtWidgets.QApplication.instance().setStyleSheet(build_stylesheet(base))

    def set_font_size(self, name: str):
        self.db.set_setting("font_size", name)
        self.apply_font_size(force=True)
        self.settings_page.refresh()
