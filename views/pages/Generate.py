import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QProgressBar, QMessageBox, QDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer

from views.Styles import BUTTON_STYLE


class Generate(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.model = None
        self.json_data = None
        self.model_loaded = False
        self.data_generated = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel("Generate")
        title.setFont(QFont("Montserrat", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        self.records_input = QLineEdit("1000")
        self.records_input.setFixedWidth(300)
        form_layout.addRow("Number of Data to Generate:", self.records_input)
        layout.addLayout(form_layout)

        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE)
        self.generate_button.setFixedSize(150, 50)
        self.generate_button.clicked.connect(self.generate_data)
        self.generate_button.setEnabled(False)
        layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.save_button = QPushButton("Save Data")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(150, 50)
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setVisible(False)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

    def on_model_loaded(self, model):
        self.model = model
        self.model_loaded = True
        self.check_enable_generate_button()
        print("Modèle chargé, bouton activé.")

    def on_file_loaded(self, json_data):
        self.json_data = json_data
        self.check_enable_generate_button()

    def check_enable_generate_button(self):
        if self.model is not None and self.json_data is not None:
            self.generate_button.setEnabled(True)

    def generate_data(self):
        if not self.model_loaded or self.json_data is None:
            QMessageBox.warning(
                self,
                "Modèle requis",
                "Veuillez charger un modèle et un fichier JSON avant de générer des données."
            )
            return

        records_count = self.records_input.text()
        try:
            num_records = int(records_count)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nombre valide.")
            return

        self.progress_bar.setVisible(True)
        QTimer.singleShot(2000, lambda: self.finish_generation(num_records))
        print("Timer started for generation.")

    def finish_generation(self, num_records):
        self.data_generated = True
        self.progress_bar.setVisible(False)
        self.save_button.setVisible(True)
        self.show_message(f"{num_records} données générées avec succès.")
        print(f"Génération de {num_records} données terminée.")

    def save_data(self):
        self.main_app.changePage(8)

    def show_message(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()

