# -*- mode: python ; coding: utf-8 -*-
# Build:  pyinstaller --noconfirm new_again_db.spec   (or run build_exe.bat)
import os

icon = os.path.join("assets", "app.ico")
datas = [(os.path.join("assets", "brands"), os.path.join("assets", "brands"))]
datas += [(p, "assets") for p in (icon, os.path.join("assets", "app.png")) if os.path.exists(p)]
datas += [(os.path.join("assets", "manual"), os.path.join("assets", "manual"))]  # 使用說明 + pictures

a = Analysis(
    ["start.py"],
    pathex=[],
    datas=datas,
    hiddenimports=[],
    excludes=[
        "tkinter", "unittest", "pydoc", "pytest", "PIL",
        "PyQt5.QtNetwork", "PyQt5.QtQml", "PyQt5.QtQuick", "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtMultimedia", "PyQt5.QtBluetooth", "PyQt5.QtSql", "PyQt5.QtTest",
        "PyQt5.QtDesigner", "PyQt5.QtOpenGL", "PyQt5.QtSvg", "PyQt5.QtXml",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="再新洗車資料庫",
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon=icon if os.path.exists(icon) else None,
)
