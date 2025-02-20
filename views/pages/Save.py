from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
import json
from views.Styles import BUTTON_STYLE

# Define the button style


class Save(QWidget):
    def __init__(self):
        super().__init__()
        self.model = None  # To store the trained model
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Add space at the top
        layout.addStretch(1)

        label = QLabel("Save")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Button to save data
        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet(BUTTON_STYLE)  # Apply the style
        self.save_button.setFixedWidth(200)  # Set a fixed width
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add space at the bottom
        layout.addStretch(2)

        self.setLayout(layout)

        # Disable the save button by default
        self.save_button.setEnabled(False)

    def on_model_loaded(self, model):
        """Method called when the model is loaded."""
        self.model = model
        self.check_enable_save_button()

    def on_file_loaded(self):
        """Method called when the file is loaded."""
        self.check_enable_save_button()

    def check_enable_save_button(self):
        """Check if the save button should be enabled."""
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            self.save_button.setEnabled(True)

    def save_data(self):
        """Saves the generated data to a JSON file."""
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(open_page.json_data, f)
                self.show_message(f"Données sauvegardées avec succès dans {file_path}")
        else:
            self.show_message("Veuillez d'abord charger le fichier JSON et le modèle.")

    def show_message(self, message):
        """Displays a message in a dialog box."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()