import sys
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QProgressBar, QMessageBox, QDialog, QFileDialog, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import json
import pandas as pd
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, INFO_MESSAGE_STYLE

class Generate(QWidget):
    # Déclaration du signal pour notifier que les données ont été générées
    data_generated_signal = pyqtSignal()

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.model = None
        self.json_data = None
        self.model_loaded = False
        self.data_generated = False
        self.generated_data = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Titre
        title = QLabel("Generate")
        title.setFont(QFont("Montserrat", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)

        # Espacement sous le titre
        layout.addSpacing(10)

        # Formulaire
        form_layout = QFormLayout()
        form_layout.setContentsMargins(200, 10, 10, 10)  # Décale vers la droite

        self.records_input = QLineEdit("1000")
        self.records_input.setFixedWidth(300)
        self.records_input.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrer le texte
        form_layout.addRow("Number of Data to Generate:", self.records_input)
        layout.addLayout(form_layout)

        # 🔴 Réduction de l'espace AVANT le bouton "Generate"
        layout.addSpacing(-150)

        # Bouton "Generate"
        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE)
        self.generate_button.setFixedSize(150, 50)
        self.generate_button.clicked.connect(self.generate_data)
        layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # 🔵 Ajout d’un espace neutre sous le bouton pour ne pas impacter le reste
        layout.addSpacerItem(QSpacerItem(300, 150, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Espacement sous la barre de progression
        layout.addSpacing(5)

        # Bouton "Save"
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(150, 50)
        self.save_button.setVisible(False)
        self.save_button.clicked.connect(self.save_generated_data)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

        # Appliquer le style au champ de saisie
        self.records_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
                color: #333;
            }
        """)

    def on_model_loaded(self, model):
        self.model = model
        self.model_loaded = True
        self.check_enable_generate_button()

    def on_file_loaded(self, json_data):
        self.json_data = json_data
        self.check_enable_generate_button()

    def check_enable_generate_button(self):
        if self.model is not None and self.model.fitted:
            self.generate_button.setEnabled(True)

    def generate_data(self):
        if self.model is None or not self.model.fitted:
            QMessageBox.warning(self, "Erreur", "Veuillez entraîner un modèle avant de générer des données.")
            return

        try:
            num_records = int(self.records_input.text())
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nombre valide.")
            return

        self.progress_bar.setVisible(True)
        QTimer.singleShot(2000, lambda: self.finish_generation(num_records))

    def finish_generation(self, num_records):
        self.progress_bar.setVisible(False)

        if self.model:
            df = self.model.sample(num_records)  # Génération des données sous forme de DataFrame
            print("🔍 Données générées :", df)

            # ✅ Transformation des données en format JSON détaillé
            #self.generated_data = []
            #for _, row in df.iterrows():
                #entry = {
                    #"id": str(uuid.uuid4()),  # Générer un UUID unique pour chaque entrée
                    #"timestamp": datetime.now().isoformat(),  # Ajouter un timestamp formaté
            self.generated_data = []
            for index, row in df.iterrows():
                entry = {
                    "id": str(uuid.uuid4()),  # Utilisation de l'index pour générer un ID dans le format souhaité
                    "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),  # Format du timestamp sans millisecondes
                    "verb": {
                        "id": f"https://w3id.org/xapi/dod-isd/verbs/{row['Verb']}"
                    },
                    "actor": {
                        "mbox": f"mailto:{row['Actor']}@open.ac.uk"
                    },
                    "object": {
                        "id": f"http://open.ac.uk/{row['Object']}"
                    }
                }
                self.generated_data.append(entry)  # Ajouter l'entrée formatée

        self.data_generated = True
        self.show_message(f"{num_records} données générées avec succès.")
        self.save_button.setVisible(True)

        # Émettre le signal pour passer à la page "Save"
        self.data_generated_signal.emit()

    def save_generated_data(self):
        if not self.data_generated:
            QMessageBox.warning(self, "Erreur", "Aucune donnée à sauvegarder.")
            return

        file_dialog = QFileDialog()
        file_name, _ = file_dialog.getSaveFileName(self, "Enregistrer les données", "", "JSON Files (*.json)")

        if file_name:
            with open(file_name, "w") as file:
                json.dump(self.generated_data, file, indent=2)  # Sauvegarder les données générées

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