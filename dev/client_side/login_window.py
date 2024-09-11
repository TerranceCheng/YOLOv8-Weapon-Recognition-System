import sys
import os
from PyQt5 import QtWidgets, uic

# Get the absolute path of the .ui file
script_path = os.path.abspath(__file__)
file_dir = os.path.split(script_path)[0]
ui_file = os.path.join(file_dir, 'UI/login_window.ui')

class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(LoginWindow, self).__init__()
        # Load the .ui file
        uic.loadUi(ui_file, self)

def main():
    # Initialize the Qt application
    app = QtWidgets.QApplication(sys.argv)

    # Create and show the main window
    window = LoginWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
