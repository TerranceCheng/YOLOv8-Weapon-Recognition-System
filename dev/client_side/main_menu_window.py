import sys
import os
import json
import sqlite3
from PyQt5 import QtWidgets, uic
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont
from PyQt5.QtCore import QTimer, QDate, Qt, QMargins
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QDialogButtonBox, QDialog, QWidget, QDateEdit, QHeaderView
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery, QSqlQueryModel
from menu_buttons import MenuButtonsMixin  # Import the mixin
from datetime import datetime, timedelta

# Import the page classes
from cameras_window import CamerasWindow
from detection_log_window import DetectionLogWindow
from settings_window import SettingsWindow

DATABASE_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3"

# Get the absolute path of the .ui file
script_path = os.path.abspath(__file__)
file_dir = os.path.split(script_path)[0]
ui_file = os.path.join(file_dir, 'UI/main_menu.ui')
json_file = os.path.join(file_dir, 'resources/cameras.json')

class ReadOnlySqlTableModel(QSqlTableModel):
    def data(self, index, role=Qt.DisplayRole):
        # Handle text alignment for all cells
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter  # Center-align the text in all cells

        # Handle the display format for the Detection Confidence column (column 5)
        if role == Qt.DisplayRole and index.column() == 5:
            # Retrieve the original data from the database
            value = super().data(index, role)
            try:
                # Convert value to float and format it to 2 decimal places
                value = float(value)
                return "{:.2f}".format(value)
            except (TypeError, ValueError):
                # Handle case where value cannot be converted to float
                return value

        return super().data(index, role)
    
    def flags(self, index):
        # Make all cells non-editable by removing the Qt.ItemIsEditable flag
        flags = super().flags(index)
        return flags & ~Qt.ItemIsEditable

