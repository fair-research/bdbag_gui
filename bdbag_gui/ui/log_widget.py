from PyQt5.Qt import qApp
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPlainTextEdit
import logging


class QPlainTextEditLogger(logging.Handler):

    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEditLog(parent)

    def emit(self, record):
        msg = self.format(record)
        self.widget.log_update_signal.emit(msg)
        qApp.processEvents()


class QPlainTextEditLog(QPlainTextEdit):
    log_update_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setBackgroundVisible(True)
