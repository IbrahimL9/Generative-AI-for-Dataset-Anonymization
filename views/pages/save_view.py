# save_view.py
import json

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QDialog, QScrollArea, \
    QFrame, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
from views.Styles import SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, INFO_MESSAGE_STYLE, \
    BUTTON_STYLE2


class SaveView(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.initUI()


    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(20)

        # Titre
        self.title = QLabel("Save")
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)

        layout.addSpacing(150)

        # Layout horizontal pour les boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(40)

        self.save_button = QPushButton("Save Data")
        self.save_button.setStyleSheet(BUTTON_STYLE2)
        self.save_button.setFixedSize(200, 150)
        self.save_button.setIcon(QIcon("images/save.png"))
        self.save_button.setIconSize(QSize(45, 45))
        buttons_layout.addWidget(self.save_button)

        self.display_button = QPushButton("Display Data")
        self.display_button.setStyleSheet(BUTTON_STYLE2)
        self.display_button.setFixedSize(200, 150)
        self.display_button.setIcon(QIcon("images/view.png"))
        self.display_button.setIconSize(QSize(45, 45))
        buttons_layout.addWidget(self.display_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # Boutons désactivés par défaut, à activer via le contrôleur
        self.save_button.setEnabled(False)
        self.display_button.setEnabled(False)

    def on_data_generated(self):
        """Active les boutons lorsque les données sont générées."""
        self.save_button.setEnabled(True)
        self.display_button.setEnabled(True)

    def display_data(self, data_to_display):
        """
        Affiche les données générées dans une QDialog avec une zone de défilement.
        """
        try:
            data_str = json.dumps(data_to_display, indent=4, ensure_ascii=False)
        except Exception as e:
            data_str = f"Erreur lors de la conversion JSON: {e}"

        MAX_LEN = 200000
        if len(data_str) > MAX_LEN:
            data_str = data_str[:MAX_LEN] + "\n[... TRONQUÉ ...]"

        dialog = QDialog(self)
        dialog.setWindowTitle("Generated Data")
        dialog.setMinimumSize(600, 400)
        dialog_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QFrame()
        content_layout = QVBoxLayout(content_widget)

        data_label = QLabel(data_str)
        data_label.setFont(QFont("Courier", 10))
        data_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        content_layout.addWidget(data_label)
        scroll_area.setWidget(content_widget)
        dialog_layout.addWidget(scroll_area)

        dialog.exec()

    def show_message(self, message, message_type="info"):
        """
        Affiche un message dans une QDialog stylisée en fonction du type (success, error, warning, info).
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        layout = QVBoxLayout(dialog)
        message_label = QLabel(message)

        if message_type == "success":
            message_label.setStyleSheet(SUCCESS_MESSAGE_STYLE)
        elif message_type == "error":
            message_label.setStyleSheet(ERROR_MESSAGE_STYLE)
        elif message_type == "warning":
            message_label.setStyleSheet(WARNING_MESSAGE_STYLE)
        else:
            message_label.setStyleSheet(INFO_MESSAGE_STYLE)

        layout.addWidget(message_label)
        dialog.exec()

    def get_save_file_name(self):
        """Ouvre un File Dialog et retourne le nom du fichier saisi."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
        return file_name
