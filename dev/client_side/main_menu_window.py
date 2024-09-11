import sys
import os
from PyQt5 import QtWidgets, uic, QtCore
from menu_buttons import MenuButtonsMixin  # Import the mixin

# Import the page classes
from cameras_window import CamerasWindow
from detection_log_window import DetectionLogWindow
from settings_window import SettingsWindow

# Get the absolute path of the .ui file
script_path = os.path.abspath(__file__)
file_dir = os.path.split(script_path)[0]
ui_file = os.path.join(file_dir, 'UI/main_menu.ui')

class MainMenuWindow(QtWidgets.QMainWindow, MenuButtonsMixin):
    def __init__(self):
        super(MainMenuWindow, self).__init__()
        # Load the .ui file
        uic.loadUi(ui_file, self)

        # Reference the stacked widget and labels
        self.MainBodyStackedWidget = self.findChild(QtWidgets.QStackedWidget, 'MainBodyStackedWidget')
        self.cam1Label = self.findChild(QtWidgets.QLabel, 'cam1Label')
        self.cam2Label = self.findChild(QtWidgets.QLabel, 'cam2Label')
        self.addCameraButton = self.findChild(QtWidgets.QPushButton, 'addCameraButton')

        # Create instances of each page
        self.main_menu_page = QtWidgets.QWidget()
        self.cameras_page = CamerasWindow(self.cam1Label, self.cam2Label, self.addCameraButton)
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

    def reset_button_colors(self):
        # Reset button colors to default
        default_style = "background-color: none; color: white;"
        self.MainMenuButton.setStyleSheet(default_style)
        self.CamerasButton.setStyleSheet(default_style)
        self.DetectionLogButton.setStyleSheet(default_style)
        self.SettingsButton.setStyleSheet(default_style)

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
