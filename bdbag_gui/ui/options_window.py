import os
import logging
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, \
    QGroupBox, QCheckBox, QMessageBox, QDialogButtonBox, qApp
from .json_editor import JSONEditor
from bdbag.bdbag_config import DEFAULT_CONFIG_FILE
from bdbag.fetch.auth.keychain import DEFAULT_KEYCHAIN_FILE


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
        self.override_config_file = None
        self.override_keychain_file = None
        self.setWindowTitle("Options")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.addStretch(1)

        # Configuration Group
        self.configGroupLayout = QVBoxLayout()

        # BDBag config file
        self.configFileLayout = QHBoxLayout()
        self.configFilePathLabel = QLabel("Configuration File:")
        self.configFileLayout.addWidget(self.configFilePathLabel)
        self.configFilePathTextBox = QLineEdit()
        self.configFilePathTextBox.setReadOnly(True)
        self.configFilePathTextBox.setText(os.path.normpath(parent.bagConfigFilePath))
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
        self.keychainFilePathTextBox.setText(os.path.normpath(parent.bagKeychainFilePath))
        self.keychainFileLayout.addWidget(self.keychainFilePathTextBox)
        self.keychainFileBrowseButton = QPushButton("Change", parent)
        self.keychainFileBrowseButton.clicked.connect(self.onKeychainChange)
        self.keychainFileLayout.addWidget(self.keychainFileBrowseButton)
        self.keychainFileEditButton = QPushButton("Edit", parent)
        self.keychainFileEditButton.clicked.connect(self.onKeychainEdit)
        self.keychainFileLayout.addWidget(self.keychainFileEditButton)
        self.configGroupLayout.addLayout(self.keychainFileLayout)

        self.configGroupBox = QGroupBox("Configuration:", self)
        self.configGroupBox.setLayout(self.configGroupLayout)
        layout.addWidget(self.configGroupBox)

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
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
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
                self.override_config_file = new_path

    @pyqtSlot()
    def onConfigEdit(self):
        configEditor = JSONEditor(self, self.configFilePathTextBox.text(), "Configuration Editor")
        configEditor.exec_()
        if configEditor.isModified():
            path = self.configFilePathTextBox.text()
            self.override_config_file = path
        del configEditor

    @pyqtSlot()
    def onKeychainChange(self):
        current_path = os.path.normpath(self.keychainFilePathTextBox.text())
        new_path = QFileDialog.getOpenFileName(self,
                                               "Select Keychain File",
                                               current_path,
                                               "Keychain Files (*.json)")
        if new_path[0]:
            new_path = os.path.normpath(new_path[0])
            if new_path != current_path:
                self.keychainFilePathTextBox.setText(new_path)
                self.override_keychain_file = new_path

    @pyqtSlot()
    def onKeychainEdit(self):
        configEditor = JSONEditor(self, self.keychainFilePathTextBox.text(), "Keychain Editor")
        configEditor.exec_()
        if configEditor.isModified():
            path = self.keychainFilePathTextBox.text()
            self.override_keychain_file = path
        del configEditor

    @staticmethod
    def getOptions(parent):
        dialog = OptionsDialog(parent)
        ret = dialog.exec_()
        if QDialog.Accepted == ret:
            debug = dialog.debugCheckBox.isChecked()
            logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
            if dialog.override_config_file:
                parent.bagConfigFilePath = dialog.override_config_file
            if dialog.override_keychain_file:
                parent.bagKeychainFilePath = dialog.override_keychain_file
        del dialog

