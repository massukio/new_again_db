"""
Entry point. Runs bootstrap to ensure environment, then launches app inside venv.
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe") if sys.platform == "win32" \
    else os.path.join(VENV_DIR, "bin", "python")


def _in_venv():
    return sys.prefix != sys.base_prefix


def main():
    if _in_venv():
        # Inside venv — launch the app
        from PyQt5 import QtWidgets
        from core.application import MainWindow

        app = QtWidgets.QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        main_window.showMaximized()

        exit_code = app.exec_()
        main_window.close()
        sys.exit(exit_code)
    else:
        # Outside venv — bootstrap then relaunch inside venv
        from bootstrap import setup
        if not setup():
            print("Environment setup failed.")
            sys.exit(1)

        # Re-exec inside the venv python
        os.execv(VENV_PYTHON, [VENV_PYTHON, __file__])


if __name__ == "__main__":
    main()
