from datetime import datetime
from PyQt5 import QtWidgets, QtGui
from database.database import (
    get_all_plate_info, get_all_plates_with_stats,
    delete_plate_info, filter_plate_info
)
from utils.helpers import format_phone_number
from config.constants import MIN_COLUMN_WIDTH


class TableViewHandler:
    def __init__(self, table_view, plate_line_edit, plate_line_edit2, search_combo_box):
        self.table_view = table_view
        self.plate_line_edit = plate_line_edit
        self.plate_line_edit2 = plate_line_edit2
        self.search_combo_box = search_combo_box
        self.plate_line_edit.textChanged.connect(self.filter_table)
        self.plate_line_edit2.textChanged.connect(self.filter_table)
        self.search_combo_box.currentIndexChanged.connect(self.filter_table)
        self.load_data()

    def load_data(self):
        """Load all data with stats into the table."""
        rows = get_all_plates_with_stats()
        self._populate_table_with_stats(rows)
        self.table_view.resizeRowsToContents()
        self._ensure_min_column_widths()

    def _populate_table_with_stats(self, rows):
        self.table_view.setRowCount(len(rows))
        today = datetime.now().date()
        for row_idx, (part1, part2, phone, note, brand, vip, last_visit) in enumerate(rows):
            plate_text = f"{part1}-{part2}"
            if vip:
                plate_text = f"★ {plate_text}"

            self.table_view.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(plate_text))
            self.table_view.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(format_phone_number(phone)))
            note_item = QtWidgets.QTableWidgetItem(note)
            note_item.setToolTip(f"<span style='font-size: 14pt;'>{note}</span>")
            self.table_view.setItem(row_idx, 2, note_item)

            # Last visit column
            if last_visit:
                last_date = datetime.strptime(last_visit, '%Y-%m-%d').date()
                days = (today - last_date).days
                if days == 0:
                    visit_text = "今天"
                elif days == 1:
                    visit_text = "昨天"
                else:
                    visit_text = f"{days}天前"
                visit_item = QtWidgets.QTableWidgetItem(visit_text)
                if days >= 30:
                    visit_item.setForeground(QtGui.QColor("#DC2626"))
                elif days == 0:
                    visit_item.setForeground(QtGui.QColor("#059669"))
            else:
                visit_item = QtWidgets.QTableWidgetItem("無紀錄")
                visit_item.setForeground(QtGui.QColor("#9CA3AF"))
            self.table_view.setItem(row_idx, 3, visit_item)

    def _populate_table(self, data):
        """Populate from filter results (no stats join)."""
        self.table_view.setRowCount(len(data))
        for row, (plate, phone_number, note, brand) in enumerate(data):
            self.table_view.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
            self.table_view.setItem(row, 1, QtWidgets.QTableWidgetItem(format_phone_number(phone_number)))
            note_item = QtWidgets.QTableWidgetItem(note)
            note_item.setToolTip(f"<span style='font-size: 14pt;'>{note}</span>")
            self.table_view.setItem(row, 2, note_item)
            self.table_view.setItem(row, 3, QtWidgets.QTableWidgetItem(""))

    def _ensure_min_column_widths(self):
        for col in range(self.table_view.columnCount()):
            if self.table_view.columnWidth(col) < MIN_COLUMN_WIDTH:
                self.table_view.setColumnWidth(col, MIN_COLUMN_WIDTH)

    def filter_table(self):
        text1 = self.plate_line_edit.text().lower()
        text2 = self.plate_line_edit2.text().lower()
        search_mode = self.search_combo_box.currentText()
        if search_mode == "電話查詢":
            data = filter_plate_info("", "", text1, search_mode)
        else:
            data = filter_plate_info(text1, text2, "", search_mode)
        self._populate_table(data)
        self.table_view.resizeRowsToContents()
        self._ensure_min_column_widths()

    def update_row(self, row, plate, phone_number, note, brand=""):
        self.table_view.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
        self.table_view.setItem(row, 1, QtWidgets.QTableWidgetItem(format_phone_number(phone_number)))
        note_item = QtWidgets.QTableWidgetItem(note)
        note_item.setToolTip(f"<span style='font-size: 14pt;'>{note}</span>")
        self.table_view.setItem(row, 2, note_item)

    def delete_selected_row(self):
        selected_row = self.table_view.currentRow()
        if selected_row >= 0:
            plate = self.table_view.item(selected_row, 0).text().replace("★ ", "")
            phone_item = self.table_view.item(selected_row, 1)
            phone = phone_item.text().replace('-', '') if phone_item else ""
            part1, part2 = plate.split('-')
            delete_plate_info(part1, part2, phone)
            self.table_view.removeRow(selected_row)
