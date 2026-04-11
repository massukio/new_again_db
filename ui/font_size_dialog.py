from PyQt5 import QtWidgets


class FontSizeDialog(QtWidgets.QDialog):
    def __init__(self, parent, button_size, table_size, input_size):
        super().__init__(parent)
        self.setWindowTitle("調整字體大小")
        self.setMinimumWidth(350)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        self.button_spin = self._add_row(layout, "按鈕字體大小:", button_size)
        self.table_spin = self._add_row(layout, "表格字體大小:", table_size)
        self.input_spin = self._add_row(layout, "輸入欄字體大小:", input_size)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("確定")
        button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _add_row(self, layout, label_text, value):
        label = QtWidgets.QLabel(label_text)
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(10, 300)
        spinbox.setValue(value)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(label)
        row.addWidget(spinbox)
        layout.addLayout(row)
        return spinbox

    def get_values(self):
        return self.button_spin.value(), self.table_spin.value(), self.input_spin.value()
