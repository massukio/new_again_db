"""使用說明 (user manual) shown inside the program.

The manual is ``assets/manual/manual.html`` plus screenshots with highlights
made by ``tools/make_manual.py``. The window is not modal, so the user can keep
it next to the program and follow the steps. It can also be saved as a PDF to
print. This file is the same in autorepair_db and new_again_db.
"""
import os
import re

from PyQt5 import QtCore, QtGui, QtPrintSupport, QtWidgets

from app import config
from app.ui.style import sized
from app.ui.widgets import ask, button, fit_to_screen, warn

MANUAL_DIR = config.resource_path("assets", "manual")
MANUAL_FILE = os.path.join(MANUAL_DIR, "manual.html")
PDF_FONT = "Microsoft JhengHei"
_IMG = re.compile(r'<img src="([^"]+)"([^>]*)>')


def manual_html() -> str:
    try:
        with open(MANUAL_FILE, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return "<p>找不到使用說明檔案。</p>"


def image_names(html: str) -> list:
    return [m[0] for m in _IMG.findall(html)]


def fit_images(html: str, max_width: int) -> str:
    """Give every screenshot a width that fits (never wider than the picture itself)."""
    def repl(m):
        size = QtGui.QImageReader(os.path.join(MANUAL_DIR, m.group(1))).size()
        w = min(size.width(), max_width) if size.isValid() else max_width
        return f'<img src="{m.group(1)}" width="{max(w, 50)}"{m.group(2)}>'
    return _IMG.sub(repl, html)


def render_pdf(path: str) -> None:
    """Write the manual (with its pictures) to an A4 PDF."""
    printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
    printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    printer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    printer.setPageMargins(15, 15, 15, 15, QtPrintSupport.QPrinter.Millimeter)
    doc = QtGui.QTextDocument()
    doc.setDefaultFont(QtGui.QFont(PDF_FONT, 11))
    page = printer.pageRect(QtPrintSupport.QPrinter.Point).size()
    # printed: every chapter starts on a new page (the 目錄 heading has no style attribute)
    html = manual_html().replace('<h2 style="', '<h2 style="page-break-before: always; ')
    for name in set(image_names(html)):
        doc.addResource(QtGui.QTextDocument.ImageResource, QtCore.QUrl(name),
                        QtGui.QImage(os.path.join(MANUAL_DIR, name)))
    doc.setHtml(fit_images(html, int(page.width()) - 4))
    doc.setPageSize(page)
    doc.print_(printer)


class ManualDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._html = manual_html()
        self._width = 0
        self._anchor = "toc"
        self._timer = QtCore.QTimer(self)  # first: style events arrive while building the window
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._render)
        self.setWindowTitle(f"{config.APP_NAME} 使用說明")
        self.setWindowFlags((self.windowFlags() | QtCore.Qt.WindowMinMaxButtonsHint)
                            & ~QtCore.Qt.WindowContextHelpButtonHint)
        lay = QtWidgets.QVBoxLayout(self)
        sized(lay, "setContentsMargins", 16, 12, 16, 12)
        sized(lay, "setSpacing", 10)
        self.view = QtWidgets.QTextBrowser()
        self.view.setProperty("role", "manual")
        self.view.setSearchPaths([MANUAL_DIR])
        self.view.setOpenLinks(True)
        self.view.setOpenExternalLinks(False)
        lay.addWidget(self.view, 1)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(button("回到目錄", slot=lambda: self.go("toc")))
        row.addStretch(1)
        row.addWidget(button("存成 PDF（可以印出來）", slot=self.save_pdf))
        close = button("關閉", "primary", self.close)
        sized(close, "setMinimumWidth", 160)
        row.addWidget(close)
        lay.addLayout(row)
        fit_to_screen(self, 1120, 900)

    def _render(self):
        width = self.view.viewport().width() - 40
        if width <= 100 or width == self._width:
            return
        bar = self.view.verticalScrollBar()
        ratio = bar.value() / bar.maximum() if bar.maximum() else 0
        self._width = width
        self.view.setHtml(fit_images(self._html, width))
        if self._anchor:
            self.view.scrollToAnchor(self._anchor)
            self._anchor = None
        else:
            bar.setValue(round(ratio * bar.maximum()))

    def go(self, anchor: str):
        """Show the chapter with this anchor (e.g. the page the user is on)."""
        if self._width:
            self.view.scrollToAnchor(anchor)
        else:
            self._anchor = anchor  # scrolled there once the text is laid out

    def showEvent(self, event):
        super().showEvent(event)
        self._timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._timer.start()

    def changeEvent(self, event):  # font size changed in 設定: lay the pictures out again
        super().changeEvent(event)
        if event.type() in (QtCore.QEvent.StyleChange, QtCore.QEvent.FontChange):
            self._width = 0
            self._timer.start()

    def save_pdf(self):
        start = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.DocumentsLocation) or os.path.expanduser("~")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "使用說明存成 PDF", os.path.join(start, f"{config.APP_NAME}使用說明.pdf"),
            "PDF 檔 (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"  # the save dialog's overwrite question did not see this name
            if os.path.exists(path) and not ask(
                    self, f"這個位置已經有同名的 PDF：\n{path}\n\n要用新的取代它嗎？", "取代檔案",
                    yes="取代", no="不要取代"):
                return
        tmp = path + ".tmp.pdf"
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
            render_pdf(tmp)  # QPrinter fails silently, so check the result
            if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
                raise OSError("PDF 沒有寫出來")
            os.replace(tmp, path)
        except PermissionError:
            warn(self, "存檔失敗：同名的 PDF 可能正開著。\n\n請先關閉那個 PDF，或換一個檔名再試一次。")
            return
        except OSError as e:
            warn(self, f"存檔失敗：{e}\n\n請換一個位置再試一次。")
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
        if ask(self, f"已存成 PDF：\n{path}\n\n要現在打開來看嗎？（可以從那裡列印）", "完成",
               yes="打開來看", no="不用"):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
