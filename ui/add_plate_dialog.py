from PyQt5 import QtWidgets, QtCore, QtGui
from core.logger import logger
from database.database import plate_exists, plate_and_phone_exists, add_plate_info, plate_and_phone_note_exists, plate_exists_excluding_original, get_connection, filter_plate_info
from config.constants import DATABASE_FILE
from utils.helpers import format_phone_number
import sqlite3

class AddPlateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, plate_type='add', original_values=None, font_size=25):
        super(AddPlateDialog, self).__init__(parent)
        self.plate_type = plate_type
        self.original_values = original_values if original_values else ("", "", "", "")
        self.font_size = font_size
        self.setWindowTitle("新增車牌資料" if plate_type == 'add' else "修改車牌資料")
        self.resize(801, 267)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.grid_layout_widget = QtWidgets.QWidget(self)
        self.grid_layout = QtWidgets.QGridLayout(self.grid_layout_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.grid_layout_widget)

        self.plate_part1_line_edit = QtWidgets.QLineEdit(self.grid_layout_widget)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        font.setWeight(75)
        self.plate_part1_line_edit.setFont(font)
        self.plate_part1_line_edit.setMaxLength(4)
        self.plate_part1_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.plate_part1_line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plate_part1_line_edit.textChanged.connect(self.convert_to_upper)
        self.plate_part1_line_edit.textChanged.connect(self.search_plate)
        self.grid_layout.addWidget(self.plate_part1_line_edit, 1, 0, 1, 1)

        self.label = QtWidgets.QLabel(self.grid_layout_widget)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)  # Same size as input fields
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setText("車牌號碼")
        self.grid_layout.addWidget(self.label, 0, 0, 1, 2)

        self.plate_part2_line_edit = QtWidgets.QLineEdit(self.grid_layout_widget)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        font.setWeight(75)
        self.plate_part2_line_edit.setFont(font)
        self.plate_part2_line_edit.setMaxLength(4)
        self.plate_part2_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.plate_part2_line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plate_part2_line_edit.textChanged.connect(self.convert_to_upper)
        self.plate_part2_line_edit.textChanged.connect(self.search_plate)
        self.grid_layout.addWidget(self.plate_part2_line_edit, 1, 1, 1, 1)

        self.grid_layout_widget_2 = QtWidgets.QWidget(self)
        self.grid_layout_2 = QtWidgets.QGridLayout(self.grid_layout_widget_2)
        self.grid_layout_2.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.grid_layout_widget_2)

        self.phone_number_line_edit = QtWidgets.QLineEdit(self.grid_layout_widget_2)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        font.setWeight(75)
        self.phone_number_line_edit.setFont(font)
        self.phone_number_line_edit.setMaxLength(10)
        self.phone_number_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.phone_number_line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.phone_number_line_edit.setValidator(QtGui.QIntValidator())
        self.grid_layout_2.addWidget(self.phone_number_line_edit, 1, 0, 1, 1)

        self.label_2 = QtWidgets.QLabel(self.grid_layout_widget_2)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)  # Same size as input fields
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setText("電話號碼")
        self.grid_layout_2.addWidget(self.label_2, 0, 0, 1, 1)

        self.grid_layout_widget_3 = QtWidgets.QWidget(self)
        self.grid_layout_3 = QtWidgets.QGridLayout(self.grid_layout_widget_3)
        self.grid_layout_3.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.grid_layout_widget_3)

        self.note_line_edit = QtWidgets.QLineEdit(self.grid_layout_widget_3)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        font.setWeight(75)
        self.note_line_edit.setFont(font)
        self.note_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.note_line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.grid_layout_3.addWidget(self.note_line_edit, 1, 0, 1, 1)

        self.label_3 = QtWidgets.QLabel(self.grid_layout_widget_3)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)  # Same size as input fields
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setText("備註")
        self.grid_layout_3.addWidget(self.label_3, 0, 0, 1, 1)

        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("確定")
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.results_table = QtWidgets.QTableWidget(self)
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["車牌號碼", "電話號碼", "備註"])
        self.results_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.results_table.setVisible(False)  # Initially hidden
        self.main_layout.addWidget(self.results_table)

        self.main_layout.addWidget(self.button_box)

        self.apply_modern_style()

    def resizeEvent(self, event):
        self.adjust_font_size()
        super(AddPlateDialog, self).resizeEvent(event)

    def adjust_font_size(self):
        # Font for input fields - use exact size passed
        input_font = QtGui.QFont()
        input_font.setPointSize(self.font_size)
        input_font.setBold(True)
        input_font.setWeight(75)
        
        # Update input fields
        self.plate_part1_line_edit.setFont(input_font)
        self.plate_part2_line_edit.setFont(input_font)
        self.phone_number_line_edit.setFont(input_font)
        self.note_line_edit.setFont(input_font)
        
        # Font for labels (60% of input field size)
        label_font = QtGui.QFont()
        label_font.setPointSize(int(self.font_size * 0.4))  # Make labels even smaller
        label_font.setBold(True)
        label_font.setWeight(75)
        
        # Update labels
        self.label.setFont(label_font)
        self.label_2.setFont(label_font)
        self.label_3.setFont(label_font)
        
        # Also update stylesheet to ensure no conflicts
        style_sheet = """
        QLabel {
            padding: 2px;
        }
        """
        self.setStyleSheet(style_sheet)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key_Escape:
            self.clear_inputs()
        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            focus_widget = self.focusWidget()
            if focus_widget == self.phone_number_line_edit:
                self.note_line_edit.setFocus()
            elif focus_widget == self.note_line_edit:
                self.accept()
            elif isinstance(focus_widget, QtWidgets.QLineEdit):
                self.focusNextChild()
        else:
            super(AddPlateDialog, self).keyPressEvent(event)

    def search_plate(self):
        """Search for plates based on the input and update the results table."""
        part1 = self.plate_part1_line_edit.text()
        part2 = self.plate_part2_line_edit.text()

        if not part1 and not part2:
            self.results_table.setVisible(False)
            self.results_table.setRowCount(0)
            return

        # We pass "車牌查詢" as search_mode to filter_plate_info
        results = filter_plate_info(part1, part2, "", "車牌查詢")

        if results:
            self.results_table.setVisible(True)
            self.results_table.setRowCount(len(results))
            for row, (plate, phone_number, note) in enumerate(results):
                formatted_phone_number = format_phone_number(phone_number)
                self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
                self.results_table.setItem(row, 1, QtWidgets.QTableWidgetItem(formatted_phone_number))
                self.results_table.setItem(row, 2, QtWidgets.QTableWidgetItem(note))
            self.results_table.resizeRowsToContents()
        else:
            self.results_table.setVisible(False)
            self.results_table.setRowCount(0)

    def accept(self) -> None:
        """Handle the accept event."""
        plate_info = self.get_plate_info()
        logger.debug(f"Plate Info: {plate_info}")

        if self.plate_type == 'add':
            if plate_and_phone_exists(plate_info[0], plate_info[1], plate_info[2]):
                error_dialog = QtWidgets.QMessageBox()
                error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
                error_dialog.setWindowTitle("錯誤")
                error_dialog.setText("此車牌號碼和電話號碼已存在。")
                error_dialog.addButton("確定", QtWidgets.QMessageBox.AcceptRole)
                error_dialog.exec_()
                return
            elif plate_exists(plate_info[0], plate_info[1]):
                warning_dialog = QtWidgets.QMessageBox()
                warning_dialog.setIcon(QtWidgets.QMessageBox.Warning)
                warning_dialog.setWindowTitle("警告")
                warning_dialog.setText("此車牌號碼已存在但電話號碼不同。是否繼續保存？")
                yes_button = warning_dialog.addButton("是", QtWidgets.QMessageBox.YesRole)
                no_button = warning_dialog.addButton("否", QtWidgets.QMessageBox.NoRole)
                warning_dialog.exec_()
                if warning_dialog.clickedButton() == yes_button:
                    add_plate_info(plate_info[0], plate_info[1], plate_info[2], plate_info[3])
                    self.done(QtWidgets.QDialog.Accepted)
                else:
                    self.clear_inputs()
                    self.plate_part1_line_edit.setFocus()
            else:
                add_plate_info(plate_info[0], plate_info[1], plate_info[2], plate_info[3])
                self.done(QtWidgets.QDialog.Accepted)

        else:  # plate_type == 'edit'
            # For edit mode, we check if the new values are different from the original
            # and if the new combination already exists
            new_part1, new_part2, new_phone, new_note = plate_info
            orig_part1, orig_part2, orig_phone, orig_note = self.original_values
            
            # Check if the new plate number already exists (excluding the original record)
            if (new_part1.upper(), new_part2.upper()) != (orig_part1.upper(), orig_part2.upper()):
                if plate_exists_excluding_original(new_part1, new_part2, orig_part1, orig_part2):
                    error_dialog = QtWidgets.QMessageBox()
                    error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
                    error_dialog.setWindowTitle("錯誤")
                    error_dialog.setText("此車牌號碼已經存在，無法更新。")
                    error_dialog.addButton("確定", QtWidgets.QMessageBox.AcceptRole)
                    error_dialog.exec_()
                    return
            
            # Check if the new combination already exists (and it's not the same as original)
            if (new_part1.upper(), new_part2.upper(), new_phone, new_note) != (orig_part1.upper(), orig_part2.upper(), orig_phone, orig_note):
                if plate_and_phone_note_exists(new_part1, new_part2, new_phone, new_note):
                    # If the exact same combination exists, check if it's a different record
                    # by querying the database directly and excluding the original record
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT COUNT(*)
                        FROM plate_info
                        WHERE part1 = ? AND part2 = ? AND phone_number = ? AND note = ? 
                        AND NOT (part1 = ? AND part2 = ? AND phone_number = ? AND note = ?)
                    ''', (new_part1.upper(), new_part2.upper(), new_phone, new_note,
                          orig_part1.upper(), orig_part2.upper(), orig_phone, orig_note))
                    count = cursor.fetchone()[0]
                    conn.close()
                    
                    if count > 0:
                        error_dialog = QtWidgets.QMessageBox()
                        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
                        error_dialog.setWindowTitle("錯誤")
                        error_dialog.setText("此車牌號碼、電話號碼與相同備註已經存在。")
                        error_dialog.addButton("確定", QtWidgets.QMessageBox.AcceptRole)
                        error_dialog.exec_()
                        return
            
            # For edit mode, we just accept and let the main application handle the update
            self.done(QtWidgets.QDialog.Accepted)

    def reject(self) -> None:
        """Handle the reject event."""
        super(AddPlateDialog, self).reject()

    def get_plate_info(self) -> tuple:
        """Get the plate info from the input fields."""
        return self.plate_part1_line_edit.text(), self.plate_part2_line_edit.text(), self.phone_number_line_edit.text(), self.note_line_edit.text()

    def clear_inputs(self):
        """Clear all input fields."""
        self.plate_part1_line_edit.clear()
        self.plate_part2_line_edit.clear()
        self.phone_number_line_edit.clear()
        self.note_line_edit.clear()
        self.results_table.setRowCount(0)
        self.results_table.setVisible(False)

    def convert_to_upper(self, text: str) -> None:
        """Convert the input text to uppercase."""
        sender = self.sender()
        sender.blockSignals(True)
        sender.setText(text.upper())
        sender.blockSignals(False)

    def apply_modern_style(self):
        style_sheet = f"""
        QDialog {{
            background-color: #f0f0f0;
            font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }}
        QLineEdit {{
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }}
        QLabel {{
            color: #333;
        }}
        QPushButton {{
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: {self.parent().button_font_size}px;
            margin: 4px 2px;
            border-radius: 8px;
        }}
        QPushButton:hover {{
            background-color: #45a049;
        }}
        """
        self.setStyleSheet(style_sheet)
        self.adjust_font_size()
