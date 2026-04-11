from PyQt5 import QtWidgets, QtCore, QtGui
from ui.styles import build_dialog_stylesheet

WASH_TYPES = ["一般洗車", "精緻洗車", "美容", "其他"]


class WashRecordDialog(QtWidgets.QDialog):
    """Dialog for recording a wash spending amount for a plate."""

    def __init__(self, parent=None, plate_text="", font_size=25):
        super().__init__(parent)
        self.setWindowTitle("記錄消費")
        self.font_size = font_size
        self._plate_text = plate_text
        self._selected_type = WASH_TYPES[0]
        self._size_to_screen(0.4, 0.55)
        self._build_ui()
        self._apply_style()

    def _size_to_screen(self, w_ratio, h_ratio):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * w_ratio), int(screen.height() * h_ratio))

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label_font = QtGui.QFont()
        label_font.setPointSize(max(10, int(self.font_size * 0.45)))
        label_font.setBold(True)

        input_font = QtGui.QFont()
        input_font.setPointSize(self.font_size)
        input_font.setBold(True)

        # Plate display
        plate_label = QtWidgets.QLabel(f"車牌：{self._plate_text}")
        plate_label.setFont(label_font)
        plate_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(plate_label)

        # Wash type selector
        type_label = QtWidgets.QLabel("洗車類型")
        type_label.setFont(label_font)
        type_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(type_label)

        type_row = QtWidgets.QHBoxLayout()
        type_row.setSpacing(6)
        self._type_buttons = {}
        btn_font = QtGui.QFont()
        btn_font.setPointSize(max(10, int(self.font_size * 0.45)))
        btn_font.setBold(True)
        for name in WASH_TYPES:
            btn = QtWidgets.QPushButton(name)
            btn.setFont(btn_font)
            btn.setCheckable(True)
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda checked, n=name: self._select_type(n))
            type_row.addWidget(btn)
            self._type_buttons[name] = btn
        layout.addLayout(type_row)
        # Select default
        self._select_type(WASH_TYPES[0])

        # Amount input
        amount_label = QtWidgets.QLabel("消費金額")
        amount_label.setFont(label_font)
        amount_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(amount_label)

        self.amount_edit = QtWidgets.QLineEdit()
        self.amount_edit.setFont(input_font)
        self.amount_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.amount_edit.setPlaceholderText("輸入金額")
        self.amount_edit.setValidator(QtGui.QIntValidator(1, 999999))
        self.amount_edit.setMinimumHeight(48)
        layout.addWidget(self.amount_edit)

        # Note input (optional)
        note_label = QtWidgets.QLabel("備註（選填）")
        note_label.setFont(label_font)
        note_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(note_label)

        self.note_edit = QtWidgets.QLineEdit()
        self.note_edit.setFont(QtGui.QFont("", max(10, int(self.font_size * 0.5))))
        self.note_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.note_edit.setPlaceholderText("額外備註")
        self.note_edit.setMaxLength(50)
        self.note_edit.setMinimumHeight(40)
        layout.addWidget(self.note_edit)

        # Buttons
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText("確定")
        btn_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.amount_edit.setFocus()

    def _select_type(self, name):
        self._selected_type = name
        for n, btn in self._type_buttons.items():
            selected = (n == name)
            btn.setChecked(selected)
            if selected:
                btn.setStyleSheet(
                    "background-color: #0891B2; color: white; border: none; "
                    "border-radius: 8px; padding: 8px 12px;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: #F5F5F4; color: #1C1917; border: 1px solid #E7E5E4; "
                    "border-radius: 8px; padding: 8px 12px;"
                )

    def _apply_style(self):
        parent_button_size = getattr(self.parent(), 'button_font_size', 20) if self.parent() else 20
        self.setStyleSheet(build_dialog_stylesheet(parent_button_size))

    def _on_accept(self):
        if not self.amount_edit.text().strip():
            QtWidgets.QMessageBox.critical(self, "錯誤", "請輸入金額。")
            return
        self.accept()

    def get_amount(self):
        return int(self.amount_edit.text())

    def get_wash_type(self):
        return self._selected_type

    def get_note(self):
        extra = self.note_edit.text().strip()
        if extra:
            return f"{self._selected_type} - {extra}"
        return self._selected_type

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self.focusWidget() == self.amount_edit:
                self.note_edit.setFocus()
            else:
                self._on_accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
