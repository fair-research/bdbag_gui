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
    status_update_signal = pyqtSignal(str, bool, bool)

    def __init__(self, parent=None):
        super(BagCreateOrUpdateTask, self).__init__(parent)
        self.update = False

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag %s completed successfully" % ("update" if self.update else "creation"),
                                       True, self.update)

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag %s error: %s" % ("update" if self.update else "creation", error),
                                       False, self.update)

    def createOrUpdate(self, bagPath, update, config_file):
        self.update = update
        self.init_request()
        self.request = async_execute(bdb.make_bag,
                                     [bagPath, ['md5', 'sha256'], update, True, False, None, None, None, config_file],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagRevertTask(BagTask):
    status_update_signal = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super(BagRevertTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag reverted successfully", True)

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag reversion failed", False)

    def revert(self, bagPath):
        self.init_request()
        self.request = async_execute(bdb.revert_bag,
                                     [bagPath],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagValidateTask(BagTask):

    status_update_signal = pyqtSignal(str, bool)
    progress_update_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(BagValidateTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag validation complete", True)

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag validation error: %s" % error, False)

    def progress_callback(self, current, maximum):
        if self.request.cancelled:
            return False

        self.progress_update_signal.emit(current, maximum)
        return True

    def validate(self, bagPath, fast, config_file):
        self.init_request()
        self.request = async_execute(bdb.validate_bag,
                                     [bagPath, fast, self.progress_callback, config_file],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagFetchTask(BagTask):

    status_update_signal = pyqtSignal(str, bool)
    progress_update_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(BagFetchTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag fetch complete: All file references resolved successfully" if result else
                                       "Bag fetch incomplete: Some file references were not resolved", True)

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag fetch error: %s" % error, False)

    def progress_callback(self, current, maximum):
        if self.request.cancelled:
            return False

        self.progress_update_signal.emit(current, maximum)
        return True

    def fetch(self, bagPath, allRefs, keychainFile, configFile):
        self.init_request()
        self.request = async_execute(bdb.resolve_fetch,
                                     [bagPath, allRefs, self.progress_callback, keychainFile, configFile],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)


class BagArchiveTask(BagTask):
    status_update_signal = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super(BagArchiveTask, self).__init__(parent)

    def success_callback(self, rid, result):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag archive complete", True)

    def error_callback(self, rid, error):
        if rid != self.rid:
            return
        self.status_update_signal.emit("Bag archive error: %s" % error, False)

    def archive(self, bagPath, archiver):
        self.init_request()
        self.request = async_execute(bdb.archive_bag,
                                     [bagPath, archiver],
                                     self.rid,
                                     self.success_callback,
                                     self.error_callback)
