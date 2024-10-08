import sys
import os
import cv2
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QComboBox, QLineEdit, QLabel, QVBoxLayout, QDialogButtonBox, QDialog
from PyQt5.QtMultimedia import QSound  # For playing audio
from ultralytics import YOLO
import sqlite3
from datetime import datetime

# Path to the YOLOv8 model
# MODEL_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\weaponRecognition_showcaseBestModel.pt"
MODEL_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\runs\detect\train2\weights\best.pt"
DATABASE_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3"
AUDIO_ALERT_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\client_side\resources\alert.wav"  # Path to alert sound file

class CamerasWindow(QtWidgets.QWidget):
    def __init__(self, cam1Label, cam2Label=None, addCameraButton=None, cam1Location=None, cam2Location=None, cam3Location=None, cam4Location=None):
        super(CamerasWindow, self).__init__()

        # Store references to the existing location textboxes from the main menu page
        self.cam1Location = cam1Location
        self.cam2Location = cam2Location
        self.cam3Location = cam3Location
        self.cam4Location = cam4Location

        # Other initialization for camera labels
        self.cam1Label = cam1Label
        self.cam2Label = cam2Label

        # Load YOLO model
        self.model = YOLO(MODEL_PATH)

        # Initialize cameras
        self.cap1 = cv2.VideoCapture(0)
        self.cap2 = None

        # Initialize SQLite database connection
        self.conn = sqlite3.connect(DATABASE_PATH)

        # Dictionary to track last detection times for deduplication
        self.last_detection_times = {}

        # Connect addCameraButton if present
        if addCameraButton:
            addCameraButton.clicked.connect(self.add_camera)

        # Timer for updating frames
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms update interval

        # Sound setup
        self.sound = QSound(AUDIO_ALERT_PATH)
        self.sound_playing = False
        self.sound_duration = 3000  # 3 seconds

    def update_frame(self):
        """Update video frames from cameras."""
        ret1, frame1 = self.cap1.read()
        if ret1:
            self.process_and_display(frame1, self.cam1Label)

        if self.cap2:
            ret2, frame2 = self.cap2.read()
            if ret2:
                self.process_and_display(frame2, self.cam2Label)

    def process_and_display(self, frame, label):
        """Process each frame, perform detection, and update the label display."""
        results = self.model(frame)
        location = ""

        # Determine corresponding location textbox
        if label == self.cam1Label:
            location = self.cam1Location.text()  # cam1 location
        elif label == self.cam2Label:
            location = self.cam2Location.text()  # cam2 location
        elif label == self.cam3Label:
            location = self.cam3Location.text()  # cam3 location
        elif label == self.cam4Label:
            location = self.cam4Location.text()  # cam4 location

        # Process detection results
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()[:4]
                conf = box.conf.item()
                cls = box.cls.item()

                if conf > 0.65:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    label_text = f"{self.model.names[int(cls)]}: {conf:.2f}"
                    cv2.putText(frame, label_text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                if conf > 0.85:
                    # Trigger highlight, play alert, and save detection
                    self.highlight_label(label)
                    if not self.sound_playing:
                        self.sound_playing = True
                        self.sound.play()
                        QtCore.QTimer.singleShot(self.sound_duration, self.reset_sound_flag)

                    # Save detection to database (with deduplication)
                    self.save_detection_to_db(frame, self.model.names[int(cls)], conf*100, location)

        # Convert frame to display format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_frame = QtGui.QImage(rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)

        # Scale frame for QLabel
        label_size = label.size()
        qt_frame = qt_frame.scaled(label_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label.setPixmap(QtGui.QPixmap.fromImage(qt_frame))

    def highlight_label(self, label):
        """Highlight the label's border for 3 seconds."""
        # Check if there's already a pending style reset
        if hasattr(self, 'highlight_timer') and self.highlight_timer.isActive():
            return  # Exit if a highlight is already active

        original_style = label.styleSheet()
        label.setStyleSheet("border: 3px solid yellow;")  # Change only the border

        # Set up a QTimer to revert the border color after 3 seconds
        self.highlight_timer = QtCore.QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(lambda: label.setStyleSheet(original_style))
        self.highlight_timer.start(3000)  # Revert after 3 seconds

    def reset_sound_flag(self):
        """Reset the sound playing flag once the sound finishes playing."""
        self.sound_playing = False

    def save_detection_to_db(self, frame, weapon_name, confidence, location):
            """Save detection details and the frame to the SQLite database, with deduplication."""
            now = datetime.now()
            detection_date = now.strftime("%Y-%m-%d")
            detection_time = now.strftime("%H:%M:%S")
            detection_confidence = confidence
            image_name = f"{location}_{detection_date}_{detection_time}"

            # Deduplication logic: skip insert if detection occurred within 1 second for the same weapon and location
            detection_key = (weapon_name, location)  # Use a tuple of weapon name and location as the key
            last_time = self.last_detection_times.get(detection_key)

            if last_time and (now - last_time).total_seconds() < 2:
                return  # Skip insertion if within 2 second

            # Convert frame to bytes for storing in the database
            _, buffer = cv2.imencode('.jpg', frame)
            image_data = buffer.tobytes()

            # Prepare the SQL query
            query = """
            INSERT INTO detection_log (detected_weapon, location, detection_date, detection_time, detection_confidence, image_name, image_data, checked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """
            checked = 0
            cursor = self.conn.cursor()
            cursor.execute(query, (weapon_name, location, detection_date, detection_time, detection_confidence, image_name, image_data, checked))
            self.conn.commit()

            # Update the last detection time
            self.last_detection_times[detection_key] = now

    def add_camera(self):
            # Scan for available cameras
            available_cameras = []
            for index in range(5):
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    if index != 0:  # Exclude cam1 (webcam at index 0)
                        available_cameras.append(f"Camera {index}")
                    cap.release()

            # Show a dialog to select a camera and enter the camera location
            if available_cameras:
                dialog = QDialog(self)
                dialog.setWindowTitle("Select Camera and Location")

                # Create layout for the dialog
                layout = QVBoxLayout(dialog)

                # Create and add a combo box with the available cameras
                combo_box = QComboBox(dialog)
                combo_box.addItems(available_cameras)
                layout.addWidget(combo_box)

                # Create and add a line edit for the camera location
                location_input = QLineEdit(dialog)
                location_input.setPlaceholderText("Enter camera location")
                layout.addWidget(location_input)

                # Create and add dialog buttons (OK and Cancel)
                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
                layout.addWidget(button_box)

                # Connect the dialog buttons to accept or reject the dialog
                button_box.accepted.connect(dialog.accept)
                button_box.rejected.connect(dialog.reject)

                # Execute the dialog
                if dialog.exec_() == QDialog.Accepted:
                    selected_camera = combo_box.currentText()
                    camera_index = int(selected_camera.split()[1])  # Extract the camera index
                    camera_location = location_input.text()

                    # Update the appropriate camera location textbox
                    if camera_index == 1:
                        self.cam2Location.setText(camera_location)
                    elif camera_index == 2:
                        self.cam3Location.setText(camera_location)
                    elif camera_index == 3:
                        self.cam4Location.setText(camera_location)

                    # Open the selected external camera and display its feed
                    self.cap2 = cv2.VideoCapture(camera_index)
                    if not self.cap2.isOpened():
                        QMessageBox.warning(self, "Error", f"Failed to open {selected_camera}.")
                        
    def closeEvent(self, event):
        """Release camera resources and close the database connection when the window is closed."""
        if self.cap1 is not None:
            self.cap1.release()
        if self.cap2 is not None:
            self.cap2.release()
        self.conn.close()
        event.accept()

# Main application setup
if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    # Setup the main window and cameras window
    main_window = QtWidgets.QMainWindow()
    cameras_window = CamerasWindow(cam1Label=QtWidgets.QLabel(main_window), addCameraButton=QtWidgets.QPushButton("Add Camera", main_window))

    # Layout and showing the main window
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(cameras_window.cam1Label)
    layout.addWidget(cameras_window.cam1Location)
    layout.addWidget(cameras_window.cam2Label)
    layout.addWidget(cameras_window.cam2Location)

    central_widget = QtWidgets.QWidget()
    central_widget.setLayout(layout)
    main_window.setCentralWidget(central_widget)
    main_window.show()

    app.exec_()

