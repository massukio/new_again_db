from PyQt5 import QtCore, QtWidgets
from database.database import get_all_plate_info, delete_plate_info, filter_plate_info
from utils.helpers import format_phone_number

class TableViewHandler:
    def __init__(self, table_view, plate_line_edit, plate_line_edit2, search_combo_box):
        self.table_view = table_view
        self.plate_line_edit = plate_line_edit
        self.plate_line_edit2 = plate_line_edit2
        self.search_combo_box = search_combo_box
        self.plate_line_edit.textChanged.connect(self.filter_table)
        self.plate_line_edit2.textChanged.connect(self.filter_table)
        self.search_combo_box.currentIndexChanged.connect(self.filter_table)
        self.table_view.verticalHeader().setVisible(False)  # Hide row numbers
        self.load_data()

    def load_data(self):
        """Load data and resize rows to fit content (initial load only)."""
        data = get_all_plate_info()
        self._populate_table(data)
        self.table_view.resizeRowsToContents()  # Only for initial load
        self._set_minimum_column_widths()

    def load_data_preserve_formatting(self, column_widths=None, row_heights=None):
        """Load data while preserving table formatting."""
        # Store current formatting if not provided
        if column_widths is None:
            column_widths = [self.table_view.columnWidth(i) for i in range(self.table_view.columnCount())]
        if row_heights is None:
            row_heights = [self.table_view.rowHeight(i) for i in range(self.table_view.rowCount())]
        
        data = get_all_plate_info()
        self._populate_table(data)
        
        # Restore formatting - column widths first
        for i, width in enumerate(column_widths):
            if i < self.table_view.columnCount():
                self.table_view.setColumnWidth(i, width)
        
        # Then restore row heights (this is the key!)
        for i, height in enumerate(row_heights):
            if i < self.table_view.rowCount():
                self.table_view.setRowHeight(i, height)
        
        self._set_minimum_column_widths()

    def _set_minimum_column_widths(self):
        for column in range(self.table_view.columnCount()):
            current_width = self.table_view.columnWidth(column)
            if current_width < 150:
                self.table_view.setColumnWidth(column, 150)  # Set minimum width to 150

    def _populate_table(self, data):
        self.table_view.setRowCount(len(data))
        for row, (plate, phone_number, note) in enumerate(data):
            formatted_phone_number = format_phone_number(phone_number)
            self.table_view.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
            self.table_view.setItem(row, 1, QtWidgets.QTableWidgetItem(formatted_phone_number))
            note_item = QtWidgets.QTableWidgetItem(note)
            note_item.setToolTip(f"<span style='font-size: 14pt;'>{note}</span>")  # Add tooltip with larger font
            self.table_view.setItem(row, 2, note_item)

    def _populate_table_and_resize(self, data):
        """Populate table and resize rows to contents."""
        self._populate_table(data)
        self.table_view.resizeRowsToContents()  # Ensure rows are resized to fit content

    def filter_table(self):
        # Store current formatting
        column_widths = [self.table_view.columnWidth(i) for i in range(self.table_view.columnCount())]
        row_heights = [self.table_view.rowHeight(i) for i in range(self.table_view.rowCount())]
        
        part1_filter_text = phone_filter_text = \
            self.plate_line_edit.text().lower()
        part2_filter_text = self.plate_line_edit2.text().lower()
        search_mode = self.search_combo_box.currentText()
        if search_mode == "電話查詢":
            data = filter_plate_info("", "", phone_filter_text, search_mode)
        else:
            data = filter_plate_info(part1_filter_text, part2_filter_text, "", search_mode)
        self._populate_table(data)
        
        # Restore formatting
        for i, width in enumerate(column_widths):
            if i < self.table_view.columnCount():
                self.table_view.setColumnWidth(i, width)
        for i, height in enumerate(row_heights):
            if i < self.table_view.rowCount():
                self.table_view.setRowHeight(i, height)
        
        self._set_minimum_column_widths()

    def update_row(self, row, plate, phone_number, note):
        formatted_phone_number = format_phone_number(phone_number)
        self.table_view.setItem(row, 0, QtWidgets.QTableWidgetItem(plate))
        self.table_view.setItem(row, 1, QtWidgets.QTableWidgetItem(formatted_phone_number))
        note_item = QtWidgets.QTableWidgetItem(note)
        note_item.setToolTip(f"<span style='font-size: 14pt;'>{note}</span>")  # Update tooltip with larger font
        self.table_view.setItem(row, 2, note_item)

    def delete_selected_row(self):
        selected_row = self.table_view.currentRow()
        if selected_row >= 0:
            plate_info = self.table_view.item(selected_row, 0).text()
            phone_number_item = self.table_view.item(selected_row, 1)
            phone_number = phone_number_item.text().replace('-', '') if phone_number_item else ""
            part1, part2 = plate_info.split('-')
            delete_plate_info(part1, part2, phone_number)
            self.table_view.removeRow(selected_row)