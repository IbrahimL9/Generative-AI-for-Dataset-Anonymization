from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog,
    QMessageBox, QHBoxLayout, QScrollArea, QFrame
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
import json
from views.Styles import SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE, BUTTON_STYLE2

class Save(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.data_generated = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Aligne tout vers le haut
        layout.addSpacing(20)

        # Titre
        label = QLabel("Save")
        label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

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
        self.save_button.clicked.connect(self.save_data)
        buttons_layout.addWidget(self.save_button)

        self.display_button = QPushButton("Display Data")
        self.display_button.setStyleSheet(BUTTON_STYLE2)
        self.display_button.setFixedSize(200, 150)
        self.display_button.setIcon(QIcon("images/view.png"))
        self.display_button.setIconSize(QSize(45, 45))
        self.display_button.clicked.connect(self.display_data)
        buttons_layout.addWidget(self.display_button)

        layout.addLayout(buttons_layout)

        # Pas de stretch ajouté en bas afin de maintenir le contenu en haut
        self.setLayout(layout)

        # Activation par défaut (peut être modifiée selon votre logique)
        self.display_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def on_data_generated(self):
        """Méthode pour activer les boutons lorsque les données sont générées."""
        self.data_generated = True
        self.save_button.setEnabled(True)
        self.display_button.setEnabled(True)

    def display_data(self):
        # Vérifie si les données ont été générées
        if not self.data_generated:
            QMessageBox.warning(self, "Error", "No data available to display.")
            return

        # Crée une fenêtre de dialogue pour afficher le JSON formaté
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated Data")
        dialog.setMinimumSize(600, 400)
        dialog_layout = QVBoxLayout(dialog)

        # On utilise un QScrollArea pour permettre le défilement du contenu si nécessaire
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QFrame()
        content_layout = QVBoxLayout(content_widget)

        # Affiche le JSON dans un QLabel (vous pouvez utiliser QPlainTextEdit pour une édition en lecture seule)
        generated_data = self.main_app.pages["generate"].generated_data
        data_str = json.dumps(generated_data, indent=4, ensure_ascii=False)
        data_label = QLabel(data_str)
        data_label.setFont(QFont("Courier", 10))
        data_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(data_label)
        scroll_area.setWidget(content_widget)
        dialog_layout.addWidget(scroll_area)

        dialog.exec()

    def save_data(self):
        file_dialog = QFileDialog()
        file_name, _ = file_dialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")

        if file_name:
            generated_data = self.main_app.pages["generate"].generated_data

            if generated_data:
                with open(file_name, "w", encoding="utf-8") as file:
                    json.dump(generated_data, file, ensure_ascii=False, indent=4)
                self.show_message("Data successfully saved!", message_type="success")

    def show_message(self, message, message_type="info"):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)

        # Appliquer le style en fonction du type de message
        if message_type == "success":
            message_label.setStyleSheet(SUCCESS_MESSAGE_STYLE)
        elif message_type == "error":
            message_label.setStyleSheet(ERROR_MESSAGE_STYLE)
        elif message_type == "warning":
            message_label.setStyleSheet(WARNING_MESSAGE_STYLE)
        else:
            message_label.setStyleSheet(INFO_MESSAGE_STYLE)

        dialog_layout.addWidget(message_label)
        dialog.exec()
