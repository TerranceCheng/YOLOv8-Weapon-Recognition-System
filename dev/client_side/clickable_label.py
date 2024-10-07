from PyQt5.QtWidgets import QLabel, QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)

    def mouseDoubleClickEvent(self, event):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Location")
        layout = QVBoxLayout(dialog)

        line_edit = QLineEdit(dialog)
        line_edit.setText(self.text())  # Pre-fill with the current text
        layout.addWidget(line_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.setText(line_edit.text())  # Update label text if OK is pressed