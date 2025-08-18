import sys
from PyQt5 import QtWidgets
from core.application import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.showMaximized()  # Maximize the window by default
    
    # Ensure the application exits cleanly
    exit_code = app.exec_()
    main_window.close()  # Ensure the main window is closed
    sys.exit(exit_code)

