from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
import os    
from detection_window import DetectionWindow

class LoginWindow(QDialog):
    def __init__(self):
        super(LoginWindow, self).__init__()
        script_path = os.path.abspath(__file__)
        file_dir = os.path.split(script_path)[0]
        login_window = os.path.join(file_dir, 'UI\login_window.ui')

        loadUi(login_window, self)
        self.detection_window = DetectionWindow()

        self.registerButton.clicked.connect(self.go_to_register_page)
        self.loginButton.clicked.connect(self.open_settings_window)

        self.show()

    def go_to_register_page(self):
        print('Go to Register Page')

    def open_settings_window(self):
        if self.detection_window.isVisible():
            print('Detection window is already open!')
        else:
            self.detection_window.create_detection_instance()
            self.detection_window.start_detection()
           

        