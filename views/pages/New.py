from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
import pickle
from .Styles1 import BUTTON_STYLE
# Définir les styles


class New(QWidget):
    model_loaded = pyqtSignal(object)  # Signal pour notifier que le modèle est chargé

    def __init__(self):
        super().__init__()
        self.model = None  # Pour stocker le modèle entraîné
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Ajouter un espace en haut
        layout.addStretch(1)

        label = QLabel("New")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Bouton pour charger un modèle entraîné
        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.clicked.connect(self.load_model)
        self.load_model_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style
        self.load_model_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.load_model_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace en bas
        layout.addStretch(2)

        self.setLayout(layout)

    def load_model(self):
        """Charge un modèle entraîné à partir d'un fichier."""
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()

        if not open_page.json_data:
            self.show_message("Veuillez d'abord charger le fichier JSON dans la page Open.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Load Model", "", "Pickle Files (*.pkl)")
        if file_path:
            with open(file_path, 'rb') as f:
                self.model = pickle.load(f)
            print("Modèle chargé depuis le fichier :", file_path)  # Impression de débogage
            self.show_message(f"Modèle chargé avec succès depuis {file_path}")
            # Émettre un signal pour informer que le modèle est chargé
            self.model_loaded.emit(self.model)
            print("Signal de modèle chargé émis.")  # Impression de débogage

    def show_message(self, message):
        """Affiche un message dans une boîte de dialogue."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
