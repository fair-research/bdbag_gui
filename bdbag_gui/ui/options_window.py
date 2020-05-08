import os
import logging
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, \
    QGroupBox, QCheckBox, QRadioButton, QMessageBox, QDialogButtonBox, qApp
from .json_editor import JSONEditor
from bdbag.bdbag_config import write_config, DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_FILE, DEFAULT_KEYCHAIN_FILE

DEFAULT_OPTIONS_FILE = os.path.join(DEFAULT_CONFIG_PATH, 'bdbag_gui.json')
DEFAULT_OPTIONS = {
    "archive_format": "zip",
    "archive_extract_dir": "",
    "bag_config_file_path": DEFAULT_CONFIG_FILE,
    "bag_keychain_file_path": DEFAULT_KEYCHAIN_FILE
}


def warningMessageBox(parent, text, detail):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Attention Required")
    msg.setText(text)
    msg.setInformativeText(detail)
    msg.exec_()


class OptionsDialog(QDialog):
    def __init__(self, parent):
        super(OptionsDialog, self).__init__(parent)
        self.config_file = parent.options.get("bag_config_file_path") or DEFAULT_OPTIONS["bag_config_file_path"]
        self.keychain_file = parent.options.get("bag_keychain_file_path") or DEFAULT_OPTIONS["bag_keychain_file_path"]
        self.archive_extract_dir = parent.options.get("archive_extract_dir") or ""
        self.archive_format = parent.options.get("archive_format") or DEFAULT_OPTIONS["archive_format"]
        self.setWindowTitle("Options")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.addStretch(1)

        # Configuration Group
        self.configGroupLayout = QVBoxLayout()
        self.configGroupBox = QGroupBox("Bag configuration:", self)
        self.configGroupBox.setLayout(self.configGroupLayout)
        layout.addWidget(self.configGroupBox)

        # BDBag config file
        self.configFileLayout = QHBoxLayout()
        self.configFilePathLabel = QLabel("Configuration File:")
        self.configFileLayout.addWidget(self.configFilePathLabel)
        self.configFilePathTextBox = QLineEdit()
        self.configFilePathTextBox.setReadOnly(True)
        self.configFilePathTextBox.setText(os.path.normpath(self.config_file))
        self.configFileLayout.addWidget(self.configFilePathTextBox)
        self.configFileBrowseButton = QPushButton("Change", parent)
        self.configFileBrowseButton.clicked.connect(self.onConfigChange)
        self.configFileLayout.addWidget(self.configFileBrowseButton)
        self.configFileEditButton = QPushButton("Edit", parent)
        self.configFileEditButton.clicked.connect(self.onConfigEdit)
        self.configFileLayout.addWidget(self.configFileEditButton)
        self.configGroupLayout.addLayout(self.configFileLayout)

        # BDBag keychain file
        self.keychainFileLayout = QHBoxLayout()
        self.keychainFilePathLabel = QLabel("Keychain File:")
        self.keychainFileLayout.addWidget(self.keychainFilePathLabel)
        self.keychainFilePathTextBox = QLineEdit()
        self.keychainFilePathTextBox.setReadOnly(True)
        self.keychainFilePathTextBox.setText(os.path.normpath(self.keychain_file))
        self.keychainFileLayout.addWidget(self.keychainFilePathTextBox)
        self.keychainFileBrowseButton = QPushButton("Change", parent)
        self.keychainFileBrowseButton.clicked.connect(self.onKeychainChange)
        self.keychainFileLayout.addWidget(self.keychainFileBrowseButton)
        self.keychainFileEditButton = QPushButton("Edit", parent)
        self.keychainFileEditButton.clicked.connect(self.onKeychainEdit)
        self.keychainFileLayout.addWidget(self.keychainFileEditButton)
        self.configGroupLayout.addLayout(self.keychainFileLayout)

        # Archive/Extract Group
        self.archiveGroupLayout = QVBoxLayout()
        self.archiveGroupBox = QGroupBox("Bag archiving and extraction:", self)
        self.archiveGroupBox.setLayout(self.archiveGroupLayout)
        layout.addWidget(self.archiveGroupBox)

        # Extraction directory path
        self.extractPathLayout = QHBoxLayout()
        self.extractPathLabel = QLabel("Archive extraction directory:")
        self.extractPathLayout.addWidget(self.extractPathLabel)
        self.extractPathTextBox = QLineEdit()
        self.extractPathTextBox.setReadOnly(True)
        self.extractPathTextBox.setText(os.path.normpath(self.archive_extract_dir))
        self.extractPathLayout.addWidget(self.extractPathTextBox)
        self.extractPathBrowseButton = QPushButton("Change", parent)
        self.extractPathBrowseButton.clicked.connect(self.onExtractPathChange)
        self.extractPathLayout.addWidget(self.extractPathBrowseButton)
        self.archiveGroupLayout.addLayout(self.extractPathLayout)

        # Archive format radio group
        self.archiveFormatLayout = QHBoxLayout()
        self.archiveFormatLabel = QLabel("Archive creation format:")
        self.archiveFormatLayout.addWidget(self.archiveFormatLabel)
        self.archiveFormatLayout.insertSpacing(1, 20)
        self.archiveFormatZipButton = QRadioButton("&ZIP")
        self.archiveFormatZipButton.setChecked(self.archive_format.lower() == "zip")
        self.archiveFormatZipButton.toggled.connect(self.onArchiveFormatChanged)
        self.archiveFormatLayout.addWidget(self.archiveFormatZipButton)
        self.archiveFormatTGZButton = QRadioButton("T&GZ")
        self.archiveFormatTGZButton.setChecked(self.archive_format.lower() == "tgz")
        self.archiveFormatTGZButton.toggled.connect(self.onArchiveFormatChanged)
        self.archiveFormatLayout.addWidget(self.archiveFormatTGZButton)
        self.archiveFormatBZ2Button = QRadioButton("&BZ2")
        self.archiveFormatBZ2Button.setChecked(self.archive_format.lower() == "bz2")
        self.archiveFormatBZ2Button.toggled.connect(self.onArchiveFormatChanged)
        self.archiveFormatLayout.addWidget(self.archiveFormatBZ2Button)
        self.archiveFormatTARButton = QRadioButton("&TAR")
        self.archiveFormatTARButton.setChecked(self.archive_format.lower() == "tar")
        self.archiveFormatTARButton.toggled.connect(self.onArchiveFormatChanged)
        self.archiveFormatLayout.addWidget(self.archiveFormatTARButton)
        self.archiveGroupLayout.addLayout(self.archiveFormatLayout)

        # Miscellaneous Group
        self.miscGroupBox = QGroupBox("Miscellaneous:", self)
        self.miscLayout = QHBoxLayout()
        self.debugCheckBox = QCheckBox("Debug logging")
        self.debugCheckBox.setChecked(True if logging.getLogger().getEffectiveLevel() == logging.DEBUG else False)
        self.miscLayout.addWidget(self.debugCheckBox)
        self.miscGroupBox.setLayout(self.miscLayout)
        layout.addWidget(self.miscGroupBox)

        # Button Box
        self.buttonBox = QDialogButtonBox(parent)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    @pyqtSlot()
    def onConfigChange(self):
        current_path = os.path.normpath(self.configFilePathTextBox.text())
        new_path = QFileDialog.getOpenFileName(self,
                                               "Select Configuration File",
                                               current_path,
                                               "Configuration Files (*.json)")
        if new_path[0]:
            new_path = os.path.normpath(new_path[0])
            if new_path != current_path:
                self.configFilePathTextBox.setText(new_path)
                self.config_file = new_path

    @pyqtSlot()
    def onConfigEdit(self):
        configEditor = JSONEditor(self, self.configFilePathTextBox.text(), "Configuration Editor")
        configEditor.exec_()
        if configEditor.isModified():
            path = self.configFilePathTextBox.text()
            self.config_file = path
        del configEditor

    @pyqtSlot()
    def onKeychainChange(self):
        current_path = os.path.normpath(self.keychainFilePathTextBox.text())
        new_path = QFileDialog.getOpenFileName(self, "Select Keychain File", current_path, "Keychain Files (*.json)")
        if new_path[0]:
            new_path = os.path.normpath(new_path[0])
            if new_path != current_path:
                self.keychainFilePathTextBox.setText(new_path)
                self.keychain_file = new_path

    @pyqtSlot()
    def onKeychainEdit(self):
        configEditor = JSONEditor(self, self.keychainFilePathTextBox.text(), "Keychain Editor")
        configEditor.exec_()
        if configEditor.isModified():
            path = self.keychainFilePathTextBox.text()
            self.keychain_file = path
        del configEditor

    @pyqtSlot()
    def onExtractPathChange(self):
        current_path = os.path.normpath(self.configFilePathTextBox.text())
        dialog = QFileDialog()
        path = dialog.getExistingDirectory(self, "Select Directory", current_path, QFileDialog.ShowDirsOnly)
        if not path:
            return
        new_path = os.path.normpath(path)
        if new_path != current_path:
            self.extractPathTextBox.setText(new_path)
            self.archive_extract_dir = new_path

    @pyqtSlot(bool)
    def onArchiveFormatChanged(self, checked):
        if checked:
            if self.archiveFormatZipButton.isChecked():
                self.archive_format = "zip"
            elif self.archiveFormatTGZButton.isChecked():
                self.archive_format = "tgz"
            elif self.archiveFormatBZ2Button.isChecked():
                self.archive_format = "bz2"
            elif self.archiveFormatTARButton.isChecked():
                self.archive_format = "tar"

    @pyqtSlot()
    def restoreDefaults(self):
        self.config_file = DEFAULT_OPTIONS["bag_config_file_path"]
        self.configFilePathTextBox.setText(self.config_file)
        self.keychain_file = DEFAULT_OPTIONS["bag_keychain_file_path"]
        self.keychainFilePathTextBox.setText(self.keychain_file)
        self.archive_extract_dir = DEFAULT_OPTIONS["archive_extract_dir"]
        self.archive_format = DEFAULT_OPTIONS["archive_format"]

    @staticmethod
    def getOptions(parent):
        dialog = OptionsDialog(parent)
        ret = dialog.exec_()
        if QDialog.Accepted == ret:
            debug = dialog.debugCheckBox.isChecked()
            logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
            dirty = False
            if dialog.config_file != parent.options["bag_config_file_path"]:
                parent.options["bag_config_file_path"] = dialog.config_file
                dirty = True
            if dialog.keychain_file != parent.options["bag_keychain_file_path"]:
                parent.options["bag_keychain_file_path"] = dialog.keychain_file
                dirty = True
            if dialog.archive_extract_dir != parent.options["archive_extract_dir"]:
                parent.options["archive_extract_dir"] = dialog.archive_extract_dir
                dirty = True
            if dialog.archive_format != parent.options["archive_format"]:
                parent.options["archive_format"] = dialog.archive_format
                dirty = True
            if dirty:
                parent.saveOptions()
        del dialog

