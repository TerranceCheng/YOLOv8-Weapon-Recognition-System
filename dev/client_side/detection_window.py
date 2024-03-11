from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from detection import Detection
import os

class DetectionWindow(QDialog):
    def __init__(self):
        super(DetectionWindow, self).__init__()
        script_path = os.path.abspath(__file__)
        file_dir = os.path.split(script_path)[0]
        login_window = os.path.join(file_dir, 'UI\detection_window.ui')

        loadUi(login_window, self)

        self.stopDetectionButton.clicked.connect(self.close)
        

    def create_detection_instance(self):
        self.detection = Detection()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.detectionLabel.setPixmap(QPixmap.fromImage(image))

    def start_detection(self):
        self.detection.changePixmap.connect(self.setImage)
        self.detection.start()
        self.show()

    def closeEvent(self, event):
        self.detection.running = False
        event.accept()