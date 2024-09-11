import sys
import os
from PyQt5 import QtWidgets, uic
from menu_buttons import MenuButtonsMixin  # Import the mixin

# Get the absolute path of the .ui file
script_path = os.path.abspath(__file__)
file_dir = os.path.split(script_path)[0]
ui_file = os.path.join(file_dir, 'UI/detection_log_window.ui')  # Update the UI file name

class DetectionLogWindow(QtWidgets.QMainWindow, MenuButtonsMixin):
    def __init__(self):
        super(DetectionLogWindow, self).__init__()
        # Load the .ui file
        uic.loadUi(ui_file, self)

        # Set up menu buttons using the mixin method
        self.setup_menu_buttons()

def main():
    # Initialize the Qt application
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = DetectionLogWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
