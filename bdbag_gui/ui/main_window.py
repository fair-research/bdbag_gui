import os
import json
import logging
import platform

from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import Qt, QDir, QMetaObject, QModelIndex, QThreadPool, QTimer, QMutex, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAction, QMenu, QMenuBar, QMessageBox, QStyle, \
    QProgressBar, QToolBar, QStatusBar, QVBoxLayout, QTreeView, QFileSystemModel, QAbstractItemView, qApp
from PyQt5.QtGui import QIcon
from bdbag import VERSION as BDBAG_VERSION, BAGIT_VERSION, BAGIT_PROFILE_VERSION, bdbag_api as bdb
from bdbag_gui import resources, VERSION
from bdbag_gui.ui import log_widget, options_window
from bdbag_gui.ui.options_window import DEFAULT_OPTIONS, DEFAULT_OPTIONS_FILE
from bdbag_gui.impl import async_task, bag_tasks


# noinspection PyBroadException,PyArgumentList
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.currentTask = None
        self.currentTaskMutex = QMutex()
        self.options = DEFAULT_OPTIONS
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)
        self.ui.logTextBrowser.widget.log_update_signal.connect(self.updateLog)
        self.ui.logTextBrowser.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.ui.logTextBrowser)
        logging.getLogger().setLevel(logging.INFO)

        self.fileSystemModel = QFileSystemModel()
        self.fileSystemModel.setReadOnly(False)
        self.ui.treeView.setModel(self.fileSystemModel)
        self.fileSystemModel.setRootPath(self.fileSystemModel.myComputer())
        self.ui.treeView.setAnimated(True)
        self.ui.treeView.setAcceptDrops(True)
        self.ui.treeView.setAutoScroll(True)
        self.ui.treeView.setAutoExpandDelay(0)
        self.ui.treeView.setSortingEnabled(True)
        self.ui.treeView.sortByColumn(0, Qt.AscendingOrder)
        self.ui.treeView.setColumnWidth(0, 300)

        self.loadOptions()
        homedir_index = self.fileSystemModel.index(self.options.get("current_dir", QDir.home().path()))
        self.ui.treeView.setCurrentIndex(homedir_index)
        self.ui.treeView.setExpanded(homedir_index, True)
        QTimer.singleShot(1300, self.selectionChanged)

        self.enableControls(True)

    def loadOptions(self, options_file=DEFAULT_OPTIONS_FILE):
        if not os.path.isfile(options_file):
            logging.debug("Creating default options file: %s" % options_file)
            self.saveOptions(options_file)

        if os.path.isfile(options_file):
            logging.debug("Loading options file from: %s" % options_file)
            with open(options_file) as of:
                options = of.read()
        else:
            options = json.dumps(DEFAULT_OPTIONS)
            logger.warning("Unable to read options file: [%s]. Using internal defaults." % config_file)

        self.options = json.loads(options)

    def saveOptions(self, options_file=DEFAULT_OPTIONS_FILE):
        logging.debug("Writing options file: %s" % options_file)
        try:
            options_path = os.path.dirname(options_file)
            if not os.path.isdir(options_path):
                try:
                    os.makedirs(options_path, mode=0o750)
                except OSError as error:
                    if error.errno != errno.EEXIST:
                        raise
            with open(options_file, 'w') as of:
                of.write(json.dumps(self.options, indent=4, sort_keys=True))
        except Exception as e:
            logger.warning("Unable to write options file: [%s]. Error: %s" % (options_file, e))

    def checkIfBag(self, silent=False):
        current_path = self.getCurrentPath()
        if not current_path:
            return False
        current_type = self.fileSystemModel.type(self.ui.treeView.currentIndex())
        if current_type == "Drive":
            is_bag = False
        else:
            if os.path.isdir(current_path):
                QApplication.setOverrideCursor(Qt.WaitCursor)
                is_bag = bdb.is_bag(current_path)
                QApplication.restoreOverrideCursor()
                if not silent:
                    self.updateStatus("The directory [%s] is%s a bag." % (current_path, "" if is_bag else " NOT"), True)
            else:
                is_bag = False

        return is_bag

    def checkIfArchive(self, silent=False):
        is_file_archive = False
        current_path = self.getCurrentPath()
        if current_path and os.path.isfile(current_path):
            # simple test based on extension only
            ext = os.path.splitext(current_path)[1]
            if ext in (".zip", ".tar", ".tgz", ".gz", ".bz2"):
                is_file_archive = True

        if is_file_archive and not silent:
            self.updateStatus("The file [%s] is a supported archive format." % current_path, True)

        return is_file_archive

    def setCurrentTask(self, task, can_cancel=True):
        if not self.currentTaskMutex.tryLock(10):
            return False
        self.currentTask = task
        self.bagTaskTriggered(can_cancel)
        return True

    def clearCurrentTask(self):
        if not self.currentTask:
            return
        self.currentTask = None
        self.currentTaskMutex.unlock()

    def getCurrentPath(self):
        return os.path.normpath(os.path.abspath(self.fileSystemModel.filePath(self.ui.treeView.currentIndex())))

    def disableControls(self, can_cancel=True):
        self.ui.actionCancel.setEnabled(can_cancel)
        self.ui.treeView.setEnabled(False)
        self.ui.actionCreateOrUpdate.setEnabled(False)
        self.ui.actionRevert.setEnabled(False)
        self.ui.actionMaterialize.setEnabled(False)
        self.ui.actionFetchMissing.setEnabled(False)
        self.ui.actionFetchAll.setEnabled(False)
        self.ui.actionValidateFast.setEnabled(False)
        self.ui.actionValidateFull.setEnabled(False)
        self.ui.actionArchive.setEnabled(False)
        self.ui.actionDelete.setEnabled(False)
        self.ui.actionOptions.setEnabled(False)

    def enableControls(self, silent=False):
        is_bag = self.checkIfBag(silent)
        is_file_archive = self.checkIfArchive(silent)
        current_path = self.getCurrentPath()
        current_type = self.fileSystemModel.type(self.ui.treeView.currentIndex())
        self.ui.treeView.setEnabled(True)
        self.ui.actionOptions.setEnabled(True)
        self.ui.actionCancel.setEnabled(False)
        self.ui.actionDelete.setEnabled(False if (not current_type or "Drive" == current_type) else True)
        self.ui.toggleCreateOrUpdate(self, is_bag)
        self.ui.actionCreateOrUpdate.setEnabled(
            (os.path.isdir(current_path) and "Drive" != current_type) if current_path else False)
        self.ui.actionRevert.setEnabled(is_bag)
        self.ui.actionMaterialize.setEnabled(is_bag or is_file_archive)
        self.ui.actionFetchMissing.setEnabled(is_bag)
        self.ui.actionFetchAll.setEnabled(is_bag)
        self.ui.actionValidateFast.setEnabled(is_bag)
        self.ui.actionValidateFull.setEnabled(is_bag)
        self.ui.toggleArchiveOrExtract(self, is_bag, is_file_archive)

    def selectionChanged(self):
        self.ui.statusBar.clearMessage()
        self.ui.progressBar.reset()
        self.ui.logTextBrowser.widget.clear()
        self.enableControls()
        self.ui.treeView.scrollTo(self.ui.treeView.currentIndex(), QAbstractItemView.PositionAtCenter)
        self.options["current_dir"] = self.getCurrentPath()

    def closeEvent(self, event):
        self.cancelTasks()
        self.saveOptions()
        event.accept()

    def cancelTasks(self):
        if not self.currentTask:
            return

        self.disableControls()
        self.currentTask.cancel()
        self.statusBar().showMessage("Waiting for background tasks to terminate...")

        while True:
            qApp.processEvents()
            if not self.currentTask and QThreadPool.globalInstance().waitForDone(10):
                break

        self.statusBar().showMessage("All background tasks terminated successfully.")

    @pyqtSlot()
    def bagTaskTriggered(self, can_cancel=True):
        self.ui.progressBar.reset()
        self.ui.progressBar.setTextVisible(can_cancel)
        self.ui.logTextBrowser.widget.clear()
        self.disableControls(can_cancel)

    @pyqtSlot(str)
    def updateStatus(self, status, success=True):
        if success:
            logging.info(status)
        else:
            logging.error(status)
        self.statusBar().showMessage(status)

    @pyqtSlot(str, bool)
    def updateUI(self, status, success=True):
        self.updateStatus(status, success)
        self.clearCurrentTask()
        self.enableControls(True)

    @pyqtSlot(str)
    def updateLog(self, text):
        self.ui.logTextBrowser.widget.appendPlainText(text)

    @pyqtSlot(int, int)
    def updateProgress(self, current, maximum):
        self.ui.progressBar.setRange(1, maximum)
        self.ui.progressBar.setValue(current)
        self.ui.progressBar.repaint()

    @pyqtSlot(bool)
    def on_actionCreateOrUpdate_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return

        if os.path.dirname(current_path) == current_path:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Operation not allowed")
            msg.setText("Bagging of root filesystems prohibited.")
            msg.setInformativeText(
                "The current selection is a filesystem root. It is not possible to create a bag of a filesystem root.")
            msg.exec_()
            return

        if not self.setCurrentTask(bag_tasks.BagCreateOrUpdateTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.createOrUpdate(current_path, self.checkIfBag(), self.options.get("bag_config_file_path"))

    @pyqtSlot(bool)
    def on_actionRevert_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Action")
        msg.setText("Are you sure you want to revert this bag directory?")
        msg.setInformativeText("Reverting a bag directory will cause all manifests to be deleted including fetch.txt, "
                               "if present.\n\nIf a bag contains remote file references, these files will no longer be "
                               "resolvable.\n\nIt is recommended that you either resolve any remote files prior to "
                               "reverting such a bag, or make a backup copy of it first.")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msg.exec_()
        if ret == QMessageBox.Cancel:
            return

        if not self.setCurrentTask(bag_tasks.BagRevertTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.revert(current_path)

    @pyqtSlot(bool)
    def on_actionMaterialize_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return

        if not self.setCurrentTask(bag_tasks.BagMaterializeTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.progress_update_signal.connect(self.updateProgress)
        self.currentTask.materialize(current_path, self.options.get("archive_extract_dir"))
        self.updateStatus("Materialize initiated for bag: [%s] -- Please wait..." % current_path)

    @pyqtSlot(bool)
    def on_actionArchive_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return
        is_bag = self.checkIfBag()
        is_file_archive = self.checkIfArchive()
        if is_file_archive:
            if not self.setCurrentTask(bag_tasks.BagExtractTask(), can_cancel=False):
                return
            self.currentTask.status_update_signal.connect(self.updateUI)
            self.currentTask.extract(current_path, self.options.get("archive_extract_dir"))
            self.updateStatus("Extracting file: [%s] -- Please wait..." % current_path)
        elif is_bag:
            archive_format = self.options.get("archive_format", "zip")
            if not self.setCurrentTask(bag_tasks.BagArchiveTask()):
                return
            self.currentTask.status_update_signal.connect(self.updateUI)
            self.currentTask.archive(current_path, archive_format)
            self.updateStatus("Archive (%s) initiated for bag: [%s] -- Please wait..." %
                              (archive_format.upper(), current_path))

    @pyqtSlot(bool)
    def on_actionValidateFast_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return
        if not self.setCurrentTask(bag_tasks.BagValidateTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.validate(current_path, True, self.options.get("bag_config_file_path"))

    @pyqtSlot(bool)
    def on_actionValidateFull_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return
        if not self.setCurrentTask(bag_tasks.BagValidateTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.progress_update_signal.connect(self.updateProgress)
        self.currentTask.validate(current_path, False, self.options.get("bag_config_file_path"))
        self.updateStatus("Full validation initiated for bag: [%s] -- Please wait..." % current_path)

    @pyqtSlot(bool)
    def on_actionFetchAll_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return
        if not self.setCurrentTask(bag_tasks.BagFetchTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.progress_update_signal.connect(self.updateProgress)
        self.currentTask.fetch(current_path,
                               True,
                               self.options.get("bag_keychain_file_path"),
                               self.options.get("bag_config_file_path"))
        self.updateStatus("Fetch all initiated for bag: [%s] -- Please wait..." % current_path)

    @pyqtSlot(bool)
    def on_actionFetchMissing_triggered(self):
        current_path = self.getCurrentPath()
        if not current_path:
            return
        if not self.setCurrentTask(bag_tasks.BagFetchTask()):
            return
        self.currentTask.status_update_signal.connect(self.updateUI)
        self.currentTask.progress_update_signal.connect(self.updateProgress)
        self.currentTask.fetch(current_path,
                               False,
                               self.options.get("bag_keychain_file_path"),
                               self.options.get("bag_config_file_path"))
        self.updateStatus("Fetch missing initiated for bag: [%s] -- Please wait..." % current_path)

    @pyqtSlot(QModelIndex)
    def on_treeView_clicked(self, index):
        self.selectionChanged()

    @pyqtSlot(bool)
    def on_actionOptions_triggered(self):
        options_window.OptionsDialog.getOptions(self)

    @pyqtSlot(bool)
    def on_actionCancel_triggered(self):
        self.cancelTasks()
        self.ui.progressBar.reset()
        self.enableControls(True)

    @pyqtSlot()
    def on_actionDelete_triggered(self):
        is_dir = self.fileSystemModel.isDir(self.ui.treeView.currentIndex())
        obj = "Directory" if is_dir else "File"
        current_path = self.getCurrentPath()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("%s Deletion Warning" % obj)
        msg.setText("The %s \"%s\" will be deleted." % (obj.lower(), current_path))
        msg.setInformativeText("You are about to DELETE a %s. "
                               "This operation is permanent and CANNOT BE UNDONE.\n\nAre you sure?" % obj.lower())
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Abort)
        ret = msg.exec_()
        if ret == QMessageBox.Ok:
            result = self.fileSystemModel.remove(self.ui.treeView.currentIndex())
            self.updateStatus("%s: [%s]" % (("Successfully deleted" if result else "Failed to delete"),
                                            current_path), result)
            qApp.processEvents()
            QTimer.singleShot(1300, self.selectionChanged)

    @pyqtSlot()
    def on_actionAbout_triggered(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About BDBag GUI")
        msg.setText("Version Information")
        msg.setInformativeText("BDBag GUI: %s\nBDBag: %s\nBagit: %s\nBagit-Profile: %s\n\n"
                               "Python: %s\nPyQt: %s\nPlatform: %s" %
                               (VERSION,
                                BDBAG_VERSION,
                                BAGIT_VERSION,
                                BAGIT_PROFILE_VERSION,
                                platform.python_version(),
                                PYQT_VERSION_STR,
                                platform.platform(aliased=True)))
        msg.setStandardButtons(QMessageBox.Ok)
        ret = msg.exec_()


# noinspection PyArgumentList,PyAttributeOutsideInit
class MainWindowUI(object):

    def setup_ui(self, MainWin):

        # Main Window
        MainWin.setObjectName("MainWindow")
        MainWin.setWindowTitle(MainWin.tr("BDBag"))
        MainWin.resize(700, 600)
        self.centralWidget = QWidget(MainWin)
        self.centralWidget.setObjectName("centralWidget")
        MainWin.setCentralWidget(self.centralWidget)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")

        # Actions

        # Materialize
        self.actionMaterialize = QAction(MainWin)
        self.actionMaterialize.setObjectName("actionMaterialize")
        self.actionMaterialize.setText(MainWin.tr("Materialize"))
        self.actionMaterialize.setToolTip(
            MainWin.tr("Extract, fetch, and validate a bag archive or directory in a single command."))
        self.actionMaterialize.setShortcut(MainWin.tr("Ctrl+M"))

        # Validate Fast
        self.actionValidateFast = QAction(MainWin)
        self.actionValidateFast.setObjectName("actionValidateFast")
        self.actionValidateFast.setText(MainWin.tr("Validate: Fast"))
        self.actionValidateFast.setToolTip(
            MainWin.tr("Perform fast validation by checking the payload file counts and sizes against the Payload-0xum "
                       "value from the bag manifest."))
        self.actionValidateFast.setShortcut(MainWin.tr("Ctrl+F"))

        # Validate Full
        self.actionValidateFull = QAction(MainWin)
        self.actionValidateFull.setObjectName("actionValidateFull")
        self.actionValidateFull.setText(MainWin.tr("Validate: Full"))
        self.actionValidateFull.setToolTip(
            MainWin.tr("Perform full validation by calculating checksums for all files and comparing them against "
                       "entries in the bag manifest(s)."))
        self.actionValidateFull.setShortcut(MainWin.tr("Ctrl+V"))

        # Fetch Missing
        self.actionFetchMissing = QAction(MainWin)
        self.actionFetchMissing.setObjectName("actionFetchMissing")
        self.actionFetchMissing.setText(MainWin.tr("Fetch: Missing"))
        self.actionFetchMissing.setToolTip(
            MainWin.tr("Fetch only those remote files that are not already present in the bag."))
        self.actionFetchMissing.setShortcut(MainWin.tr("Ctrl+P"))

        # Fetch All
        self.actionFetchAll = QAction(MainWin)
        self.actionFetchAll.setObjectName("actionFetchAll")
        self.actionFetchAll.setText(MainWin.tr("Fetch: All"))
        self.actionFetchAll.setToolTip(
            MainWin.tr("Fetch all remote files, even if they are already present in the bag."))
        self.actionFetchAll.setShortcut(MainWin.tr("Ctrl+A"))

        # Archive
        self.actionArchive = QAction(MainWin)
        self.actionArchive.setObjectName("actionArchive")
        self.actionArchive.setText(MainWin.tr("Archive"))
        self.actionArchive.setToolTip(MainWin.tr("Create a single file compressed archive of the bag."))
        self.actionArchive.setShortcut(MainWin.tr("Ctrl+Z"))

        # Create/Update
        self.actionCreateOrUpdate = QAction(MainWin)
        self.actionCreateOrUpdate.setObjectName("actionCreateOrUpdate")

        # Revert
        self.actionRevert = QAction(MainWin)
        self.actionRevert.setObjectName("actionRevert")
        self.actionRevert.setText(MainWin.tr("Revert"))
        self.actionRevert.setToolTip(
            MainWin.tr("Revert a bag directory back to a normal directory."))
        self.actionRevert.setShortcut(MainWin.tr("Ctrl+R"))

        # Delete
        self.actionDelete = QAction(MainWin)
        self.actionDelete.setObjectName("actionDelete")
        self.actionDelete.setText(MainWin.tr("Delete"))
        self.actionDelete.setToolTip(MainWin.tr("Delete"))
        self.actionDelete.setShortcut(MainWin.tr("Ctrl+D"))

        # Cancel
        self.actionCancel = QAction(MainWin)
        self.actionCancel.setObjectName("actionCancel")
        self.actionCancel.setText(MainWin.tr("Cancel"))
        self.actionCancel.setToolTip(MainWin.tr("Cancel the current background task."))
        self.actionCancel.setShortcut(MainWin.tr("Ctrl+C"))

        # Options
        self.actionOptions = QAction(MainWin)
        self.actionOptions.setObjectName("actionOptions")
        self.actionOptions.setText(MainWin.tr("Options"))
        self.actionOptions.setToolTip(MainWin.tr("Configuration options."))
        self.actionOptions.setShortcut(MainWin.tr("Ctrl+O"))

        # About
        self.actionAbout = QAction(MainWin)
        self.actionAbout.setObjectName("actionAbout")
        self.actionAbout.setText(MainWin.tr("About"))
        self.actionAbout.setToolTip(MainWin.tr("Show version information."))
        self.actionAbout.setShortcut(MainWin.tr("Ctrl+B"))

        # Tree View
        self.treeView = QTreeView(self.centralWidget)
        self.treeView.setObjectName("treeView")
        self.treeView.setStyleSheet(
            """
            QTreeView {
                    border: 2px solid grey;
                    border-radius: 5px;
            }
            """)
        self.verticalLayout.addWidget(self.treeView)

        # Log Widget

        self.logTextBrowser = log_widget.QPlainTextEditLogger(self.centralWidget)
        self.logTextBrowser.widget.setObjectName("logTextBrowser")
        self.logTextBrowser.widget.setStyleSheet(
            """
            QPlainTextEdit {
                    border: 2px solid grey;
                    border-radius: 5px;
                    background-color: lightgray;
            }
            """)
        self.verticalLayout.addWidget(self.logTextBrowser.widget)

        # Menu Bar

        self.menuBar = QMenuBar(MainWin)
        self.menuBar.setObjectName("menuBar")
        MainWin.setMenuBar(self.menuBar)

        # Bag Menu
        self.menuBag = QMenu(self.menuBar)
        self.menuBag.setObjectName("menuBag")
        self.menuBag.setTitle(MainWin.tr("Bag"))

        # Fetch Menu
        self.menuFetch = QMenu(self.menuBag)
        self.menuFetch.setObjectName("menuFetch")
        self.menuFetch.setTitle(MainWin.tr("Fetch"))
        self.menuFetch.addAction(self.actionFetchMissing)
        self.menuFetch.addAction(self.actionFetchAll)

        # Validate Menu
        self.menuValidate = QMenu(self.menuBag)
        self.menuValidate.setObjectName("menuValidate")
        self.menuValidate.setTitle(MainWin.tr("Validate"))
        self.menuValidate.addAction(self.actionValidateFast)
        self.menuValidate.addAction(self.actionValidateFull)

        # Populate Bag menu
        self.menuBar.addAction(self.menuBag.menuAction())
        self.menuBag.addAction(self.actionMaterialize)
        self.menuBag.addAction(self.menuFetch.menuAction())
        self.menuBag.addAction(self.menuValidate.menuAction())
        self.menuBag.addAction(self.actionArchive)
        self.menuBag.addAction(self.actionCreateOrUpdate)
        self.menuBag.addAction(self.actionRevert)
        self.menuBag.addAction(self.actionDelete)
        self.menuBag.addAction(self.actionCancel)
        self.menuBag.addAction(self.actionOptions)

        # Help Menu
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuHelp.setTitle(MainWin.tr("Help"))
        self.menuHelp.addAction(self.actionAbout)
        self.menuBar.addAction(self.menuHelp.menuAction())

        # Tool Bar

        self.mainToolBar = QToolBar(MainWin)
        self.mainToolBar.setObjectName("mainToolBar")
        self.mainToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.mainToolBar.setContextMenuPolicy(Qt.PreventContextMenu)
        MainWin.addToolBar(Qt.TopToolBarArea, self.mainToolBar)

        # Materialize
        self.mainToolBar.addAction(self.actionMaterialize)
        self.actionMaterialize.setIcon(
            self.actionMaterialize.parentWidget().style().standardIcon(getattr(QStyle, "SP_MediaPlay")))

        # Fetch
        self.mainToolBar.addAction(self.actionFetchMissing)
        self.actionFetchMissing.setIcon(
            self.actionFetchMissing.parentWidget().style().standardIcon(getattr(QStyle, "SP_ArrowDown")))
        self.mainToolBar.addAction(self.actionFetchAll)
        self.actionFetchAll.setIcon(
            self.actionFetchAll.parentWidget().style().standardIcon(getattr(QStyle, "SP_ArrowDown")))

        # Validate
        self.mainToolBar.addAction(self.actionValidateFast)
        self.actionValidateFast.setIcon(
            self.actionValidateFast.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogApplyButton")))
        self.mainToolBar.addAction(self.actionValidateFull)
        self.actionValidateFull.setIcon(
            self.actionValidateFull.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogApplyButton")))

        # Archive
        self.mainToolBar.addAction(self.actionArchive)
        self.actionArchive.setIcon(
            self.actionArchive.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogSaveButton")))

        # Create/Update
        self.mainToolBar.addAction(self.actionCreateOrUpdate)
        self.actionCreateOrUpdate.setIcon(
            self.actionCreateOrUpdate.parentWidget().style().standardIcon(getattr(QStyle, "SP_FileDialogNewFolder")))

        # Revert
        self.mainToolBar.addAction(self.actionRevert)
        self.actionRevert.setIcon(
            self.actionRevert.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogOkButton")))

        # Delete
        self.mainToolBar.addAction(self.actionDelete)
        self.actionDelete.setIcon(
            self.actionDelete.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogDiscardButton")))

        # Cancel
        self.mainToolBar.addAction(self.actionCancel)
        self.actionCancel.setIcon(
            self.actionCancel.parentWidget().style().standardIcon(getattr(QStyle, "SP_BrowserStop")))

        # Options
        self.mainToolBar.addAction(self.actionOptions)
        self.actionOptions.setIcon(
            self.actionOptions.parentWidget().style().standardIcon(getattr(QStyle, "SP_FileDialogDetailedView")))

        # Status Bar

        self.statusBar = QStatusBar(MainWin)
        self.statusBar.setToolTip("")
        self.statusBar.setStatusTip("")
        self.statusBar.setObjectName("statusBar")
        MainWin.setStatusBar(self.statusBar)

        # Progress Bar

        self.progressBar = QProgressBar(self.centralWidget)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setStyleSheet(
            """
            QProgressBar {
                    border: 2px solid grey;
                    border-radius: 5px;
                    text-align: center;
            }
            QProgressBar::chunk {
                    background-color: cornflowerblue;
                    width: 15px;
                    margin: 0.5px;
            }
            """)
        self.verticalLayout.addWidget(self.progressBar)

        # finalize UI setup
        QMetaObject.connectSlotsByName(MainWin)

    def toggleCreateOrUpdate(self, MainWin, is_bag):
        if is_bag:
            self.actionCreateOrUpdate.setText(MainWin.tr("Update"))
            self.actionCreateOrUpdate.setToolTip(MainWin.tr("Update a bag in an existing directory."))
            self.actionCreateOrUpdate.setShortcut(MainWin.tr("Ctrl+U"))
        else:
            self.actionCreateOrUpdate.setText(MainWin.tr("Create"))
            self.actionCreateOrUpdate.setToolTip(MainWin.tr("Create a new bag from an existing directory."))
            self.actionCreateOrUpdate.setShortcut(MainWin.tr("Ctrl+N"))

    def toggleArchiveOrExtract(self, MainWin, is_bag, is_file_archive):
        self.actionArchive.setEnabled(is_bag)
        if is_bag:
            self.actionArchive.setIcon(
                self.actionArchive.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogSaveButton")))
            self.actionArchive.setText(MainWin.tr("Archive"))
            self.actionArchive.setToolTip(MainWin.tr("Create a single file compressed archive of the bag."))

        if is_file_archive:
            self.actionArchive.setEnabled(True)
            self.actionArchive.setIcon(
                self.actionArchive.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogOpenButton")))
            self.actionArchive.setText(MainWin.tr("Extract"))
            self.actionArchive.setToolTip(MainWin.tr("Extract a compressed archive file."))
