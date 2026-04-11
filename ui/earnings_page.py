from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtCore, QtGui
from database.database import (
    get_wash_records_by_date_range, get_earnings_summary, get_plate_spending
)
from ui.styles import build_dialog_stylesheet


class EarningsPage(QtWidgets.QDialog):
    """Earnings report dialog — view wash records by day/week/month/year."""

    PERIODS = [
        ("今日", "day"),
        ("本週", "week"),
        ("本月", "month"),
        ("今年", "year"),
    ]

    def __init__(self, parent=None, font_size=25):
        super().__init__(parent)
        self.setWindowTitle("營收報表")
        self.font_size = font_size
        self._size_to_screen(0.65, 0.8)
        self._build_ui()
        self._apply_style()
        self._on_period_changed()

    def _size_to_screen(self, w_ratio, h_ratio):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * w_ratio), int(screen.height() * h_ratio))

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        label_font = QtGui.QFont()
        label_font.setPointSize(max(12, int(self.font_size * 0.5)))
        label_font.setBold(True)

        # Period selector row
        period_row = QtWidgets.QHBoxLayout()
        period_row.setSpacing(8)

        period_label = QtWidgets.QLabel("時間範圍：")
        period_label.setFont(label_font)
        period_row.addWidget(period_label)

        btn_font = QtGui.QFont()
        btn_font.setPointSize(max(12, int(self.font_size * 0.45)))
        btn_font.setBold(True)

        self._period_buttons = {}
        for display_name, key in self.PERIODS:
            btn = QtWidgets.QPushButton(display_name)
            btn.setFont(btn_font)
            btn.setCheckable(True)
            btn.setMinimumHeight(56)
            btn.setMinimumWidth(100)
            btn.clicked.connect(lambda checked, k=key: self._select_period(k))
            period_row.addWidget(btn)
            self._period_buttons[key] = btn

        period_row.addStretch()

        # Custom date range
        date_font = QtGui.QFont()
        date_font.setPointSize(max(11, int(self.font_size * 0.4)))

        self.start_date = QtWidgets.QDateEdit()
        self.start_date.setFont(date_font)
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QtCore.QDate.currentDate())
        self.start_date.setMinimumHeight(56)
        self.start_date.setMinimumWidth(140)
        period_row.addWidget(self.start_date)

        to_label = QtWidgets.QLabel("至")
        to_label.setFont(label_font)
        period_row.addWidget(to_label)

        self.end_date = QtWidgets.QDateEdit()
        self.end_date.setFont(date_font)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QtCore.QDate.currentDate())
        self.end_date.setMinimumHeight(56)
        self.end_date.setMinimumWidth(140)
        period_row.addWidget(self.end_date)

        self.custom_btn = QtWidgets.QPushButton("查詢")
        self.custom_btn.setFont(btn_font)
        self.custom_btn.setMinimumHeight(56)
        self.custom_btn.setMinimumWidth(100)
        self.custom_btn.clicked.connect(self._on_custom_query)
        period_row.addWidget(self.custom_btn)

        layout.addLayout(period_row)

        # Summary cards
        summary_row = QtWidgets.QHBoxLayout()
        summary_row.setSpacing(12)

        summary_font = QtGui.QFont()
        summary_font.setPointSize(max(14, int(self.font_size * 0.6)))
        summary_font.setBold(True)

        self.total_label = QtWidgets.QLabel("總營收：$0")
        self.total_label.setFont(summary_font)
        self.total_label.setAlignment(QtCore.Qt.AlignCenter)
        self.total_label.setStyleSheet(
            "background: #F0FDFA; border: 1px solid #99F6E4; border-radius: 8px; padding: 12px; color: #0F766E;"
        )
        summary_row.addWidget(self.total_label)

        self.count_label = QtWidgets.QLabel("筆數：0")
        self.count_label.setFont(summary_font)
        self.count_label.setAlignment(QtCore.Qt.AlignCenter)
        self.count_label.setStyleSheet(
            "background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px; padding: 12px; color: #0369A1;"
        )
        summary_row.addWidget(self.count_label)

        layout.addLayout(summary_row)

        # Records table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["車牌號碼", "金額", "日期", "備註"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

        # Close button
        close_btn = QtWidgets.QPushButton("關閉")
        close_btn.setMinimumHeight(48)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        # Default to "today"
        self._select_period("day")

    def _apply_style(self):
        parent_button_size = getattr(self.parent(), 'button_font_size', 20) if self.parent() else 20
        self.setStyleSheet(build_dialog_stylesheet(parent_button_size))

    def _select_period(self, key):
        for k, btn in self._period_buttons.items():
            btn.setChecked(k == key)
        self._current_period = key
        self._on_period_changed()

    def _get_date_range(self, key):
        today = datetime.now().date()
        if key == "day":
            return today, today
        elif key == "week":
            start = today - timedelta(days=today.weekday())
            return start, today
        elif key == "month":
            start = today.replace(day=1)
            return start, today
        elif key == "year":
            start = today.replace(month=1, day=1)
            return start, today
        return today, today

    def _on_period_changed(self):
        start, end = self._get_date_range(self._current_period)
        self._load_data(start.isoformat(), end.isoformat())

    def _on_custom_query(self):
        # Deselect all period buttons
        for btn in self._period_buttons.values():
            btn.setChecked(False)
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        self._load_data(start, end)

    def _load_data(self, start_date, end_date):
        records = get_wash_records_by_date_range(start_date, end_date)
        summary = get_earnings_summary(start_date, end_date)

        self.total_label.setText(f"總營收：${summary['total']:,}")
        self.count_label.setText(f"筆數：{summary['count']}")

        self.table.setRowCount(len(records))
        for row, (plate, amount, wash_date, note) in enumerate(records):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
            amount_item = QtWidgets.QTableWidgetItem(f"${amount:,}")
            amount_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.table.setItem(row, 1, amount_item)
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(wash_date))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(note))

        self.table.resizeRowsToContents()
