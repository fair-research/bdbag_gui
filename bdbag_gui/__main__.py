import sys

from PyQt5.QtWidgets import QApplication
from bdbag_gui.ui import main_window as mw


def main():
    try:
        app = QApplication(sys.argv)
        mainWindow = mw.MainWindow()
        mainWindow.show()
        ret = app.exec()
        return ret
    except Exception as e:
        print(e)

if __name__ == '__main__':
    sys.exit(main())
