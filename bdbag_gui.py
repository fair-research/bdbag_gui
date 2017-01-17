import sys
from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication


def main():
    try:
        app = QApplication(sys.argv)
        mainWindow = MainWindow()
        mainWindow.show()
        ret = app.exec()
        return ret
    except Exception as e:
        print(e)

if __name__ == '__main__':
    sys.exit(main())
