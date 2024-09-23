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
MODEL_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\weaponRecognition_showcaseBestModel.pt"
DATABASE_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3"
LOCATION = "sample_location"
AUDIO_ALERT_PATH = r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\client_side\resources\alert.wav"  # Path to alert sound file

class CamerasWindow(QtWidgets.QWidget):
    def __init__(self, cam1Label, cam2Label=None, addCameraButton=None, cam2Location=None):
        super(CamerasWindow, self).__init__()
        self.cam2Location = cam2Location  # Set the cam2Location
        self.cam1Label = cam1Label  # Set the cam1Label
        self.cam2Label = cam2Label  # Set the cam2Label for external camera (if any)

        # Set QLabel size policies to prevent resizing
        self.cam1Label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        if self.cam2Label:
            self.cam2Label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        # Load YOLO model
        self.model = YOLO(MODEL_PATH)

        # Initialize the camera for cam1Label
        self.cap1 = cv2.VideoCapture(0)  # Default to webcam for cam1Label
        self.cap2 = None  # Will be used for cam2Label (external camera)

        # Initialize database connection
        self.conn = sqlite3.connect(DATABASE_PATH)

        # If addCameraButton is provided, connect it to the add_camera method
        if addCameraButton:
            addCameraButton.clicked.connect(self.add_camera)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

        # Initialize the sound for weapon detection and set flag for sound playing
        self.sound = QSound(AUDIO_ALERT_PATH)
        self.sound_playing = False
        self.sound_duration = 3000  # Set the sound duration in milliseconds (3 seconds for example)

    def update_frame(self):
        # Update frame for cam1Label (webcam)
        ret1, frame1 = self.cap1.read()
        if ret1:
            self.process_and_display(frame1, self.cam1Label)

        # Update frame for cam2Label (external camera)
        if self.cap2:
            ret2, frame2 = self.cap2.read()
            if ret2:
                self.process_and_display(frame2, self.cam2Label)

    def process_and_display(self, frame, label):
        results = self.model(frame)
        # Draw detection results on frame and check for confidence > 0.9
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()[:4]
                conf = box.conf.item()
                cls = box.cls.item()

                # Confidence more than 70%, display boxes
                if conf > 0.7:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    label_text = f"{self.model.names[int(cls)]}: {conf:.2f}"
                    cv2.putText(frame, label_text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                # Confidence more than 90%, save to db, and trigger alert
                if conf > 0.9:
                    # Highlight the label and play the audio if it's not already playing
                    self.highlight_label(label)
                    if not self.sound_playing:
                        self.sound_playing = True
                        self.sound.play()

                        # Reset sound flag after the duration of the sound
                        QtCore.QTimer.singleShot(self.sound_duration, self.reset_sound_flag)

                    # Save the frame and details to the database
                    self.save_detection_to_db(frame, self.model.names[int(cls)], conf)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_frame = QtGui.QImage(rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)

        # Scale the frame to fit within the QLabel size without changing QLabel size
        label_size = label.size()  # Get the current size of the QLabel
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

    def save_detection_to_db(self, frame, weapon_name, confidence):
        """Save detection details and the frame to the SQLite database."""
        now = datetime.now()
        detection_date = now.strftime("%Y-%m-%d")
        detection_time = now.strftime("%H:%M:%S")
        image_name = f"{LOCATION}_{detection_date}_{detection_time}"

        # Convert frame to bytes for storing in the database
        _, buffer = cv2.imencode('.jpg', frame)
        image_data = buffer.tobytes()

        # Prepare the SQL query
        query = """
        INSERT INTO detection_log (detected_weapon, location, detection_date, detection_time, image_name, image_data, checked)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        checked = 0
        cursor = self.conn.cursor() 
        cursor.execute(query, (weapon_name, LOCATION, detection_date, detection_time, image_name, image_data, checked))
        self.conn.commit()
            
    #TODO: Currently add second camera when web cam is using wont show error message.
    #TODO: Should remove cam 0 from the list
    #TODO: If remove camera while working, should display error instead of freezing?

    def add_camera(self):
        # Scan for available cameras (assume max 5 cameras, excluding the one in use)
        available_cameras = []
        for index in range(5):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Check if this camera is already in use (by cam1Label)
                if not (self.cap1 and self.cap1.isOpened() and self.cap1 == cap):
                    available_cameras.append(f"Camera {index}")
                cap.release()

        # Show a dialog to select a camera and enter the camera location
        if available_cameras:
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Camera and Location")

            # Create layout for the dialog
            layout = QVBoxLayout(dialog)

            # Create and add a combo box with the available cameras
            label = QLabel("Choose a camera to add and provide its location:")
            combo_box = QComboBox(dialog)
            combo_box.addItems(available_cameras)

            # Create and add a line edit for the camera location
            location_input = QLineEdit(dialog)
            location_input.setPlaceholderText("Enter camera location")

            # Add the combo box and location input to the layout
            layout.addWidget(label)
            layout.addWidget(combo_box)
            layout.addWidget(location_input)

            # Create OK and Cancel buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addWidget(button_box)

            # Set the font color to black for all widgets
            dialog.setStyleSheet("""
                QLabel { color: black; }
                QComboBox { color: black; }
                QLineEdit { color: black; }
                QDialogButtonBox { color: black; }
            """)

            # Connect the OK and Cancel buttons to the dialog result
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)

            result = dialog.exec_()
            if result == QDialog.Accepted:
                # Get the selected camera index from the combo box
                selected_camera_index = int(combo_box.currentText().split()[-1])
                self.cap2 = cv2.VideoCapture(selected_camera_index)
                if not self.cap2.isOpened():
                    QMessageBox.warning(self, "Error", f"Failed to open Camera {selected_camera_index}.")
                else:
                    # Get the entered location and update the cam2Location label
                    camera_location = location_input.text()
                    self.cam2Location.setText(camera_location)
        else:
            # Show a message if no external cameras are available
            msg = QMessageBox(self)
            msg.setWindowTitle("No Cameras")
            msg.setText("No external cameras detected.")
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; }")
            msg.exec_()

    def closeEvent(self, event):
        """Handle the close event and release resources."""
        self.cap1.release()
        if self.cap2:
            self.cap2.release()
        self.conn.close()
        event.accept()
