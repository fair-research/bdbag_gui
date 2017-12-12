import sys
import traceback
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory, QMessageBox
from bagit import BagError
from bdbag import get_typed_exception
from bdbag_gui.ui import main_window as mw
from bdbag_gui import resources


def excepthook(etype, value, tb):
    sys.stderr.write(get_typed_exception(value))
    if isinstance(value, BagError) or isinstance(value, RuntimeError):
        return
    traceback.print_tb(tb)
    msg = QMessageBox()
    msg.setText(str(value))
    msg.setStandardButtons(QMessageBox.Close)
    msg.setWindowTitle("Unhandled Exception: %s" % etype.__name__)
    msg.setIcon(QMessageBox.Critical)
    msg.setDetailedText('\n'.join(traceback.format_exception(etype, value, tb)))
    msg.exec_()


def main():
    sys.excepthook = excepthook
    QApplication.setDesktopSettingsAware(False)
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setWindowIcon(QIcon(":/images/bag.png"))
    mainWindow = mw.MainWindow()
    mainWindow.show()
    ret = app.exec()
    return ret


if __name__ == '__main__':
    sys.exit(main())
