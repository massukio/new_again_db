from PyQt5 import QtCore, QtGui, QtWidgets
from config.constants import PLATE_MAX_LENGTH, PHONE_MAX_LENGTH, APP_NAME


class _SearchModeProxy(QtCore.QObject):
    """Mimics QComboBox API so existing code (table_view_handler) works unchanged."""
    currentIndexChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._index = 0
        self._items = ["車牌查詢", "電話查詢"]

    def currentText(self):
        return self._items[self._index]

    def currentIndex(self):
        return self._index

    def setCurrentIndex(self, idx):
        if self._index != idx:
            self._index = idx
            self.currentIndexChanged.emit(idx)


class UiMainWindow(object):
    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.setWindowTitle(APP_NAME)

        self.central_widget = QtWidgets.QWidget(main_window)
        main_window.setCentralWidget(self.central_widget)

        # Main layout with comfortable margins
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(12)

        # === Search bar at TOP (more natural — search first, results below) ===
        search_layout = QtWidgets.QHBoxLayout()
        search_layout.setSpacing(10)

        # Search mode toggle buttons (replaces dropdown for elder usability)
        self.search_combo_box = _SearchModeProxy()  # proxy for backward compat
        self.plate_search_btn = QtWidgets.QPushButton("車牌查詢")
        self.plate_search_btn.setObjectName("search_mode_btn")
        self.plate_search_btn.setCheckable(True)
        self.plate_search_btn.setChecked(True)
        self.plate_search_btn.setFixedHeight(72)
        self.plate_search_btn.setMinimumWidth(120)
        self.plate_search_btn.clicked.connect(lambda: self._set_search_mode(0))
        search_layout.addWidget(self.plate_search_btn)

        self.phone_search_btn = QtWidgets.QPushButton("電話查詢")
        self.phone_search_btn.setObjectName("search_mode_btn")
        self.phone_search_btn.setCheckable(True)
        self.phone_search_btn.setFixedHeight(72)
        self.phone_search_btn.setMinimumWidth(120)
        self.phone_search_btn.clicked.connect(lambda: self._set_search_mode(1))
        search_layout.addWidget(self.phone_search_btn)

        self.plate_line_edit = QtWidgets.QLineEdit()
        self.plate_line_edit.setObjectName("plate_line_edit")
        self.plate_line_edit.setMaxLength(PLATE_MAX_LENGTH)
        self.plate_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.plate_line_edit.setPlaceholderText("車牌前半")
        self.plate_line_edit.setFixedHeight(72)
        search_layout.addWidget(self.plate_line_edit, stretch=1)

        # Dash separator label between plate fields
        self.dash_label = QtWidgets.QLabel("—")
        self.dash_label.setAlignment(QtCore.Qt.AlignCenter)
        self.dash_label.setFixedWidth(24)
        search_layout.addWidget(self.dash_label)

        self.plate_line_edit2 = QtWidgets.QLineEdit()
        self.plate_line_edit2.setObjectName("plate_line_edit2")
        self.plate_line_edit2.setMaxLength(PLATE_MAX_LENGTH)
        self.plate_line_edit2.setAlignment(QtCore.Qt.AlignCenter)
        self.plate_line_edit2.setPlaceholderText("車牌後半")
        self.plate_line_edit2.setFixedHeight(72)
        search_layout.addWidget(self.plate_line_edit2, stretch=1)

        self.clear_button = QtWidgets.QPushButton("清除")
        self.clear_button.setObjectName("clear_button")
        self.clear_button.setFixedHeight(72)
        self.clear_button.setFixedWidth(120)
        search_layout.addWidget(self.clear_button)

        # === Content area: table + action buttons ===
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(12)

        # Table view — the star of the UI
        self.table_view = QtWidgets.QTableWidget()
        self.table_view.setObjectName("table_view")
        self.table_view.setColumnCount(4)
        self.table_view.setHorizontalHeaderLabels(["車牌號碼", "電話號碼", "備註", "上次來店"])
        self.table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_view.horizontalHeader().setVisible(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table_view.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_view.setShowGrid(False)
        content_layout.addWidget(self.table_view, stretch=5)

        # Right button panel — compact, no wasted space
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(8)

        self.add_button = QtWidgets.QPushButton("＋ 新增資料")
        self.add_button.setObjectName("add_button")
        self.add_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.add_button.setMinimumHeight(64)
        button_layout.addWidget(self.add_button)

        self.modify_button = QtWidgets.QPushButton("✎ 修改資料")
        self.modify_button.setObjectName("modify_button")
        self.modify_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.modify_button.setMinimumHeight(64)
        button_layout.addWidget(self.modify_button)

        self.delete_button = QtWidgets.QPushButton("✕ 刪除資料")
        self.delete_button.setObjectName("delete_button")
        self.delete_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.delete_button.setMinimumHeight(64)
        button_layout.addWidget(self.delete_button)

        button_layout.addSpacing(12)

        self.wash_record_button = QtWidgets.QPushButton("$ 記錄消費")
        self.wash_record_button.setObjectName("wash_record_button")
        self.wash_record_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.wash_record_button.setMinimumHeight(64)
        button_layout.addWidget(self.wash_record_button)

        self.customer_info_button = QtWidgets.QPushButton("👤 客戶資訊")
        self.customer_info_button.setObjectName("wash_record_button")
        self.customer_info_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.customer_info_button.setMinimumHeight(64)
        button_layout.addWidget(self.customer_info_button)

        self.earnings_button = QtWidgets.QPushButton("📊 營收報表")
        self.earnings_button.setObjectName("earnings_button")
        self.earnings_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.earnings_button.setMinimumHeight(64)
        button_layout.addWidget(self.earnings_button)

        button_layout.addStretch(1)

        self.backup_button = QtWidgets.QPushButton("備份資料庫")
        self.backup_button.setObjectName("backup_button")
        self.backup_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.backup_button.setMinimumHeight(56)
        button_layout.addWidget(self.backup_button)

        content_layout.addLayout(button_layout, stretch=1)
        main_layout.addLayout(content_layout)

        # === Status flash label (auto-hides) ===
        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setMinimumHeight(48)
        self.status_label.setStyleSheet(
            "background-color: #D1FAE5; color: #065F46; border-radius: 8px; "
            "font-size: 18px; font-weight: bold; padding: 10px; margin: 4px 0px;"
        )
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

        # === Search bar at BOTTOM ===
        main_layout.addLayout(search_layout)

        # === Menu bar ===
        self.menu_bar = QtWidgets.QMenuBar(main_window)
        self.menu_other = QtWidgets.QMenu("其他", self.menu_bar)
        main_window.setMenuBar(self.menu_bar)

        self.action_about = QtWidgets.QAction("關於", main_window)
        self.action_adjust_font_size = QtWidgets.QAction("調整字體大小", main_window)
        self.menu_other.addAction(self.action_about)
        self.menu_other.addAction(self.action_adjust_font_size)
        self.menu_bar.addAction(self.menu_other.menuAction())

        # Tab order: plate1 → plate2 → clear
        QtWidgets.QWidget.setTabOrder(self.plate_line_edit, self.plate_line_edit2)
        QtWidgets.QWidget.setTabOrder(self.plate_line_edit2, self.clear_button)

        # Signal connections
        self.plate_line_edit.textChanged.connect(self._convert_to_upper)
        self.plate_line_edit2.textChanged.connect(self._convert_to_upper)
        self.plate_line_edit.returnPressed.connect(lambda: self.plate_line_edit2.setFocus())
        self.clear_button.clicked.connect(self.reset_table_view)
        self.action_about.triggered.connect(self._show_about_dialog)

        # Set initial search button styles
        self._update_search_btn_styles()

    def _set_search_mode(self, index):
        self.plate_search_btn.setChecked(index == 0)
        self.phone_search_btn.setChecked(index == 1)
        self._update_search_btn_styles()
        self.search_combo_box.setCurrentIndex(index)
        self.update_line_edits()

    def _update_search_btn_styles(self):
        for btn, checked in [(self.plate_search_btn, self.plate_search_btn.isChecked()),
                             (self.phone_search_btn, self.phone_search_btn.isChecked())]:
            if checked:
                btn.setStyleSheet(
                    "background-color: #0891B2; color: white; border: none; "
                    "border-radius: 10px; font-weight: bold;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: #F5F5F4; color: #1C1917; border: 1px solid #E7E5E4; "
                    "border-radius: 10px; font-weight: bold;"
                )

    def _convert_to_upper(self, text):
        sender = self.sender()
        sender.blockSignals(True)
        sender.setText(text.upper())
        sender.blockSignals(False)

    def reset_table_view(self):
        pass

    def update_line_edits(self):
        pass

    def _show_about_dialog(self):
        from config.constants import APP_VERSION, APP_AUTHOR
        QtWidgets.QMessageBox.about(
            None, "關於",
            f"Author: {APP_AUTHOR}\nVersion: {APP_VERSION}\n"
            f"Release Date: 2025-03-01\n\n"
            f"License: MIT License\n"
            f"This application is licensed under the MIT License."
        )
