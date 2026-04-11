import os
import sqlite3
from datetime import datetime
import shutil

from PyQt5 import QtCore, QtGui, QtWidgets

from ui.main_ui import UiMainWindow
from ui.add_plate_dialog import AddPlateDialog
from ui.table_view_handler import TableViewHandler
from ui.font_size_dialog import FontSizeDialog
from ui.wash_record_dialog import WashRecordDialog
from ui.earnings_page import EarningsPage
from ui.customer_dashboard import CustomerDashboard
from ui.styles import build_main_stylesheet
from core.logger import logger
from config.config_manager import load_font_config, save_font_config
from config.constants import DATABASE_FILE, PLATE_MAX_LENGTH, PHONE_MAX_LENGTH
from database.database import (
    add_plate_info, get_all_plate_info, update_plate_info, delete_plate_info,
    add_wash_record
)
from database.initialize_db import initialize_database, migrate_database


class MainWindow(QtWidgets.QMainWindow, UiMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        config = load_font_config()
        self.button_font_size = config["button_font_size"]
        self.table_font_size = config["table_font_size"]
        self.input_font_size = config["input_font_size"]

        self.setup_ui(self)
        self._adjust_window_size()
        self._apply_style()
        self._connect_signals()
        self._pre_check_database()
        self._initialize_table_handler()

    def _connect_signals(self):
        self.add_button.clicked.connect(self.show_add_plate_dialog)
        self.modify_button.clicked.connect(self.modify_selected_row)
        self.delete_button.clicked.connect(self.confirm_delete_selected_row)
        self.wash_record_button.clicked.connect(self.show_wash_record_dialog)
        self.customer_info_button.clicked.connect(self.show_customer_dashboard)
        self.earnings_button.clicked.connect(self.show_earnings_page)
        self.table_view.cellDoubleClicked.connect(lambda row, col: self.show_customer_dashboard())
        self.backup_button.clicked.connect(self.backup_database)
        self.action_adjust_font_size.triggered.connect(self.show_font_size_dialog)
        # ESC event filter on input widgets so ESC always clears search
        self.plate_line_edit.installEventFilter(self)
        self.plate_line_edit2.installEventFilter(self)
        self.table_view.installEventFilter(self)

    def _adjust_window_size(self):
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.setMinimumSize(int(screen.width() * 0.5), int(screen.height() * 0.5))

    def _apply_style(self):
        self.setStyleSheet(build_main_stylesheet(
            self.button_font_size, self.table_font_size, self.input_font_size
        ))

    def _pre_check_database(self):
        if not os.path.exists(DATABASE_FILE):
            initialize_database()
            QtWidgets.QMessageBox.information(
                self, '資料庫初始化', f'資料庫已創建於: {os.path.abspath(DATABASE_FILE)}'
            )
        else:
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plate_info'")
                if cursor.fetchone() is None:
                    raise sqlite3.OperationalError("Table 'plate_info' does not exist.")
                conn.close()
                migrate_database()
            except sqlite3.OperationalError as e:
                logger.error(f"Database error: {e}")
                os.remove(DATABASE_FILE)
                initialize_database()
                QtWidgets.QMessageBox.information(
                    self, '資料庫初始化', f'資料庫已創建於: {os.path.abspath(DATABASE_FILE)}'
                )

    def _initialize_table_handler(self):
        try:
            self.table_handler = TableViewHandler(
                self.table_view, self.plate_line_edit, self.plate_line_edit2, self.search_combo_box
            )
            self.table_view.sortByColumn(0, QtCore.Qt.AscendingOrder)
        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {e}")
            QtWidgets.QMessageBox.critical(
                self, '資料庫錯誤', '資料庫不存在或無法訪問。'
            )

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.reset_table_view()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Catch ESC from child widgets (QLineEdit consumes it otherwise)."""
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape:
            self.reset_table_view()
            return True
        return super().eventFilter(obj, event)

    def reset_table_view(self):
        self.plate_line_edit.clear()
        self.plate_line_edit2.clear()
        self._set_search_mode(0)
        self.table_handler.load_data()
        self.plate_line_edit.setFocus()
        self.table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def update_line_edits(self):
        self.plate_line_edit.clear()
        self.plate_line_edit2.clear()
        self.plate_line_edit.setFocus()

        if self.search_combo_box.currentText() == "電話查詢":
            self.plate_line_edit2.hide()
            self.dash_label.hide()
            self.plate_line_edit.setMaxLength(PHONE_MAX_LENGTH)
            self.plate_line_edit.setValidator(QtGui.QIntValidator())
            self.plate_line_edit.setPlaceholderText("輸入電話號碼...")
        else:
            self.plate_line_edit2.show()
            self.dash_label.show()
            self.plate_line_edit.setMaxLength(PLATE_MAX_LENGTH)
            self.plate_line_edit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[A-Za-z0-9]{0,4}")))
            self.plate_line_edit2.setMaxLength(PLATE_MAX_LENGTH)
            self.plate_line_edit2.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[A-Za-z0-9]{0,4}")))
            self.plate_line_edit.setPlaceholderText("車牌前半")
            self.plate_line_edit2.setPlaceholderText("車牌後半")

    def show_add_plate_dialog(self):
        dialog = AddPlateDialog(self, 'add', font_size=self.table_font_size)
        while dialog.exec_() == QtWidgets.QDialog.Accepted:
            logger.info(f"新增車牌號碼: {dialog.get_plate_info()}")
            self.table_handler.load_data()
            dialog.clear_inputs()  # Reuse dialog instead of creating new one

    def modify_selected_row(self):
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
        plate_info = self.table_view.item(selected_row, 0).text().replace("★ ", "")
        phone_number = self.table_view.item(selected_row, 1).text().replace('-', '')
        note = self.table_view.item(selected_row, 2).text()
        part1, part2 = plate_info.split('-')
        # Look up brand from DB
        from database.database import get_all_plate_info
        brand = ""
        for p, ph, n, b in get_all_plate_info():
            if p == plate_info and ph == phone_number:
                brand = b
                break

        dialog = AddPlateDialog(self, 'edit', (part1, part2, phone_number, note, brand), font_size=self.table_font_size)
        dialog.plate_part1_line_edit.setText(part1)
        dialog.plate_part2_line_edit.setText(part2)
        dialog.phone_number_line_edit.setText(phone_number)
        dialog.note_line_edit.setText(note)
        dialog.brand_selector.set_brand(brand)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_part1, new_part2, new_phone, new_note, new_brand = dialog.get_plate_info()
            success = update_plate_info(part1, part2, phone_number, new_part1, new_part2, new_phone, new_note, new_brand)
            if success:
                self.table_handler.update_row(selected_row, f"{new_part1}-{new_part2}", new_phone, new_note, new_brand)
            else:
                QtWidgets.QMessageBox.critical(self, '錯誤', '此車牌號碼、電話號碼組合已經存在，無法更新。')

    def show_customer_dashboard(self):
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            self._show_status("請先選擇一筆車牌資料")
            return
        plate_text = self.table_view.item(selected_row, 0).text().replace("★ ", "")
        phone = self.table_view.item(selected_row, 1).text().replace('-', '')
        part1, part2 = plate_text.split('-')
        # Check VIP status from DB
        from database.database import get_all_plates_with_stats
        is_vip = False
        for row in get_all_plates_with_stats():
            if row[0] == part1.upper() and row[1] == part2.upper() and row[2] == phone:
                is_vip = bool(row[5])
                break
        dialog = CustomerDashboard(self, part1, part2, phone, is_vip, font_size=self.table_font_size)
        dialog.exec_()
        # Refresh table in case VIP status changed
        self.table_handler.load_data()

    def show_wash_record_dialog(self):
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            self._show_status("請先選擇一筆車牌資料")
            return
        plate_text = self.table_view.item(selected_row, 0).text().replace("★ ", "")
        dialog = WashRecordDialog(self, plate_text, font_size=self.table_font_size)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            part1, part2 = plate_text.split('-')
            today = datetime.now().strftime('%Y-%m-%d')
            add_wash_record(part1, part2, dialog.get_amount(), today, dialog.get_note())
            self._show_status(f"✓ {plate_text} 已記錄 ${dialog.get_amount():,}")

    def _show_status(self, text):
        self.status_label.setText(text)
        self.status_label.show()
        QtCore.QTimer.singleShot(2500, self.status_label.hide)

    def show_earnings_page(self):
        dialog = EarningsPage(self, font_size=self.table_font_size)
        dialog.exec_()

    def confirm_delete_selected_row(self):
        selected_row = self.table_view.currentRow()
        if selected_row < 0:
            return
        plate_info = self.table_view.item(selected_row, 0).text().replace("★ ", "")
        phone_number = self.table_view.item(selected_row, 1).text()

        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setWindowTitle('確認刪除')
        msg.setText(f"確定要刪除車牌號碼 {plate_info} 和電話號碼 {phone_number} 嗎？")
        yes_btn = msg.addButton("是", QtWidgets.QMessageBox.YesRole)
        msg.addButton("否", QtWidgets.QMessageBox.NoRole)
        msg.exec_()
        if msg.clickedButton() == yes_btn:
            self.table_handler.delete_selected_row()

    def backup_database(self):
        current_date = datetime.now().strftime("%Y%m%d")
        file_type, ok = QtWidgets.QInputDialog.getItem(
            self, "選擇備份文件類型", "備份文件類型:",
            ["SQLite Database Files (*.db)", "SQL Dump Files (*.sql)"], 0, False
        )
        if not ok or not file_type:
            return

        options = QtWidgets.QFileDialog.Options() | QtWidgets.QFileDialog.DontUseNativeDialog
        if "db" in file_type:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "備份資料庫", f"{current_date}_backup.db",
                "SQLite Database Files (*.db);;All Files (*)", options=options
            )
            if file_path:
                try:
                    shutil.copyfile(DATABASE_FILE, file_path)
                    QtWidgets.QMessageBox.information(self, '成功', '資料庫備份成功。')
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, '錯誤', f'資料庫備份失敗: {e}')
        elif "sql" in file_type:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "備份資料庫", f"{current_date}_backup.sql",
                "SQL Dump Files (*.sql);;All Files (*)", options=options
            )
            if file_path:
                try:
                    conn = sqlite3.connect(DATABASE_FILE)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for line in conn.iterdump():
                            f.write(f'{line}\n')
                    conn.close()
                    QtWidgets.QMessageBox.information(self, '成功', '資料庫備份成功。')
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, '錯誤', f'資料庫備份失敗: {e}')

    def show_font_size_dialog(self):
        dialog = FontSizeDialog(self, self.button_font_size, self.table_font_size, self.input_font_size)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.button_font_size, self.table_font_size, self.input_font_size = dialog.get_values()
            save_font_config(self.button_font_size, self.table_font_size, self.input_font_size)
            self._apply_style()
