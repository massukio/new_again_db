"""Build assets/app.ico (16-256 px) and assets/app.png: white 「洗」 on a teal rounded square.
Replace with a designed icon later by drawing it here or loading an image instead."""
import io
import os
import sys

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render(size=512) -> Image.Image:
    img = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32)
    img.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setRenderHint(QtGui.QPainter.TextAntialiasing)
    grad = QtGui.QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0, QtGui.QColor("#13849C"))
    grad.setColorAt(1, QtGui.QColor("#0B5566"))
    p.setBrush(grad)
    p.setPen(QtCore.Qt.NoPen)
    m = int(size * 0.04)
    p.drawRoundedRect(m, m, size - 2 * m, size - 2 * m, size * 0.22, size * 0.22)
    font = QtGui.QFont("Microsoft JhengHei")
    font.setBold(True)
    font.setPixelSize(int(size * 0.58))
    p.setFont(font)
    p.setPen(QtGui.QColor("white"))
    p.drawText(QtCore.QRect(0, -int(size * 0.02), size, size), QtCore.Qt.AlignCenter, "洗")
    p.end()
    buf = QtCore.QBuffer()
    buf.open(QtCore.QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


def main():
    app = QtWidgets.QApplication(sys.argv)  # noqa: F841 - must stay alive while drawing
    im = render()
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    im.resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, "assets", "app.png"))
    im.resize((256, 256), Image.LANCZOS).save(
        os.path.join(ROOT, "assets", "app.ico"),
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote assets/app.ico and assets/app.png")


if __name__ == "__main__":
    main()
