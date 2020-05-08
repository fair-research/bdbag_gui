from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from bdbag import bdbag_api as bdb
from bdbag_gui.impl.async_task import Task, async_execute


class BagTask(QtCore.QObject):
    status_update_signal = pyqtSignal(str, bool)
    progress_update_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(BagTask, self).__init__(parent)
        self.task = None

    def start(self):
        async_execute(self.task)

    def cancel(self):
        self.task.cancel()

    def terminate(self):
        self.task.terminate()

    def set_status(self, status, success):
        self.status_update_signal.emit(status, success)

    def result_callback(self, result, success):
        self.set_status(result, success)

    def progress_callback(self, current, maximum):
        if self.task.canceled:
            return False

        self.progress_update_signal.emit(current, maximum)
        return True


class BagCreateOrUpdateTask(BagTask):

    def __init__(self, parent=None):
        super(BagCreateOrUpdateTask, self).__init__(parent)
        self.update = False

    def result_callback(self, result, success):
        status = "Bag %s completed successfully." % ("update" if self.update else "creation") if success else \
            "Bag %s error: %s" % ("update" if self.update else "creation", result)
        self.set_status(status, success)

    def createOrUpdate(self, bag_path, update, config_file):
        self.update = update
        self.task = Task(bdb.make_bag,
                         [bag_path, ['md5', 'sha256'], update, True, False, None, None, None, config_file],
                         self.result_callback)
        self.start()


class BagRevertTask(BagTask):

    def __init__(self, parent=None):
        super(BagRevertTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = "Bag reverted successfully." if success else "Bag reversion failed: %s" % result
        self.set_status(status, success)

    def revert(self, bag_path):
        self.task = Task(bdb.revert_bag,
                         [bag_path],
                         self.result_callback)
        self.start()


class BagValidateTask(BagTask):

    def __init__(self, parent=None):
        super(BagValidateTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = "Bag validation complete." if success else "Bag validation error: %s" % result
        self.set_status(status, success)

    def validate(self, bag_path, fast, config_file):
        self.task = Task(bdb.validate_bag,
                         [bag_path, fast, self.progress_callback, config_file],
                         self.result_callback)
        self.start()


class BagFetchTask(BagTask):

    def __init__(self, parent=None):
        super(BagFetchTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = ("Bag fetch complete: All file references resolved successfully." if result else
                  "Bag fetch incomplete: Some file references were not resolved.") if success else \
            "Bag fetch error: %s" % result
        self.set_status(status, success)

    def fetch(self, bag_path, fetch_all, keychain_file, config_file):
        self.task = Task(bdb.resolve_fetch,
                         [bag_path, fetch_all, self.progress_callback, keychain_file, config_file],
                         self.result_callback)
        self.start()


class BagArchiveTask(BagTask):

    def __init__(self, parent=None):
        super(BagArchiveTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = "Bag archive complete." if success else "Bag archive error: %s" % result
        self.set_status(status, success)

    def archive(self, bag_path, archiver):
        self.task = Task(bdb.archive_bag,
                         [bag_path, archiver],
                         self.result_callback)
        self.start()


class BagExtractTask(BagTask):

    def __init__(self, parent=None):
        super(BagExtractTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = "File extraction complete." if success else "File extraction error: %s" % result
        self.set_status(status, success)

    def extract(self, bag_path, output_path=None):
        self.task = Task(bdb.extract_bag,
                         [bag_path, output_path],
                         self.result_callback)
        self.start()


class BagMaterializeTask(BagTask):

    def __init__(self, parent=None):
        super(BagMaterializeTask, self).__init__(parent)

    def result_callback(self, result, success):
        status = "Bag materialization complete." if success else "Bag materialization error: %s" % result
        self.set_status(status, success)

    def materialize(self, bag_path, output_path=None):
        self.task = Task(bdb.materialize,
                         [bag_path, output_path, self.progress_callback, self.progress_callback],
                         self.result_callback)
        self.start()
