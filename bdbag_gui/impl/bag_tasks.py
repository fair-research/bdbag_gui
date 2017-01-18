from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from bdbag import bdbag_api as bdb
from bdbag_gui.impl.async_task import async_execute


class BagTask(QtCore.QObject):
    def __init__(self, parent=None):
        super(BagTask, self).__init__(parent)
        self.rid = 0
        self.request = None

    def init_request(self):
        if self.request is not None:
            self.request.cancelled = True
            self.request = None
        self.rid += 1


class BagCreateOrUpdateTask(BagTask):
    status_update_signal = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super(BagCreateOrUpdateTask, self).__init__(parent)
        self.update = False

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit(True, "Bag %s completed successfully" % "update" if self.update else "creation")

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit(False, "Bag %s error: %s" % ("update" if self.update else "creation", error))

    def createOrUpdate(self, bagPath, update):
        self.update = update
        self.init_request()
        self.request = async_execute(bdb.make_bag,
                                     [bagPath, ['md5', 'sha256'], update],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagValidateTask(BagTask):

    status_update_signal = pyqtSignal(str)
    progress_update_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(BagValidateTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag validation complete")

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag validation error: %s" % error)

    def progress_callback(self, current, maximum):
        if self.request.cancelled:
            return False

        self.progress_update_signal.emit(current, maximum)
        return True

    def validate(self, bagPath, fast):
        self.init_request()
        self.request = async_execute(bdb.validate_bag,
                                     [bagPath, fast, self.progress_callback],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagFetchTask(BagTask):

    status_update_signal = pyqtSignal(str)
    progress_update_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(BagFetchTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag fetch complete: All file references resolved successfully"
                                       if result else "Bag fetch incomplete: Some file references were not resolved")

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag fetch error: %s" % error)

    def progress_callback(self, current, maximum):
        if self.request.cancelled:
            return False

        self.progress_update_signal.emit(current, maximum)
        return True

    def fetch(self, bagPath, allRefs):
        self.init_request()
        self.request = async_execute(bdb.resolve_fetch,
                                     [bagPath, allRefs, self.progress_callback],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagArchiveTask(BagTask):
    status_update_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(BagArchiveTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag archive complete")

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag archive error: %s" % error)

    def archive(self, bagPath, archiver):
        self.init_request()
        self.request = async_execute(bdb.archive_bag,
                                     [bagPath, archiver],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)
