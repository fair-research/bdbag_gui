import sys

from PyQt5.QtCore import Qt, QRegExp, QSize, QRect
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QPainter, QColor, QTextFormat
from PyQt5.QtWidgets import QTextEdit, QApplication, QWidget, QPlainTextEdit, QMessageBox, QDialog, QVBoxLayout


class JSONSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(JSONSyntaxHighlighter, self).__init__(parent)

        self.symbol_format = QTextCharFormat()
        self.symbol_format.setForeground(Qt.blue)
        self.symbol_format.setFontWeight(QFont.Bold)

        self.name_format = QTextCharFormat()
        self.name_format.setForeground(Qt.darkMagenta)
        self.name_format.setFontWeight(QFont.Bold)
        self.name_format.setFontItalic(True)

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(Qt.darkGreen)

    def highlightBlock(self, text):
        expression = QRegExp("(\\{|\\}|\\[|\\]|\\:|\\,)")
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, self.symbol_format)
            index = expression.indexIn(text, index + length)

        text.replace("\\\"", "  ")

        expression = QRegExp("\".*\" *\\:")
        expression.setMinimal(True)
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length - 1, self.name_format)
            index = expression.indexIn(text, index + length)

        expression = QRegExp("\\: *\".*\"")
        expression.setMinimal(True)
        index = expression.indexIn(text)
        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, self.value_format)
            index = expression.indexIn(text, index + length)


class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.modified = False
        self.lineNumberArea = LineNumberArea(self)

        self.modificationChanged.connect(self.setModified)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)

    def setModified(self, modified):
        self.modified = modified

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):

        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)


class JSONEditor(QDialog):
    def __init__(self, parent, file_path, title="JSON Editor"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.file_path = file_path
        self.editor = CodeEditor()
        self.highlighter = JSONSyntaxHighlighter(self.editor.document())
        self.initUI()
        self.openFile()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)

        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setSizeGripEnabled(True)
        self.show()

    def saveFile(self):
        with open(self.file_path, 'w') as f:
            file_data = self.editor.toPlainText()
            f.write(file_data)

    def openFile(self):
        with open(self.file_path, 'r') as f:
            file_data = f.read()
            self.editor.setPlainText(file_data)

    def closeEvent(self, event=None):
        if not self.editor.modified:
            return
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowIcon(self.parent().windowIcon())
        msg.setWindowTitle("Save Changes?")
        msg.setText("Do you want to save changes to this file?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()
        if ret == QMessageBox.Yes:
            self.saveFile()
        if event:
            event.accept()

    def isModified(self):
        return self.editor.modified


def main():
    app = QApplication(sys.argv)
    editor = JSONEditor(sys.argv[1])
    editor.exec_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
