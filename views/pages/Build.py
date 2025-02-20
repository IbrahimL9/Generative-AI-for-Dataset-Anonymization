from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression

from views.Styles import BUTTON_STYLE


class Build(QWidget):
    def __init__(self, model=None):
        super().__init__()
        self.model = model  # Pour stocker le modèle entraîné ou chargé
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Ajouter un espace en haut
        layout.addStretch(1)

        label = QLabel("Build")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Bouton pour entraîner le modèle
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        self.train_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style
        self.train_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.train_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace réduit entre les boutons
        layout.addSpacing(10)

        # Bouton pour sauvegarder le modèle entraîné
        self.save_model_button = QPushButton("Save Model")
        self.save_model_button.clicked.connect(self.save_model)
        self.save_model_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style
        self.save_model_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.save_model_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace en bas
        layout.addStretch(2)

        self.setLayout(layout)

    def on_model_loaded(self, model):
        """Méthode appelée lorsque le modèle est chargé."""
        print("Signal de modèle chargé reçu dans Build.")  # Impression de débogage
        self.model = model
        print("Modèle chargé dans Build.")  # Impression de débogage

    def train_model(self):
        """Affiche une erreur si aucun modèle n'est chargé."""
        if self.model is None:
            self.show_message("Erreur : Aucun modèle n'est chargé. Veuillez charger un modèle d'abord.")
        else:
            print("Modèle déjà chargé.")

    def save_model(self):
        """Sauvegarde le modèle entraîné dans un fichier."""
        if self.model is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Model", "", "Pickle Files (*.pkl)")
            if file_path:
                with open(file_path, 'wb') as f:
                    pickle.dump(self.model, f)
                self.show_message(f"Modèle sauvegardé avec succès dans {file_path}")
        else:
            self.show_message("Erreur : Aucun modèle disponible à sauvegarder. Veuillez charger un modèle d'abord.")

    def show_message(self, message):
        """Affiche un message dans une boîte de dialogue."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()