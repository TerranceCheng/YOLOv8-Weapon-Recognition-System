import sys
import os
import json
import sqlite3
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QComboBox, QLineEdit, QLabel, QVBoxLayout, QDialogButtonBox, QDialog, QWidget
from menu_buttons import MenuButtonsMixin  # Import the mixin
from clickable_label import ClickableLabel  # Import the ClickableLabel class
from datetime import datetime, timedelta
import cv2

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

class MainMenuWindow(QtWidgets.QMainWindow, MenuButtonsMixin):
    def __init__(self):
        super(MainMenuWindow, self).__init__()
        # Load the .ui file
        uic.loadUi(ui_file, self)

        # Reference the stacked widget and labels
        # Main Menu Page
        self.MainBodyStackedWidget = self.findChild(QtWidgets.QStackedWidget, 'MainBodyStackedWidget')
        self.weaponTypeChart = self.findChild(QWidget, 'weaponTypeChart')  # Match the objectName
        self.NewDCountLabel = self.findChild(QtWidgets.QLabel, 'NewDCountLabel')
        self.ToBeRCountLabel = self.findChild(QtWidgets.QLabel, 'ToBeRCountLabel')
        self.onCamCountLabel = self.findChild(QtWidgets.QLabel, 'onCamCountLabel')
        self.offCamCountLabel = self.findChild(QtWidgets.QLabel, 'offCamCountLabel')

        # Cameras Page
        self.cam1Label = self.findChild(QtWidgets.QLabel, 'cam1Label')
        self.cam2Label = self.findChild(QtWidgets.QLabel, 'cam2Label')
        self.addCameraButton = self.findChild(QtWidgets.QPushButton, 'addCameraButton')
        self.cam1Location = self.findChild(QtWidgets.QLineEdit, 'cam1Location')
        self.cam2Location = self.findChild(QtWidgets.QLineEdit, 'cam2Location')
        self.cam3Location = self.findChild(QtWidgets.QLineEdit, 'cam3Location')
        self.cam4Location = self.findChild(QtWidgets.QLineEdit, 'cam4Location')

        # Create instances of each page
        self.main_menu_page = QtWidgets.QWidget()
        self.cameras_page = CamerasWindow(self.cam1Label, self.cam2Label, self.addCameraButton, self.cam1Location, self.cam2Location, self.cam3Location, self.cam4Location)
        self.detection_log_page = DetectionLogWindow()
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

        # Display the chart   
        self.create_weapon_type_pie_chart()

        # Load saved camera settings
        self.load_camera_settings()

        # Update record counts in labels
        self.update_detection_stats()  # Add this call
        
        # Set up a timer to check the camera status every 2 seconds (2000 ms)
        self.camera_status_timer = QTimer(self)
        self.camera_status_timer.timeout.connect(self.check_camera_status)
        self.camera_status_timer.start(2000)  # Check every 2 seconds

        # Update the record counts in main menu page
        self.update_record_counts()

    def update_detection_stats(self):
        """Update the total number of detections, average confidence, and most common weapon."""
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Query to get the total number of detections
        cursor.execute("SELECT COUNT(*) FROM detection_log")
        total_detections = cursor.fetchone()[0]
        self.totalDetectionLabel.setText(str(total_detections))

        # Query to calculate the average detection confidence
        cursor.execute("SELECT AVG(detection_confidence) FROM detection_log")
        average_confidence = cursor.fetchone()[0]
        self.averageConfLabel.setText(f"{average_confidence:.2f}" if average_confidence else "N/A")

        # Query to find the most common weapon detected
        cursor.execute("""
            SELECT detected_weapon, COUNT(*) as count 
            FROM detection_log 
            GROUP BY detected_weapon 
            ORDER BY count DESC 
            LIMIT 1
        """)
        common_weapon = cursor.fetchone()
        self.commonWeaponLabel.setText(common_weapon[0] if common_weapon else "N/A")

        # Close the database connection
        conn.close()

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
        
    def create_weapon_type_pie_chart(self):
        """Create a pie chart displaying the count of each weapon type detection within 1 month."""
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get the current date and calculate the date 1 month ago
        today = datetime.now()
        one_month_ago = today - timedelta(days=30)

        # Query to count each weapon type detected in the last 1 month
        cursor.execute("""
            SELECT detected_weapon, COUNT(*) 
            FROM detection_log 
            WHERE detection_date >= ? 
            GROUP BY detected_weapon
        """, (one_month_ago,))
        weapon_counts = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Create a QPieSeries for the pie chart
        series = QPieSeries()

        # Add the weapon types and their counts to the series
        for weapon, count in weapon_counts:
            series.append(weapon, count)

        # Create a QChart and add the series to it
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Weapon Types Detection (Last 1 Month)")

        # Create a QChartView to display the chart
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # Ensure the weaponTypeChart widget has a layout
        if self.weaponTypeChart.layout() is None:
            layout = QVBoxLayout(self.weaponTypeChart)
            self.weaponTypeChart.setLayout(layout)
        else:
            layout = self.weaponTypeChart.layout()
        
        # Clear any existing widgets in the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add the new chart view to the layout
        layout.addWidget(chart_view)

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

    def edit_location_dialog(self, event):
        """Open dialog to edit the content of the clicked cam location label."""
        label = self.sender()
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Location")
        layout = QVBoxLayout(dialog)

        line_edit = QLineEdit(dialog)
        line_edit.setText(label.text())  # Pre-fill with the current text
        layout.addWidget(line_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        result = dialog.exec_()

        if result == QDialog.Accepted:
            label.setText(line_edit.text())  # Update label text if OK is pressed
            self.save_camera_settings()  # Save settings after editing

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
