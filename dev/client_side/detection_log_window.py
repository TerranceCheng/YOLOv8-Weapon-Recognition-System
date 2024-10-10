import sys
import os
import io
from PyQt5 import QtWidgets, uic
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter, QBrush, QColor, QImage, QPixmap
from PyQt5.QtCore import QTimer, QDate, Qt, QMargins
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QDialogButtonBox, QDialog, QWidget, QDateEdit, QHeaderView, QHBoxLayout, QPushButton
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery, QSqlQueryModel
from menu_buttons import MenuButtonsMixin  # Import the mixin

# Get the absolute path of the .ui file
script_path = os.path.abspath(__file__)
file_dir = os.path.split(script_path)[0]

class ReadOnlySqlTableModel(QSqlQueryModel):
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        
        if role == Qt.DisplayRole:
            # Check for Reviewed column (index 7)
            if index.column() == 8:  # Reviewed column
                value = super().data(index, role)
                return "Yes" if value == 1 else "No"  # Convert 1 to "Yes" and 0 to "No"

            # Handle display format for Detection Confidence column (index 5)
            if index.column() == 5:
                value = super().data(index, role)
                try:
                    return "{:.2f}".format(float(value))
                except (TypeError, ValueError):
                    return value

        return super().data(index, role)

    def flags(self, index):
        flags = super().flags(index)
        return flags & ~Qt.ItemIsEditable

class DetectionLogWindow(QtWidgets.QWidget):
    def __init__(self, detectionLogTable):
        super(DetectionLogWindow, self).__init__()
        self.detectionLogTable = detectionLogTable
        
        # Create a connection to the SQLite database
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(r'C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3')

        if not self.db.open():
            print("Unable to open database")
            return
        
        # Create a model
        self.model = QSqlQueryModel(self)  # Change to QSqlQueryModel for custom queries

        # Prepare a query to select records from the detection_log table
        query = QSqlQuery("SELECT id, location, detection_date, detection_time, detected_weapon, detection_confidence, image_name, image_data, checked, action FROM detection_log")

        # Execute the query and set it in the model
        if query.exec_():
            self.model = ReadOnlySqlTableModel(self)  # Use your custom model
            self.model.setQuery(query)  # Set the executed query in your model

            # Set headers
            self.model.setHeaderData(0, Qt.Horizontal, "No.")
            self.model.setHeaderData(1, Qt.Horizontal, "Location")
            self.model.setHeaderData(2, Qt.Horizontal, "Detection Date")
            self.model.setHeaderData(3, Qt.Horizontal, "Detection Time")
            self.model.setHeaderData(4, Qt.Horizontal, "Detected Weapon")
            self.model.setHeaderData(5, Qt.Horizontal, "Detection Confidence (%)")
            self.model.setHeaderData(6, Qt.Horizontal, "Image Name")
            self.model.setHeaderData(8, Qt.Horizontal, "Reviewed")  # Column for reviewed status
            self.model.setHeaderData(9, Qt.Horizontal, "Actions")  # Column for buttons

            self.detectionLogTable.setModel(self.model)

            # Hide the primary key and image data columns
            self.detectionLogTable.hideColumn(0)  # Hide the id column
            self.detectionLogTable.hideColumn(6)  # Hide the image_name
            self.detectionLogTable.hideColumn(7)  # Hide the image_data

            # Resize columns
            header = self.detectionLogTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)

            # Set styles
            self.detectionLogTable.setStyleSheet("""
                QTableView {
                    background-color: #3a364f;
                    color: white;
                    gridline-color: white;
                }
                QHeaderView::section {
                    background-color: #3a364f;
                    color: white;
                }
                QTableView::item:selected {
                    background-color: #4c4a6f;
                    color: white;
                }
                QTableCornerButton::section {
                    background-color: #3a364f;  /* Top left corner button */
                }
            """)

            # Add 'View Image' buttons
            self.add_view_image_buttons()

    def add_view_image_buttons(self):
        for row in range(self.model.rowCount()):
            button = QPushButton("View Image")
            button.clicked.connect(lambda checked, row=row: self.view_image(row))  # Use default parameter to capture the current row

            # Create a widget for the button and set it in the table
            layout = QHBoxLayout()
            layout.addWidget(button)
            widget = QWidget()
            widget.setLayout(layout)

            # Set the button widget in the corresponding index
            self.detectionLogTable.setIndexWidget(self.model.index(row, 9), widget)

    def view_image(self, row):
        # Fetch the image data from the database for the specific row
        query = QSqlQuery(f"SELECT image_data FROM detection_log WHERE id = {self.model.data(self.model.index(row, 0))}")  # Assuming column 0 has the id

        if query.exec_() and query.next():
            image_data = query.value(0)  # Get the image data BLOB

            if image_data is None:
                QtWidgets.QMessageBox.warning(self, "Image Not Found", "No image data found.")
                return

            # Convert the BLOB data to a QImage
            image = QImage.fromData(image_data)

            if image.isNull():
                QtWidgets.QMessageBox.warning(self, "Error", "Unable to load image from database.")
                return

            # Create a dialog to display the image
            dialog = QDialog(self)
            dialog.setWindowTitle("View Image")

            # Create a label to display the image
            label = QLabel(dialog)
            label.setPixmap(QPixmap.fromImage(image))  # Corrected from QPixmap(image) to QPixmap.fromImage(image)
            label.setScaledContents(True)  # Scale the image to fit the label size if necessary

            # Create a layout and add the label to the dialog
            layout = QVBoxLayout(dialog)
            layout.addWidget(label)

            dialog.setLayout(layout)
            dialog.resize(400, 400)  # Set the size of the dialog (you can adjust this)
            dialog.exec_()  # Show the dialog modally
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Unable to retrieve image data.")

def main():
    # Initialize the Qt application
    app = QtWidgets.QApplication(sys.argv)

    # Set up the database connection
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3")
    if not db.open():
        print("Error: Unable to connect to the database.")
        sys.exit(1)

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
