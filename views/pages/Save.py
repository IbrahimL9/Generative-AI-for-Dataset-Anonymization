# views/pages/Save.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import json
from views.Styles import BUTTON_STYLE

class Save(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app  # Référence à l'application principale
        self.model = None  # Pour stocker le modèle entraîné
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Espace en haut
        layout.addStretch(5)

        label = QLabel("Save")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Bouton pour sauvegarder les données
        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedWidth(200)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Espace en bas
        layout.addStretch(2)

        self.setLayout(layout)
        self.save_button.setEnabled(False)

    def on_model_loaded(self, model):
        """Méthode appelée lors du chargement du modèle."""
        self.model = model
        self.check_enable_save_button()

    def on_file_loaded(self):
        """Méthode appelée lors du chargement du fichier JSON."""
        self.check_enable_save_button()

    def check_enable_save_button(self):
        """Active le bouton si le modèle et le fichier JSON sont chargés."""
        open_page = self.main_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            self.save_button.setEnabled(True)

    def save_data(self):
        """Sauvegarde les données générées dans un fichier JSON."""
        open_page = self.main_app.get_open_page()
        if self.model is not None and hasattr(open_page, 'json_data') and open_page.json_data is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(open_page.json_data, f)
                self.show_message(f"Données sauvegardées avec succès dans {file_path}")
        else:
            self.show_message("Veuillez d'abord charger le fichier JSON et le modèle.")

    def show_message(self, message):
        """Affiche un message dans une boîte de dialogue."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
