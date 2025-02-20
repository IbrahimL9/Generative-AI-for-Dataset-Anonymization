from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .Styles1 import BUTTON_STYLE
# Define the button style


class Generate(QWidget):
    def __init__(self):
        super().__init__()
        self.model = None  # To store the trained model
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Add space at the top
        layout.addStretch(1)

        label = QLabel("Generate")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Button to generate data
        self.generate_button = QPushButton("Generate Data")
        self.generate_button.clicked.connect(self.generate_data)
        self.generate_button.setStyleSheet(BUTTON_STYLE)  # Apply the style
        self.generate_button.setFixedWidth(200)  # Set a fixed width
        layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add space at the bottom
        layout.addStretch(2)

        self.setLayout(layout)

        # Disable the generate button by default
        self.generate_button.setEnabled(False)

    def on_model_loaded(self, model):
        """Method called when the model is loaded."""
        self.model = model
        self.check_enable_generate_button()

    def on_file_loaded(self):
        """Method called when the file is loaded."""
        self.check_enable_generate_button()

    def check_enable_generate_button(self):
        """Check if the generate button should be enabled."""
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            self.generate_button.setEnabled(True)

    def generate_data(self):
        """Generates new data based on the trained model."""
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            self.show_message("Data generation logic goes here.")
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
