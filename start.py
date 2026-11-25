"""Entry point: python start.py  (or double-click the built exe)."""
import datetime
import os
import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets

from app import backup, config
from app.db import open_database


def _log_path() -> str:
    try:
        return os.path.join(config.data_dir(), config.LOG_FILENAME)
    except OSError:
        return os.path.join(os.path.expanduser("~"), f"{config.APP_NAME}_{config.LOG_FILENAME}")


def _log(exc) -> None:
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}]\n{text}")
    except OSError:
        pass


def _excepthook(exc_type, exc, tb):
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}]\n{text}")
    except OSError:
        pass
    if QtWidgets.QApplication.instance() is not None:
        QtWidgets.QMessageBox.critical(
            None, "發生錯誤", f"程式發生錯誤，請把以下檔案給維護人員：\n{_log_path()}\n\n{exc}")


def main() -> int:
    sys.excepthook = _excepthook
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    icon_path = config.resource_path("assets", "app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Chinese, QtCore.QLocale.Taiwan))
    translator = QtCore.QTranslator(app)
    if translator.load("qtbase_zh_TW", QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)

    # one copy at a time: two copies writing the same database would block each other
    try:
        folder = config.data_dir()
    except OSError as e:
        QtWidgets.QMessageBox.critical(
            None, "無法開啟資料", f"找不到可以存放資料的資料夾。\n請把程式放到「文件」或桌面再打開。\n\n{e}")
        return 1
    lock = QtCore.QLockFile(os.path.join(folder, config.LOCK_FILENAME))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QtWidgets.QMessageBox.information(
            None, config.APP_NAME, f"{config.APP_NAME}已經開著了。\n\n請在下方工作列找到它，點一下就可以回到程式。")
        return 0

    try:
        db, aside = open_database(config.db_path())
    except Exception as e:  # noqa: BLE001 - show any startup problem to the user
        QtWidgets.QMessageBox.critical(None, "無法開啟資料", f"無法開啟資料檔：\n{config.db_path()}\n\n{e}")
        return 1
    if aside:
        QtWidgets.QMessageBox.warning(
            None, "資料檔無法讀取",
            f"原本的資料檔無法讀取，已經另存為：\n{aside}\n\n程式已建立新的資料檔。"
            f"如果有備份檔，請到「備份 / 還原」把資料還原回來。")
    try:
        backup.daily_auto_backup(db, config.auto_backup_dir())
    except Exception as e:  # noqa: BLE001 - auto backup must never block startup
        _excepthook(type(e), e, e.__traceback__)

    from app.ui.main_window import MainWindow
    win = MainWindow(db)
    win.showMaximized()

    told = {"backup_failed": False}

    def hourly_backup():  # the PC may stay on for days: make the new day's backup too
        try:
            backup.daily_auto_backup(db, config.auto_backup_dir())
        except Exception as e:  # noqa: BLE001
            if told["backup_failed"]:
                _log(e)  # already told once: a full disk must not pop up every hour
            else:
                told["backup_failed"] = True
                _excepthook(type(e), e, e.__traceback__)
    backup_timer = QtCore.QTimer()
    backup_timer.timeout.connect(hourly_backup)
    backup_timer.start(60 * 60 * 1000)
    rc = app.exec_()
    db.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
