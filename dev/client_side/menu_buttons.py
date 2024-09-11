# # menu_buttons.py

# from PyQt5 import QtWidgets

# class MenuButtonsMixin:
#     def setup_menu_buttons(self):
#         """
#         Set up the connections for all menu navigation buttons.
#         Assumes that buttons and their corresponding methods are correctly named and defined.
#         """
#         self.MainMenuButton.clicked.connect(self.show_main_menu)
#         self.DetectionLogButton.clicked.connect(self.show_detection_log)
#         self.SettingsButton.clicked.connect(self.show_settings)
#         self.LogoutButton.clicked.connect(self.show_login)

#     def show_main_menu(self):
#         from main_menu_window import MainMenuWindow
#         self.main_menu_window = MainMenuWindow()
#         self.main_menu_window.show()
#         self.close()

#     def show_detection_log(self):
#         from detection_log_window import DetectionLogWindow
#         self.detection_log_window = DetectionLogWindow()
#         self.detection_log_window.show()
#         self.close()

#     def show_settings(self):
#         from setting_window import SettingWindow
#         self.setting_window = SettingWindow()
#         self.setting_window.show()
#         self.close()

#     def show_login(self):
#         from login_window import LoginWindow
#         self.login_window = LoginWindow()
#         self.login_window.show()
#         self.close()

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

class MenuButtonsMixin:
    def setup_menu_buttons(self):
        # Connect buttons to respective pages
        self.MainMenuButton.clicked.connect(lambda: self.display_page(0, self.MainMenuButton))
        self.CamerasButton.clicked.connect(lambda: self.display_page(1, self.CamerasButton))
        self.DetectionLogButton.clicked.connect(lambda: self.display_page(2, self.DetectionLogButton))
        self.SettingsButton.clicked.connect(lambda: self.display_page(3, self.SettingsButton))

    def display_page(self, page_index, button):
        # Set the current page in the QStackedWidget
        self.MainBodyStackedWidget.setCurrentIndex(page_index)
        
        # Reset all buttons to their default color
        self.reset_button_colors()

        # Change the clicked button's background color
        button.setStyleSheet("background-color: #3a364f; color: white;")

    def reset_button_colors(self):
        # Reset button colors to default
        default_style = "background-color: none; color: black;"
        self.MainMenuButton.setStyleSheet(default_style)
        self.CamerasButton.setStyleSheet(default_style)
        self.DetectionLogButton.setStyleSheet(default_style)
        self.SettingsButton.setStyleSheet(default_style)
