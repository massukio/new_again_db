from PyQt5 import QtWidgets, QtCore, QtGui
from core.logger import logger
from database.database import (
    plate_exists, plate_and_phone_exists, add_plate_info,
    plate_and_phone_note_exists, plate_exists_excluding_original, get_connection
)
from ui.styles import build_dialog_stylesheet
from utils.helpers import validate_plate_parts
from config.brands import BRANDS, BRAND_ICONS


class BrandSelector(QtWidgets.QWidget):
    """Grid of brand buttons with large logo icons for elder-friendly selection."""
    brand_selected = QtCore.pyqtSignal(str)

    ICON_SIZE = 48

    def __init__(self, parent=None, font_size=14):
        super().__init__(parent)
        self._selected = ""
        self._buttons = {}
        self._font_size = font_size
        self._build_grid()

    def _build_grid(self):
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        cols = 4
        for i, (name, _) in enumerate(BRANDS):
            btn = QtWidgets.QToolButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            btn.setMinimumSize(100, 80)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            btn.setIconSize(QtCore.QSize(self.ICON_SIZE, self.ICON_SIZE))
            # Load brand logo
            logo_path = BRAND_ICONS.get(name, "")
            if logo_path and QtCore.QFile.exists(logo_path):
                btn.setIcon(QtGui.QIcon(logo_path))
            btn.setStyleSheet(self._button_style(False))
            btn.clicked.connect(lambda checked, n=name: self._on_click(n))
            layout.addWidget(btn, i // cols, i % cols)
            self._buttons[name] = btn

        scroll.setWidget(container)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _button_style(self, selected):
        if selected:
            return f"""
                QToolButton {{
                    background-color: #0891B2; color: white; border: none;
                    border-radius: 8px; font-size: {self._font_size}px; font-weight: bold;
                    padding: 8px 4px;
                }}
            """
        return f"""
            QToolButton {{
                background-color: #F5F5F4; color: #1C1917; border: 1px solid #E7E5E4;
                border-radius: 8px; font-size: {self._font_size}px;
                padding: 8px 4px;
            }}
            QToolButton:hover {{
                background-color: #E7E5E4;
            }}
        """

    def _on_click(self, name):
        self._selected = name
        for n, btn in self._buttons.items():
            btn.setChecked(n == name)
            btn.setStyleSheet(self._button_style(n == name))
        self.brand_selected.emit(name)

    def get_brand(self):
        return self._selected

    def set_brand(self, name):
        self._on_click(name) if name else self.clear()

    def clear(self):
        self._selected = ""
        for btn in self._buttons.values():
            btn.setChecked(False)
            btn.setStyleSheet(self._button_style(False))


class AddPlateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, plate_type='add', original_values=None, font_size=25):
        super().__init__(parent)
        self.plate_type = plate_type
        self.original_values = original_values or ("", "", "", "", "")
        self.font_size = font_size
        self.setWindowTitle("新增車牌資料" if plate_type == 'add' else "修改車牌資料")
        self._size_to_screen(0.55, 0.8)

        self._build_ui()
        self._apply_style()

    def _size_to_screen(self, w_ratio, h_ratio):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * w_ratio)
        h = int(screen.height() * h_ratio)
        self.resize(w, h)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        input_font = QtGui.QFont()
        input_font.setPointSize(self.font_size)
        input_font.setBold(True)

        label_font = QtGui.QFont()
        label_font.setPointSize(max(10, int(self.font_size * 0.45)))
        label_font.setBold(True)

        # Brand selector
        brand_label = QtWidgets.QLabel("車輛品牌")
        brand_label.setFont(label_font)
        brand_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(brand_label)

        self.brand_selector = BrandSelector(self, font_size=max(11, int(self.font_size * 0.45)))
        layout.addWidget(self.brand_selector)

        # Plate number
        plate_label = QtWidgets.QLabel("車牌號碼")
        plate_label.setFont(label_font)
        plate_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(plate_label)

        plate_row = QtWidgets.QHBoxLayout()
        self.plate_part1_line_edit = self._make_line_edit(input_font, 4)
        self.plate_part1_line_edit.setPlaceholderText("前半")
        self.plate_part1_line_edit.textChanged.connect(self._convert_to_upper)
        plate_row.addWidget(self.plate_part1_line_edit)

        dash = QtWidgets.QLabel("—")
        dash.setFont(input_font)
        dash.setAlignment(QtCore.Qt.AlignCenter)
        dash.setFixedWidth(30)
        plate_row.addWidget(dash)

        self.plate_part2_line_edit = self._make_line_edit(input_font, 4)
        self.plate_part2_line_edit.setPlaceholderText("後半")
        self.plate_part2_line_edit.textChanged.connect(self._convert_to_upper)
        plate_row.addWidget(self.plate_part2_line_edit)
        layout.addLayout(plate_row)

        # Phone + Note in a row
        detail_row = QtWidgets.QHBoxLayout()
        detail_row.setSpacing(10)

        phone_col = QtWidgets.QVBoxLayout()
        phone_label = QtWidgets.QLabel("電話號碼")
        phone_label.setFont(label_font)
        phone_label.setAlignment(QtCore.Qt.AlignCenter)
        phone_col.addWidget(phone_label)
        self.phone_number_line_edit = self._make_line_edit(input_font, 10)
        self.phone_number_line_edit.setPlaceholderText("電話號碼")
        self.phone_number_line_edit.setValidator(QtGui.QIntValidator())
        phone_col.addWidget(self.phone_number_line_edit)
        detail_row.addLayout(phone_col)

        note_col = QtWidgets.QVBoxLayout()
        note_label = QtWidgets.QLabel("備註")
        note_label.setFont(label_font)
        note_label.setAlignment(QtCore.Qt.AlignCenter)
        note_col.addWidget(note_label)
        self.note_line_edit = self._make_line_edit(input_font, 100)
        self.note_line_edit.setPlaceholderText("備註（選填）")
        note_col.addWidget(self.note_line_edit)
        detail_row.addLayout(note_col)

        layout.addLayout(detail_row)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("確定")
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _make_line_edit(self, font, max_length):
        edit = QtWidgets.QLineEdit()
        edit.setFont(font)
        edit.setMaxLength(max_length)
        edit.setAlignment(QtCore.Qt.AlignCenter)
        edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        edit.setMinimumHeight(48)
        return edit

    def _apply_style(self):
        parent_button_size = getattr(self.parent(), 'button_font_size', 20) if self.parent() else 20
        self.setStyleSheet(build_dialog_stylesheet(parent_button_size))

    def clear_inputs(self):
        self.plate_part1_line_edit.clear()
        self.plate_part2_line_edit.clear()
        self.phone_number_line_edit.clear()
        self.note_line_edit.clear()
        self.brand_selector.clear()
        self.plate_part1_line_edit.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            focus = self.focusWidget()
            if focus == self.plate_part1_line_edit:
                self.plate_part2_line_edit.setFocus()
            elif focus == self.plate_part2_line_edit:
                self.phone_number_line_edit.setFocus()
            elif focus == self.phone_number_line_edit:
                self.note_line_edit.setFocus()
            elif focus == self.note_line_edit:
                self.accept()
            # Don't propagate Enter to avoid closing dialog
        elif event.key() == QtCore.Qt.Key_Escape:
            self.clear_inputs()
        else:
            super().keyPressEvent(event)

    def accept(self):
        plate_info = self.get_plate_info()
        part1, part2, phone, note, brand = plate_info

        error = validate_plate_parts(part1, part2)
        if error:
            QtWidgets.QMessageBox.critical(self, "錯誤", error)
            return

        if self.plate_type == 'add':
            self._accept_add(part1, part2, phone, note, brand)
        else:
            self._accept_edit(part1, part2, phone, note, brand)

    def _accept_add(self, part1, part2, phone, note, brand):
        if plate_and_phone_exists(part1, part2, phone):
            QtWidgets.QMessageBox.critical(self, "錯誤", "此車牌號碼和電話號碼已存在。")
            return

        if plate_exists(part1, part2):
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("警告")
            msg.setText("此車牌號碼已存在但電話號碼不同。是否繼續保存？")
            yes_btn = msg.addButton("是", QtWidgets.QMessageBox.YesRole)
            msg.addButton("否", QtWidgets.QMessageBox.NoRole)
            msg.exec_()
            if msg.clickedButton() == yes_btn:
                add_plate_info(part1, part2, phone, note, brand)
                self.done(QtWidgets.QDialog.Accepted)
            else:
                self.clear_inputs()
            return

        add_plate_info(part1, part2, phone, note, brand)
        self.done(QtWidgets.QDialog.Accepted)

    def _accept_edit(self, new_part1, new_part2, new_phone, new_note, new_brand):
        orig_part1, orig_part2, orig_phone, orig_note = self.original_values[:4]

        if (new_part1.upper(), new_part2.upper()) != (orig_part1.upper(), orig_part2.upper()):
            if plate_exists_excluding_original(new_part1, new_part2, orig_part1, orig_part2):
                QtWidgets.QMessageBox.critical(self, "錯誤", "此車牌號碼已經存在，無法更新。")
                return

        if (new_part1.upper(), new_part2.upper(), new_phone, new_note) != \
           (orig_part1.upper(), orig_part2.upper(), orig_phone, orig_note):
            if plate_and_phone_note_exists(new_part1, new_part2, new_phone, new_note):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT COUNT(*) FROM plate_info
                        WHERE part1 = ? AND part2 = ? AND phone_number = ? AND note = ?
                        AND NOT (part1 = ? AND part2 = ? AND phone_number = ? AND note = ?)
                    ''', (new_part1.upper(), new_part2.upper(), new_phone, new_note,
                          orig_part1.upper(), orig_part2.upper(), orig_phone, orig_note))
                    if cursor.fetchone()[0] > 0:
                        QtWidgets.QMessageBox.critical(self, "錯誤", "此車牌號碼、電話號碼與相同備註已經存在。")
                        return

        self.done(QtWidgets.QDialog.Accepted)

    def get_plate_info(self):
        return (
            self.plate_part1_line_edit.text(),
            self.plate_part2_line_edit.text(),
            self.phone_number_line_edit.text(),
            self.note_line_edit.text(),
            self.brand_selector.get_brand(),
        )

    def _convert_to_upper(self, text):
        sender = self.sender()
        sender.blockSignals(True)
        sender.setText(text.upper())
        sender.blockSignals(False)
