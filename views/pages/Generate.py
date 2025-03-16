import sys
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QProgressBar, QMessageBox, QDialog, QFileDialog, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
import json
import pandas as pd
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE, BUTTON_STYLE2


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
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addSpacing(20)

        # Titre centré
        title = QLabel("Generate")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        main_layout.addSpacing(100)

        # Création du formulaire
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        # Label pour le formulaire
        txt = QLabel("Number of Data to Generate:")
        txt.setFont(QFont("Montserrat", 14))
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Champ de saisie
        self.records_input = QLineEdit("1000")
        self.records_input.setFixedWidth(200)
        self.records_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        form_layout.addRow(txt, self.records_input)

        # Encapsulation du form_layout dans un QHBoxLayout pour le centrer horizontalement
        form_container = QHBoxLayout()
        form_container.addStretch(1)
        form_container.addLayout(form_layout)
        form_container.addStretch(1)
        main_layout.addLayout(form_container)

        main_layout.addSpacing(40)

        # Bouton "Generate" centré
        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE2)
        self.generate_button.setFixedSize(200, 150)
        self.generate_button.setIcon(QIcon("images/generate.png"))
        self.generate_button.setIconSize(QSize(45, 45))
        self.generate_button.clicked.connect(self.generate_data)
        main_layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Barre de progression (invisible au départ)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

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
            self.generated_data = []
            for index, row in df.iterrows():
                entry = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    "verb": {"id": f"https://w3id.org/xapi/dod-isd/verbs/{row['Verb']}"},
                    "actor": {"mbox": f"mailto:{row['Actor']}@open.ac.uk"},
                    "object": {"id": f"http://open.ac.uk/{row['Object']}"}
                }
                self.generated_data.append(entry)
        self.data_generated = True
        self.show_message(f"{num_records} données générées avec succès.")


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