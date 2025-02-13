import json
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QDialog, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from views.Styles import BUTTON_STYLE

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
import pickle

class GenerateDataPage(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button  # L'instance de DownloadButton
        self.download_button.file_loaded.connect(self.on_file_loaded)  # Connexion au signal
        self.model = None  # Pour stocker le modèle entraîné
        self.generated_data = None  # Pour stocker les données générées
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)  # Réduire les marges en haut et en bas
        layout.setSpacing(10)  # Réduire l'espacement entre les widgets

        label = QLabel("Generate Data Page")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace réduit en haut
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Bouton pour entraîner le modèle
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        self.train_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style importé
        self.train_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.train_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace réduit entre les boutons
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Bouton pour générer de nouvelles données
        self.generate_button = QPushButton("Generate Data")
        self.generate_button.clicked.connect(self.generate_data)
        self.generate_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style importé
        self.generate_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace réduit entre les boutons
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Bouton pour exporter les données générées
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setStyleSheet(BUTTON_STYLE)  # Appliquer le style importé
        self.export_button.setFixedWidth(200)  # Définir une largeur fixe
        layout.addWidget(self.export_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajouter un espace réduit en bas
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.setLayout(layout)

        # Désactiver les boutons par défaut
        self.train_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.export_button.setEnabled(False)

    def on_file_loaded(self):
        """Mise à jour de l'UI lorsque le fichier est chargé."""
        # Activer les boutons lorsque le fichier est chargé
        self.train_button.setEnabled(True)
        self.generate_button.setEnabled(False)  # Activer après l'entraînement
        self.export_button.setEnabled(False)  # Activer après la génération de données

    def train_model(self):
        """Entraîne le modèle à partir des données JSON."""
        if self.download_button.json_data is not None:
            data = self.download_button.json_data
            if 'events' in data:
                # Convertir les données en DataFrame
                df = pd.DataFrame(data['events'])

                # Prétraitement des données
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['dayofweek'] = df['timestamp'].dt.dayofweek

                # Séparer les caractéristiques et la cible avant l'encodage
                X = df[['actor', 'verb', 'object', 'hour', 'dayofweek']]
                y = df['verb']  # Par exemple, prédire le verbe

                # Encodage des caractéristiques catégorielles
                encoder = OneHotEncoder(sparse_output=False)
                encoded_features = encoder.fit_transform(X[['actor', 'verb', 'object']])

                # Créer un DataFrame avec les caractéristiques encodées
                df_encoded = pd.DataFrame(encoded_features)
                df_encoded['hour'] = X['hour']
                df_encoded['dayofweek'] = X['dayofweek']

                # Convertir les noms des colonnes en chaînes de caractères
                df_encoded.columns = df_encoded.columns.astype(str)

                # Diviser les données en ensembles d'entraînement et de test
                X_train, X_test, y_train, y_test = train_test_split(df_encoded, y, test_size=0.2, random_state=42)

                # Entraîner un modèle simple
                model = LogisticRegression(max_iter=1000)
                model.fit(X_train, y_train)
                self.model = model
                self.generate_button.setEnabled(True)
                self.show_message("Model trained successfully!")
            else:
                self.show_message("Invalid data format: Missing 'events' key.")
        else:
            self.show_message("No data available for training.")

    def generate_data(self):
        """Génère de nouvelles données basées sur le modèle entraîné."""
        if self.model is not None:
            # Exemple simple de génération de données
            # Vous pouvez adapter cette logique en fonction de votre cas d'utilisation
            # Générer des données aléatoires pour l'exemple
            new_data = {
                "events": [
                    {
                        "timestamp": "2023-10-01T10:00:00",
                        "actor": "new_user@example.com",
                        "verb": "view",
                        "object": "http://example.com/new1"
                    },
                    {
                        "timestamp": "2023-10-01T11:00:00",
                        "actor": "new_user2@example.com",
                        "verb": "submit",
                        "object": "http://example.com/new2"
                    }
                ]
            }
            self.generated_data = new_data
            self.export_button.setEnabled(True)
            self.show_message("Data generated successfully!")
        else:
            self.show_message("No model available for data generation.")

    def export_data(self):
        """Exporte les données générées dans un fichier JSON."""
        if self.generated_data is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Generated Data", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.generated_data, f, ensure_ascii=False, indent=4)
                self.show_message(f"Generated data exported successfully to {file_path}")
        else:
            self.show_message("No generated data available for export.")

    def show_message(self, message):
        """Affiche un message dans une boîte de dialogue."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
