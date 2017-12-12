import os
import logging

from PyQt5.QtCore import Qt, QMetaObject, QModelIndex, QThreadPool, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAction, QMenu, QMenuBar, QMessageBox, QStyle, \
    QProgressBar, QToolBar, QStatusBar, QVBoxLayout, QTreeView, QFileSystemModel, qApp
from PyQt5.QtGui import QIcon
from bdbag import VERSION as BDBAG_VERSION, BAGIT_VERSION, bdbag_api as bdb
from bdbag_gui import resources, VERSION
from bdbag_gui.ui import log_widget
from bdbag_gui.impl import async_task
from bdbag_gui.impl import bag_tasks


# noinspection PyBroadException,PyArgumentList
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.isBag = False
        self.currentPath = None
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)
        self.ui.logTextBrowser.widget.log_update_signal.connect(self.updateLog)
        self.ui.logTextBrowser.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.ui.logTextBrowser)
        logging.getLogger().setLevel(logging.INFO)

        self.fileSystemModel = QFileSystemModel()
        self.fileSystemModel.setReadOnly(False)
        root = self.fileSystemModel.setRootPath(self.fileSystemModel.myComputer())
        self.ui.treeView.setModel(self.fileSystemModel)
        self.ui.treeView.setRootIndex(root)
        self.ui.treeView.setAnimated(True)
        self.ui.treeView.setAcceptDrops(True)
        self.ui.treeView.setColumnWidth(0, 300)

        self.enableControls()

    def checkIfBag(self):
        if not self.currentPath:
            self.isBag = False
        else:
            if os.path.isdir(self.currentPath):
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.isBag = bdb.is_bag(self.currentPath)
                QApplication.restoreOverrideCursor()
                if self.isBag:
                    self.updateStatus("The directory [%s] is a bag." % self.currentPath)
                else:
                    self.updateStatus("The directory [%s] is NOT a bag." % self.currentPath)
            else:
                self.isBag = False

    def disableControls(self):
        self.ui.actionCancel.setEnabled(True)
        self.ui.treeView.setEnabled(False)
        self.ui.actionCreateOrUpdate.setEnabled(False)
        self.ui.actionRevert.setEnabled(False)
        self.ui.actionFetchMissing.setEnabled(False)
        self.ui.actionFetchAll.setEnabled(False)
        self.ui.actionValidateFast.setEnabled(False)
        self.ui.actionValidateFull.setEnabled(False)
        self.ui.actionArchiveZIP.setEnabled(False)
        self.ui.actionArchiveTGZ.setEnabled(False)

    def enableControls(self):
        self.ui.treeView.setEnabled(True)
        self.ui.toggleCreateOrUpdate(self)
        self.ui.actionCreateOrUpdate.setEnabled(os.path.isdir(self.currentPath) if self.currentPath else False)
        self.ui.actionRevert.setEnabled(self.isBag)
        self.ui.actionFetchMissing.setEnabled(self.isBag)
        self.ui.actionFetchAll.setEnabled(self.isBag)
        self.ui.actionValidateFast.setEnabled(self.isBag)
        self.ui.actionValidateFull.setEnabled(self.isBag)
        self.ui.actionArchiveZIP.setEnabled(self.isBag)
        self.ui.actionArchiveTGZ.setEnabled(self.isBag)
        self.ui.actionCancel.setEnabled(False)

    def closeEvent(self, event):
        self.cancelTasks()
        event.accept()

    def cancelTasks(self):
        self.disableControls()
        async_task.Request.shutdown()
        self.statusBar().showMessage("Waiting for background tasks to terminate...")

        while True:
            qApp.processEvents()
            if QThreadPool.globalInstance().waitForDone(10):
                break

        self.statusBar().showMessage("All background tasks terminated successfully")

    @pyqtSlot()
    def bagTaskTriggered(self):
        self.ui.progressBar.reset()
        self.ui.logTextBrowser.widget.clear()
        self.disableControls()

    @pyqtSlot(str)
    def updateStatus(self, status):
        logging.info(status)
        self.statusBar().showMessage(status)

    @pyqtSlot(str)
    def updateUI(self, status):
        self.updateStatus(status)
        self.enableControls()

    @pyqtSlot(str)
    def updateLog(self, text):
        self.ui.logTextBrowser.widget.appendPlainText(text)

    @pyqtSlot(int, int)
    def updateProgress(self, current, maximum):
        self.ui.progressBar.setRange(1, maximum)
        self.ui.progressBar.setValue(current)
        self.ui.progressBar.repaint()

    @pyqtSlot(bool, str)
    def onBagCreated(self, success, status):
        self.isBag = success
        self.updateUI(status)

    @pyqtSlot(bool)
    def on_actionCreateOrUpdate_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        createOrUpdateTask = bag_tasks.BagCreateOrUpdateTask()
        createOrUpdateTask.status_update_signal.connect(self.onBagCreated)
        createOrUpdateTask.createOrUpdate(self.currentPath, self.isBag)

    @pyqtSlot(bool)
    def on_actionRevert_triggered(self):
        if not self.currentPath:
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

        self.bagTaskTriggered()
        revertTask = bag_tasks.BagRevertTask()
        revertTask.status_update_signal.connect(self.onBagCreated)
        revertTask.revert(self.currentPath)

    @pyqtSlot(bool)
    def on_actionArchiveZIP_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        archiveTask = bag_tasks.BagArchiveTask()
        archiveTask.status_update_signal.connect(self.updateUI)
        archiveTask.archive(self.currentPath, "zip")
        self.updateStatus("Archive (ZIP) initiated for bag: [%s]" % self.currentPath)

    @pyqtSlot(bool)
    def on_actionArchiveTGZ_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        archiveTask = bag_tasks.BagArchiveTask()
        archiveTask.status_update_signal.connect(self.updateUI)
        archiveTask.archive(self.currentPath, "tgz")
        self.updateStatus("Archive (TGZ) initiated for bag: [%s]" % self.currentPath)

    @pyqtSlot(bool)
    def on_actionValidateFast_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        validateTask = bag_tasks.BagValidateTask()
        validateTask.status_update_signal.connect(self.updateUI)
        validateTask.validate(self.currentPath, True)

    @pyqtSlot(bool)
    def on_actionValidateFull_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        validateTask = bag_tasks.BagValidateTask()
        validateTask.status_update_signal.connect(self.updateUI)
        validateTask.progress_update_signal.connect(self.updateProgress)
        validateTask.validate(self.currentPath, False)
        self.updateStatus("Full validation initiated for bag: [%s] -- Please wait..." % self.currentPath)

    @pyqtSlot(bool)
    def on_actionFetchAll_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        fetchTask = bag_tasks.BagFetchTask()
        fetchTask.status_update_signal.connect(self.updateUI)
        fetchTask.progress_update_signal.connect(self.updateProgress)
        fetchTask.fetch(self.currentPath, True)
        self.updateStatus("Fetch all initiated for bag: [%s] -- Please wait..." % self.currentPath)

    @pyqtSlot(bool)
    def on_actionFetchMissing_triggered(self):
        if not self.currentPath:
            return
        self.bagTaskTriggered()
        fetchTask = bag_tasks.BagFetchTask()
        fetchTask.status_update_signal.connect(self.updateUI)
        fetchTask.progress_update_signal.connect(self.updateProgress)
        fetchTask.fetch(self.currentPath, False)
        self.updateStatus("Fetch missing initiated for bag: [%s] -- Please wait..." % self.currentPath)

    @pyqtSlot(QModelIndex)
    def on_treeView_clicked(self, index):
        self.ui.statusBar.clearMessage()
        self.ui.logTextBrowser.widget.clear()
        self.currentPath = os.path.normpath(os.path.abspath(
            self.fileSystemModel.filePath(
                self.fileSystemModel.index(
                    index.row(), 0, index.parent()))))
        self.checkIfBag()
        self.enableControls()

    @pyqtSlot(bool)
    def on_actionCancel_triggered(self):
        self.cancelTasks()
        self.ui.progressBar.reset()
        self.enableControls()

    @pyqtSlot()
    def on_actionAbout_triggered(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About BDBag GUI")
        msg.setText("Version Information")
        msg.setInformativeText("BDBag GUI: %s\nBDBag: %s\nBagit: %s\n" % (VERSION, BDBAG_VERSION, BAGIT_VERSION))
        msg.setStandardButtons(QMessageBox.Ok)
        ret = msg.exec_()


# noinspection PyArgumentList,PyAttributeOutsideInit
class MainWindowUI(object):

    def setup_ui(self, MainWin):

        # Main Window
        MainWin.setObjectName("MainWindow")
        MainWin.setWindowTitle(MainWin.tr("BDBag"))
        MainWin.resize(640, 600)
        self.centralWidget = QWidget(MainWin)
        self.centralWidget.setObjectName("centralWidget")
        MainWin.setCentralWidget(self.centralWidget)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")

    # Actions

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

        # Validate Fast
        self.actionValidateFast = QAction(MainWin)
        self.actionValidateFast.setObjectName("actionValidateFast")
        self.actionValidateFast.setText(MainWin.tr("Validate: Fast"))
        self.actionValidateFast.setToolTip(
            MainWin.tr("Perform fast validation by checking the payload file counts and sizes against the Payload-0xum "
                       "value from the bag manifest"))
        self.actionValidateFast.setShortcut(MainWin.tr("Ctrl+F"))

        # Validate Full
        self.actionValidateFull = QAction(MainWin)
        self.actionValidateFull.setObjectName("actionValidateFull")
        self.actionValidateFull.setText(MainWin.tr("Validate: Full"))
        self.actionValidateFull.setToolTip(
            MainWin.tr("Perform full validation by calculating checksums for all files and comparing them against "
                       "entries in the bag manifest(s)"))
        self.actionValidateFull.setShortcut(MainWin.tr("Ctrl+V"))

        # Fetch Missing
        self.actionFetchMissing = QAction(MainWin)
        self.actionFetchMissing.setObjectName("actionFetchMissing")
        self.actionFetchMissing.setText(MainWin.tr("Fetch: Missing"))
        self.actionFetchMissing.setToolTip(
            MainWin.tr("Fetch only those remote files that are not already present in the bag"))
        self.actionFetchMissing.setShortcut(MainWin.tr("Ctrl+M"))

        # Fetch All
        self.actionFetchAll = QAction(MainWin)
        self.actionFetchAll.setObjectName("actionFetchAll")
        self.actionFetchAll.setText(MainWin.tr("Fetch: All"))
        self.actionFetchAll.setToolTip(
            MainWin.tr("Fetch all remote files, even if they are already present in the bag"))
        self.actionFetchAll.setShortcut(MainWin.tr("Ctrl+A"))

        # Archive ZIP
        self.actionArchiveZIP = QAction(MainWin)
        self.actionArchiveZIP.setObjectName("actionArchiveZIP")
        self.actionArchiveZIP.setText(MainWin.tr("Archive: ZIP"))
        self.actionArchiveZIP.setToolTip(MainWin.tr("Create a ZIP format archive of the bag."))
        self.actionArchiveZIP.setShortcut(MainWin.tr("Ctrl+Z"))

        # Archive TGZ
        self.actionArchiveTGZ = QAction(MainWin)
        self.actionArchiveTGZ.setObjectName("actionArchiveTGZ")
        self.actionArchiveTGZ.setText(MainWin.tr("Archive: TGZ"))
        self.actionArchiveTGZ.setToolTip(MainWin.tr("Create a TAR/GZIP format archive of the bag."))
        self.actionArchiveTGZ.setShortcut(MainWin.tr("Ctrl+T"))

        # Cancel
        self.actionCancel = QAction(MainWin)
        self.actionCancel.setObjectName("actionCancel")
        self.actionCancel.setText(MainWin.tr("Cancel"))
        self.actionCancel.setToolTip(MainWin.tr("Cancel the current background task."))
        self.actionCancel.setShortcut(MainWin.tr("Ctrl+C"))

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
        self.menuBar.addAction(self.menuBag.menuAction())
        self.menuBag.addAction(self.actionCreateOrUpdate)
        self.menuBag.addAction(self.actionRevert)
        self.menuBag.addAction(self.actionCancel)

        # Fetch Menu
        self.menuFetch = QMenu(self.menuBag)
        self.menuFetch.setObjectName("menuFetch")
        self.menuFetch.setTitle(MainWin.tr("Fetch"))
        self.menuFetch.addAction(self.actionFetchMissing)
        self.menuFetch.addAction(self.actionFetchAll)
        self.menuBag.addAction(self.menuFetch.menuAction())

        # Validate Menu
        self.menuValidate = QMenu(self.menuBag)
        self.menuValidate.setObjectName("menuValidate")
        self.menuValidate.setTitle(MainWin.tr("Validate"))
        self.menuValidate.addAction(self.actionValidateFast)
        self.menuValidate.addAction(self.actionValidateFull)
        self.menuBag.addAction(self.menuValidate.menuAction())

        # Archive Menu
        self.menuArchive = QMenu(self.menuBag)
        self.menuArchive.setObjectName("menuArchive")
        self.menuArchive.setTitle(MainWin.tr("Archive"))
        self.menuArchive.addAction(self.actionArchiveZIP)
        self.menuArchive.addAction(self.actionArchiveTGZ)
        self.menuBag.addAction(self.menuArchive.menuAction())

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
        MainWin.addToolBar(Qt.TopToolBarArea, self.mainToolBar)

        # Create/Update
        self.mainToolBar.addAction(self.actionCreateOrUpdate)
        self.actionCreateOrUpdate.setIcon(
            self.actionCreateOrUpdate.parentWidget().style().standardIcon(getattr(QStyle, "SP_FileDialogNewFolder")))

        # Revert
        self.mainToolBar.addAction(self.actionRevert)
        self.actionRevert.setIcon(
            self.actionRevert.parentWidget().style().standardIcon(getattr(QStyle, "SP_DialogOkButton")))

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
        self.mainToolBar.addAction(self.actionArchiveZIP)
        self.actionArchiveZIP.setIcon(
            self.actionArchiveZIP.parentWidget().style().standardIcon(getattr(QStyle, "SP_FileDialogDetailedView")))
        self.mainToolBar.addAction(self.actionArchiveTGZ)
        self.actionArchiveTGZ.setIcon(
            self.actionArchiveTGZ.parentWidget().style().standardIcon(getattr(QStyle, "SP_FileDialogDetailedView")))

        # Cancel
        self.mainToolBar.addAction(self.actionCancel)
        self.actionCancel.setIcon(
            self.actionCancel.parentWidget().style().standardIcon(getattr(QStyle, "SP_BrowserStop")))

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
                    background-color: darkblue;
                    width: 10px;
                    margin: 0.5px;
            }
            """)
        self.verticalLayout.addWidget(self.progressBar)

        # finalize UI setup
        self.toggleCreateOrUpdate(MainWin)
        QMetaObject.connectSlotsByName(MainWin)

    def toggleCreateOrUpdate(self, MainWin):
        if MainWin.isBag:
            self.actionCreateOrUpdate.setText(MainWin.tr("Update"))
            self.actionCreateOrUpdate.setToolTip(MainWin.tr("Update a bag in an existing directory"))
            self.actionCreateOrUpdate.setShortcut(MainWin.tr("Ctrl+U"))
        else:
            self.actionCreateOrUpdate.setText(MainWin.tr("Create"))
            self.actionCreateOrUpdate.setToolTip(MainWin.tr("Create a new bag from an existing directory"))
            self.actionCreateOrUpdate.setShortcut(MainWin.tr("Ctrl+N"))