class MainMenuWindow(QtWidgets.QMainWindow, MenuButtonsMixin):
    def __init__(self):
        super(MainMenuWindow, self).__init__()
        # Load the .ui file
        uic.loadUi(ui_file, self)

        # Reference the stacked widget and labels
        # Main Menu Page
        self.MainBodyStackedWidget = self.findChild(QtWidgets.QStackedWidget, 'MainBodyStackedWidget')
        self.weaponNumberChart = self.findChild(QWidget, 'weaponNumberChart')
        self.weaponTypeChart = self.findChild(QWidget, 'weaponTypeChart')
        self.NewDCountLabel = self.findChild(QtWidgets.QLabel, 'NewDCountLabel')
        self.ToBeRCountLabel = self.findChild(QtWidgets.QLabel, 'ToBeRCountLabel')
        self.onCamCountLabel = self.findChild(QtWidgets.QLabel, 'onCamCountLabel')
        self.offCamCountLabel = self.findChild(QtWidgets.QLabel, 'offCamCountLabel')
        self.summaryPeriodComboBox = self.findChild(QtWidgets.QComboBox, 'summaryPeriodComboBox')
        self.totalDetectionLabel = self.findChild(QtWidgets.QLabel, 'totalDetectionLabel')
        self.averageConfLabel = self.findChild(QtWidgets.QLabel, 'averageConfLabel')
        self.commonWeaponLabel = self.findChild(QtWidgets.QLabel, 'commonWeaponLabel')
        self.recentDetectionTable = self.findChild(QtWidgets.QTableView, 'recentDetectionTable')

        # Cameras Page
        self.cam1Label = self.findChild(QtWidgets.QLabel, 'cam1Label')
        self.cam2Label = self.findChild(QtWidgets.QLabel, 'cam2Label')
        self.addCameraButton = self.findChild(QtWidgets.QPushButton, 'addCameraButton')
        self.cam1Location = self.findChild(QtWidgets.QLineEdit, 'cam1Location')
        self.cam2Location = self.findChild(QtWidgets.QLineEdit, 'cam2Location')
        self.cam3Location = self.findChild(QtWidgets.QLineEdit, 'cam3Location')
        self.cam4Location = self.findChild(QtWidgets.QLineEdit, 'cam4Location')

        # Detection Log Page
        self.detectionLogTable = self.findChild(QtWidgets.QTableView, 'detectionLogTable')

        # Create instances of each page
        self.main_menu_page = QtWidgets.QWidget()
        self.cameras_page = CamerasWindow(self.cam1Label, self.cam2Label, self.addCameraButton, self.cam1Location, self.cam2Location, self.cam3Location, self.cam4Location)
        self.detection_log_page = DetectionLogWindow(self.detectionLogTable)
        self.settings_page = SettingsWindow()

        # Add pages to the stacked widget
        self.MainBodyStackedWidget.addWidget(self.main_menu_page)
        self.MainBodyStackedWidget.addWidget(self.cameras_page)
        self.MainBodyStackedWidget.addWidget(self.detection_log_page)
        self.MainBodyStackedWidget.addWidget(self.settings_page)

        # Set the default page index
        self.MainBodyStackedWidget.setCurrentIndex(0)

        # Set up menu buttons using the mixin method
        self.setup_menu_buttons()

        # Load saved camera settings
        self.load_camera_settings()

        # Display the chart and stats
        self.create_weapon_type_pie_chart()
        self.updateStatsAndGraph()

        # Set up the database and populate the table view
        self.setupDatabase()  

        # Call on period changed when summaryPeriodComboBox change text
        self.summaryPeriodComboBox.currentTextChanged.connect(self.onPeriodChanged)

        # Set up a timer to check the camera status every 2 seconds (2000 ms)
        self.camera_status_timer = QTimer(self)
        self.camera_status_timer.timeout.connect(self.check_camera_status)
        self.camera_status_timer.start(2000)  # Check every 2 seconds

        # Update the record counts in main menu page
        self.update_record_counts()

    def onPeriodChanged(self, text):
        if text == "Custom":
            self.showCustomDateRangePicker()
        else:
            # Update stats and graph based on the selected period
            self.updateStatsAndGraph()

    def showCustomDateRangePicker(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select a date range")  # Set the window title
        layout = QVBoxLayout()

        # Create DateEdit widgets with default dates set to today
        start_date = QDateEdit(calendarPopup=True)
        end_date = QDateEdit(calendarPopup=True)
        today = QDate.currentDate()  # Get today's date
        start_date.setDate(today)  # Set default start date to today
        end_date.setDate(today)    # Set default end date to today
        
        # Disable dates after today
        start_date.setMaximumDate(today)
        end_date.setMaximumDate(today)

        start_date.setDisplayFormat("yyyy-MM-dd")
        end_date.setDisplayFormat("yyyy-MM-dd")

        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(start_date)
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(end_date)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Set stylesheet for black font color for all widgets in the dialog
        dialog.setStyleSheet("QWidget { color: black; }")  # Apply black color to all text in dialog

        dialog.setLayout(layout)
        
        # Connect the date change signal to update the end date minimum
        start_date.dateChanged.connect(lambda date: end_date.setMinimumDate(date))
        
        if dialog.exec_() == QDialog.Accepted:
            start = start_date.date().toString("yyyy-MM-dd")
            end = end_date.date().toString("yyyy-MM-dd")
            self.updateStatsAndGraph(custom_range=(start, end))

    def updateStatsAndGraph(self, custom_range=None):
        selected_period = self.summaryPeriodComboBox.currentText()

        if custom_range:
            start_date, end_date = custom_range
            # Fetch and update data for custom date range
            self.updateDataFromDatabase(start_date, end_date)
            self.create_weapon_type_pie_chart(start_date, end_date)  # Call with custom range
        elif selected_period == "Day":
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.updateDataFromDatabase(today, today)
            self.create_weapon_type_pie_chart(today, today)  # Call with today's date
        elif selected_period == "Month":
            first_day_of_month = QDate.currentDate().toString("yyyy-MM-01")
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.updateDataFromDatabase(first_day_of_month, today)
            self.create_weapon_type_pie_chart(first_day_of_month, today)  # Call with month range
        elif selected_period == "Year":
            first_day_of_year = QDate.currentDate().toString("yyyy-01-01")
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.updateDataFromDatabase(first_day_of_year, today)
            self.create_weapon_type_pie_chart(first_day_of_year, today)  # Call with year range

    def updateDataFromDatabase(self, start_date, end_date):
        """Fetch detection stats and graph data between start_date and end_date from the database."""
        
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Query to get the total number of detections within the date range
        cursor.execute("""
            SELECT COUNT(*) FROM detection_log 
            WHERE detection_date BETWEEN ? AND ?
        """, (start_date, end_date))
        total_detections = cursor.fetchone()[0]
        self.totalDetectionLabel.setText(str(total_detections))

        # Query to calculate the average detection confidence within the date range
        cursor.execute("""
            SELECT AVG(detection_confidence) FROM detection_log 
            WHERE detection_date BETWEEN ? AND ?
        """, (start_date, end_date))
        average_confidence = cursor.fetchone()[0]
        self.averageConfLabel.setText(f"{average_confidence:.2f}%" if average_confidence else "N/A")

        # Query to find the most common weapon detected within the date range
        cursor.execute("""
            SELECT detected_weapon, COUNT(*) as count 
            FROM detection_log 
            WHERE detection_date BETWEEN ? AND ? 
            GROUP BY detected_weapon 
            ORDER BY count DESC 
            LIMIT 1
        """, (start_date, end_date))
        common_weapon = cursor.fetchone()
        self.commonWeaponLabel.setText(common_weapon[0] if common_weapon else "N/A")

        # Close the database connection
        conn.close() 

    def create_weapon_type_pie_chart(self, start_date=None, end_date=None):
        """Create a pie chart displaying the count of each weapon type detection based on the selected date range."""
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        if start_date and end_date:
            # Query to count each weapon type detected in the specified date range
            cursor.execute("""
                SELECT detected_weapon, COUNT(*) 
                FROM detection_log 
                WHERE detection_date BETWEEN ? AND ? 
                GROUP BY detected_weapon
            """, (start_date, end_date))
        else:
            # Get the current date and calculate the date today
            today = QDate.currentDate().toString("yyyy-MM-dd")

            # Query to count each weapon type detected in the last month
            cursor.execute("""
                SELECT detected_weapon, COUNT(*) 
                FROM detection_log 
                WHERE detection_date BETWEEN ? AND ?  
                GROUP BY detected_weapon
            """, (today, today))

        weapon_counts = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Create a QPieSeries for the pie chart
        series = QPieSeries()

        if weapon_counts:
            # Add the weapon types and their counts to the series
            for weapon, count in weapon_counts:
                slice = series.append(weapon, count)
                slice.setLabel(f"{weapon}: {count}")  # Set label with weapon name and count
                slice.setLabelBrush(QBrush(QColor("#ffffff")))
                slice.setLabelVisible(True)  # Make the label visible
        else:
            # Add a single entry for "No data found"
            slice = series.append("No detection found", 1)

        selected_period = self.summaryPeriodComboBox.currentText()

        # Create a QChart and add the series to it
        chart = QChart()
        chart.addSeries(series)
        if selected_period == 'Custom':
            chart.setTitle(f"Weapon Types Detection ({start_date} to {end_date})")
        else:
            chart.setTitle(f"Weapon Types Detection ({selected_period})")

        # Set a 9pt font for all text elements
        font = QFont()
        font.setPointSize(9)

        # Apply the font to the chart title
        chart.setTitleFont(font)
        chart.setTitleBrush(QBrush(QColor("#ffffff")))
        chart.setBackgroundBrush(QBrush(QColor("#3a364f")))

        # Set chart margins to 0 to remove extra space at the edges
        chart.setMargins(QMargins(0, 0, 0, 0))

        # Customize legend markers to have white font
        legend = chart.legend()
        legend.setVisible(True)
        legend.setFont(font)  # Set font size for the legend

        for marker in legend.markers():
            weapon = marker.slice().label().split(":")[0]  # Extract weapon name
            marker.setLabel(weapon)  # Set only the weapon name in the legend
            marker.setLabelBrush(QBrush(QColor("#ffffff")))  # Set legend text color to white

        # Apply the 9pt font size to all pie slice labels
        for slice in series.slices():
            slice.setLabelFont(font)

        # Resize the pie chart to make it bigger
        chart.setMinimumSize(300, 300)  # Set minimum size for the chart (width, height)

        # Create a QChartView to display the chart
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # Set the background color of the chart view
        chart_view.setBackgroundBrush(QBrush(QColor("#3a364f")))

        # Ensure the weaponNumberChart widget has a layout
        if self.weaponNumberChart.layout() is None:
            layout = QVBoxLayout(self.weaponNumberChart)
            self.weaponNumberChart.setLayout(layout)
        else:
            layout = self.weaponNumberChart.layout()

        # Clear any existing widgets in the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Set padding and margins to 0 for the layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add the new chart view to the layout with alignment to center
        layout.addWidget(chart_view, alignment=Qt.AlignCenter)

    def check_camera_status(self):
        """Periodically check the status of the cameras and update the labels."""
        working_camera_count, offline_camera_count = self.count_working_cameras()
        
        # Update the labels with the current camera counts
        self.onCamCountLabel.setText(str(working_camera_count))
        self.offCamCountLabel.setText(str(offline_camera_count))

        # Check camera 1 (webcam) status
        if hasattr(self.cameras_page, 'cap1') and self.cameras_page.cap1 is not None:
            if self.cameras_page.cap1.isOpened():
                ret, _ = self.cameras_page.cap1.read()
                if not ret:
                    # Camera feed is lost, release it
                    self.cameras_page.cap1.release()

        # Check camera 2 (external camera) status
        if hasattr(self.cameras_page, 'cap2') and self.cameras_page.cap2 is not None:
            if self.cameras_page.cap2.isOpened():
                ret, _ = self.cameras_page.cap2.read()
                if not ret:
                    # Camera feed is lost, release it
                    self.cameras_page.cap2.release()

        # Update the labels again in case a camera status has changed
        self.onCamCountLabel.setText(str(working_camera_count))
        self.offCamCountLabel.setText(str(offline_camera_count))
    
    def update_record_counts(self):
        """Query the database and update the QLabel widgets with the record counts."""
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get the current date and calculate the date 7 days ago
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)

        # Count of records within the last 7 days
        cursor.execute("SELECT COUNT(*) FROM detection_log WHERE detection_date >= ?", (seven_days_ago,))
        new_d_count = cursor.fetchone()[0]
        self.NewDCountLabel.setText(str(new_d_count))

        # Count of records within 7 days where 'checked' = 0
        cursor.execute("SELECT COUNT(*) FROM detection_log WHERE detection_date >= ? AND checked = 0", (seven_days_ago,))
        to_be_reviewed_count = cursor.fetchone()[0]
        self.ToBeRCountLabel.setText(str(to_be_reviewed_count))

        # Count working and offline cameras
        working_camera_count, offline_camera_count = self.count_working_cameras()
        self.onCamCountLabel.setText(str(working_camera_count))
        self.offCamCountLabel.setText(str(offline_camera_count))

        # Close the database connection
        conn.close()

        self.create_weapon_type_pie_chart()

    def count_working_cameras(self):
        """Count the number of cameras currently providing video feeds and those offline."""
        working_cameras = 0
        total_cameras = 0  # This will track total cameras initialized (online or offline)
        
        # Check if cap1 (for cam1Label) is initialized and opened
        if hasattr(self.cameras_page, 'cap1') and self.cameras_page.cap1 is not None:
            total_cameras += 1
            if self.cameras_page.cap1.isOpened():
                # Try to grab a frame to ensure the feed is active
                ret, _ = self.cameras_page.cap1.read()
                if ret:
                    working_cameras += 1

        # Check if cap2 (for cam2Label) is initialized and opened
        if hasattr(self.cameras_page, 'cap2') and self.cameras_page.cap2 is not None:
            total_cameras += 1
            if self.cameras_page.cap2.isOpened():
                # Try to grab a frame to ensure the feed is active
                ret, _ = self.cameras_page.cap2.read()
                if ret:
                    working_cameras += 1

        # You can add more checks for other cameras (cap3, cap4, etc.) similarly.

        offline_cameras = total_cameras - working_cameras
        return working_cameras, offline_cameras

    def setup_menu_buttons(self):
        # Connect buttons to respective pages
        self.MainMenuButton.clicked.connect(lambda: self.display_page(0, self.MainMenuButton))
        self.CamerasButton.clicked.connect(lambda: self.display_page(1, self.CamerasButton))
        self.DetectionLogButton.clicked.connect(lambda: self.display_page(2, self.DetectionLogButton))
        self.SettingsButton.clicked.connect(lambda: self.display_page(3, self.SettingsButton))

    def display_page(self, page_index, button):
        # Set the current page in the QStackedWidget (MainBodyStackedWidget)
        self.MainBodyStackedWidget.setCurrentIndex(page_index)
        
        # Reset all buttons to their default color
        self.reset_button_colors()

        # Change the clicked button's background color
        button.setStyleSheet("background-color: #3a364f; color: white;")

        if page_index == 0:  # Main Menu index is 0
            self.update_record_counts()
            self.count_working_cameras()
            self.updateStatsAndGraph()

    def reset_button_colors(self):
        # Reset button colors to default
        default_style = "background-color: none; color: white;"
        self.MainMenuButton.setStyleSheet(default_style)
        self.CamerasButton.setStyleSheet(default_style)
        self.DetectionLogButton.setStyleSheet(default_style)
        self.SettingsButton.setStyleSheet(default_style)

    def load_camera_settings(self):
        """Load camera settings from the JSON file."""
        if os.path.exists(json_file):
            with open(json_file, 'r') as file:
                data = json.load(file)
                self.cam2Location.setText(data.get('cam2_location', 'Default Location'))

    def save_camera_settings(self):
        """Save camera settings to the JSON file."""
        data = {
            'cam2_location': self.cam2Location.text(),
        }
        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)

    def setupDatabase(self):
        # Create a connection to the SQLite database
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(r'C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3')

        if not self.db.open():
            print("Unable to open database")
            return

        # Create a model
        self.model = QSqlQueryModel(self)  # Change to QSqlQueryModel for custom queries

        # Prepare a query to select only 15 records from the detection_log table
        query = QSqlQuery("SELECT id, location, detection_date, detection_time, detected_weapon, detection_confidence, image_name FROM detection_log LIMIT 15")

        # Execute the query and set it in the model
        if query.exec_():
            self.model = ReadOnlySqlTableModel(self)  # Use your custom model
            self.model.setQuery(query)  # Set the executed query in your model

            # Set headers (ensure they match the database columns)
            self.model.setHeaderData(0, Qt.Horizontal, "No.")  # id
            self.model.setHeaderData(1, Qt.Horizontal, "Location")
            self.model.setHeaderData(2, Qt.Horizontal, "Detection Date")
            self.model.setHeaderData(3, Qt.Horizontal, "Detection Time")
            self.model.setHeaderData(4, Qt.Horizontal, "Detected Weapon")
            self.model.setHeaderData(5, Qt.Horizontal, "Accuracy (%)")
            self.model.setHeaderData(6, Qt.Horizontal, "Image Name")

            # Set the model to the QTableView
            self.recentDetectionTable.setModel(self.model)

            # Hide the primary key and image data columns
            self.recentDetectionTable.hideColumn(0)  # Hide the id column
            self.recentDetectionTable.hideColumn(6)  # Hide the image_name

            # Resize columns based on percentage
            header = self.recentDetectionTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)  # Stretch to fill space

        else:
            print("Query execution failed")

def main():
    # Initialize the Qt application
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = MainMenuWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
