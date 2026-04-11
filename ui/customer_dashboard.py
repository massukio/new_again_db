from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from database.database import get_plate_summary, get_plate_spending, set_vip_status
from ui.styles import build_dialog_stylesheet


class CustomerDashboard(QtWidgets.QDialog):
    """Per-plate customer dashboard — spending, visits, VIP toggle."""

    def __init__(self, parent=None, part1="", part2="", phone="", is_vip=False, font_size=25):
        super().__init__(parent)
        self.part1 = part1
        self.part2 = part2
        self.phone = phone
        self._is_vip = is_vip
        self.font_size = font_size
        self.setWindowTitle(f"客戶資訊 — {part1}-{part2}")
        self._size_to_screen(0.5, 0.7)
        self._build_ui()
        self._apply_style()
        self._load_data()

    def _size_to_screen(self, w_ratio, h_ratio):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * w_ratio), int(screen.height() * h_ratio))

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header_font = QtGui.QFont()
        header_font.setPointSize(max(16, int(self.font_size * 0.7)))
        header_font.setBold(True)

        card_font = QtGui.QFont()
        card_font.setPointSize(max(14, int(self.font_size * 0.55)))
        card_font.setBold(True)

        # Header: plate + VIP toggle
        header_row = QtWidgets.QHBoxLayout()
        plate_label = QtWidgets.QLabel(f"{self.part1}-{self.part2}")
        plate_label.setFont(header_font)
        header_row.addWidget(plate_label)
        header_row.addStretch()

        self.vip_btn = QtWidgets.QPushButton("★ VIP" if self._is_vip else "☆ 設為VIP")
        self.vip_btn.setMinimumHeight(48)
        self.vip_btn.setMinimumWidth(140)
        self.vip_btn.clicked.connect(self._toggle_vip)
        self._update_vip_btn_style()
        header_row.addWidget(self.vip_btn)
        layout.addLayout(header_row)

        # Summary cards
        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(10)

        self.total_label = self._make_card("累計消費：$0", card_font,
            "background: #F0FDFA; border: 1px solid #99F6E4; color: #0F766E;")
        cards_row.addWidget(self.total_label)

        self.count_label = self._make_card("來店次數：0 次", card_font,
            "background: #F0F9FF; border: 1px solid #BAE6FD; color: #0369A1;")
        cards_row.addWidget(self.count_label)

        self.last_visit_label = self._make_card("上次來店：無紀錄", card_font,
            "background: #FFF7ED; border: 1px solid #FED7AA; color: #9A3412;")
        cards_row.addWidget(self.last_visit_label)

        self.avg_label = self._make_card("平均消費：$0", card_font,
            "background: #F5F3FF; border: 1px solid #DDD6FE; color: #5B21B6;")
        cards_row.addWidget(self.avg_label)

        layout.addLayout(cards_row)

        # Visit history table
        history_label = QtWidgets.QLabel("消費紀錄")
        label_font = QtGui.QFont()
        label_font.setPointSize(max(12, int(self.font_size * 0.45)))
        label_font.setBold(True)
        history_label.setFont(label_font)
        layout.addWidget(history_label)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["日期", "金額", "備註"])
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

    def _make_card(self, text, font, style):
        label = QtWidgets.QLabel(text)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet(f"{style} border-radius: 8px; padding: 12px;")
        label.setMinimumHeight(60)
        return label

    def _apply_style(self):
        parent_button_size = getattr(self.parent(), 'button_font_size', 20) if self.parent() else 20
        self.setStyleSheet(build_dialog_stylesheet(parent_button_size))

    def _load_data(self):
        summary = get_plate_summary(self.part1, self.part2)

        self.total_label.setText(f"累計消費：${summary['total_spent']:,}")
        self.count_label.setText(f"來店次數：{summary['visit_count']} 次")
        self.avg_label.setText(f"平均消費：${summary['avg_spend']:,}")

        if summary['last_visit']:
            last = datetime.strptime(summary['last_visit'], '%Y-%m-%d').date()
            days = (datetime.now().date() - last).days
            if days == 0:
                text = "上次來店：今天"
            else:
                text = f"上次來店：{days} 天前"
            self.last_visit_label.setText(text)
            if days >= 30:
                self.last_visit_label.setStyleSheet(
                    "background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; "
                    "border-radius: 8px; padding: 12px;"
                )
        else:
            self.last_visit_label.setText("上次來店：無紀錄")

        # Populate history table
        records = get_plate_spending(self.part1, self.part2)
        self.table.setRowCount(len(records))
        for row, (amount, wash_date, note) in enumerate(records):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(wash_date))
            amount_item = QtWidgets.QTableWidgetItem(f"${amount:,}")
            amount_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.table.setItem(row, 1, amount_item)
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(note))
        self.table.resizeRowsToContents()

    def _toggle_vip(self):
        self._is_vip = not self._is_vip
        set_vip_status(self.part1, self.part2, self.phone, self._is_vip)
        self._update_vip_btn_style()

    def _update_vip_btn_style(self):
        if self._is_vip:
            self.vip_btn.setText("★ VIP")
            self.vip_btn.setStyleSheet(
                "background-color: #F59E0B; color: white; border: none; "
                "border-radius: 8px; font-weight: bold; font-size: 16px; padding: 8px 16px;"
            )
        else:
            self.vip_btn.setText("☆ 設為VIP")
            self.vip_btn.setStyleSheet(
                "background-color: #F5F5F4; color: #78716C; border: 1px solid #E7E5E4; "
                "border-radius: 8px; font-weight: bold; font-size: 16px; padding: 8px 16px;"
            )

    @property
    def is_vip(self):
        return self._is_vip
