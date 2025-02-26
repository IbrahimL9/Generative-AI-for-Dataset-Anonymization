from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog, QProgressBar, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import pandas as pd
from views.Styles import BUTTON_STYLE
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata

def simplify_df(df):
    # Traitement de la colonne Actor
    def simplify_actor(x):
        if isinstance(x, dict):
            x = x.get("mbox", "")
        if isinstance(x, str) and "mailto:" in x:
            return x.replace("mailto:", "").split('@')[0]
        return x

    if 'Actor' in df.columns:
        df['Actor'] = df['Actor'].apply(simplify_actor)
    elif 'actor' in df.columns:
        df.rename(columns={'actor': 'Actor'}, inplace=True)
        df['Actor'] = df['Actor'].apply(simplify_actor)

    # Traitement de la colonne Verb
    def simplify_verb(x):
        if isinstance(x, dict):
            x = x.get("id", "")
        if isinstance(x, str):
            return x.split('/')[-1]
        return x

    if 'Verb' in df.columns:
        df['Verb'] = df['Verb'].apply(simplify_verb)
    elif 'verb' in df.columns:
        df.rename(columns={'verb': 'Verb'}, inplace=True)
        df['Verb'] = df['Verb'].apply(simplify_verb)

    # Traitement de la colonne Object
    def simplify_object(x):
        if isinstance(x, dict):
            x = x.get("id", "")
        if isinstance(x, str):
            return x.split('/')[-1]
        return x

    if 'Object' in df.columns:
        df['Object'] = df['Object'].apply(simplify_object)
    elif 'object' in df.columns:
        df.rename(columns={'object': 'Object'}, inplace=True)
        df['Object'] = df['Object'].apply(simplify_object)

    # Supprimer la colonne 'id' si elle existe
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df


class Build(QWidget):
    def __init__(self, main_app, download_button, model=None):
        super().__init__()
        self.main_app = main_app  # Ajout de la référence à l'application principale
        self.download_button = download_button
        self.model = model
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Espace en haut
        layout.addStretch(1)

        label = QLabel("Build")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Bouton pour lancer l'entraînement (prétraitement + entraînement CTGAN)
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        self.train_button.setStyleSheet(BUTTON_STYLE)
        self.train_button.setFixedWidth(200)
        layout.addWidget(self.train_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Bouton pour sauvegarder le modèle (si applicable)
        self.save_model_button = QPushButton("Save Model")
        self.save_model_button.clicked.connect(self.save_model)
        self.save_model_button.setStyleSheet(BUTTON_STYLE)
        self.save_model_button.setFixedWidth(200)
        layout.addWidget(self.save_model_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Barre de chargement en bas (mode indéterminé)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Espace en bas
        layout.addStretch(2)
        self.setLayout(layout)

    def on_model_loaded(self, model):
        self.model = model
        self.model_loaded = True  # ✅ Marque le modèle comme chargé
        self.generate_button.setEnabled(True)  # ✅ Active le bouton Generate
        print("✅ Modèle chargé dans Generate. Bouton activé.")

    def train_model(self):
        """Entraîne un modèle CTGAN sur les données téléchargées."""
        if not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None:
            self.show_message("Erreur : Aucune donnée chargée. Veuillez charger un fichier JSON via DownloadButton.")
            return

        try:
            self.progress_bar.setVisible(True)
            QApplication.processEvents()

            # Conversion du JSON en DataFrame
            df = pd.DataFrame(self.download_button.json_data)
            df_preprocessed = self.preprocess_data(df)

            # Détection des métadonnées et création du modèle
            metadata = SingleTableMetadata()
            metadata.detect_from_dataframe(df_preprocessed)

            ctgan = CTGANSynthesizer(metadata, epochs=200)
            ctgan.fit(df_preprocessed)

            # ✅ Stocker le modèle
            self.model = ctgan

            # ✅ Envoyer le modèle à la page Generate
            if hasattr(self.main_app, "pages") and "generate" in self.main_app.pages:
                self.main_app.pages["generate"].on_model_loaded(self.model)
                print("✅ Modèle envoyé à la page Generate avec succès.")

            self.show_message("Modèle CTGAN entraîné avec succès.")

        except Exception as e:
            self.show_message(f"Erreur lors de l'entraînement du modèle CTGAN : {e}")

        finally:
            self.progress_bar.setVisible(False)

    def preprocess_data(self, df):
        # Simplifier les colonnes 'Actor', 'Verb' et 'Object'
        df = simplify_df(df)

        # Renommer 'timestamp' en 'Timestamp' si nécessaire
        if 'Timestamp' not in df.columns and 'timestamp' in df.columns:
            df.rename(columns={'timestamp': 'Timestamp'}, inplace=True)

        # Conversion de 'Timestamp' en datetime (format ISO, ex : "2013-09-21T00:00:00")
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%Y-%m-%dT%H:%M:%S", errors='coerce')
        if df['Timestamp'].isnull().any():
            problematic = df[df['Timestamp'].isnull()]
            print("Valeurs de Timestamp non convertibles :", problematic)
            raise ValueError("Certaines valeurs de 'Timestamp' n'ont pas pu être converties en datetime.")

        # Conversion en secondes depuis l'époque
        df['Timestamp'] = df['Timestamp'].apply(lambda x: x.timestamp())

        # Normalisation : soustraire le plus petit timestamp pour que le premier événement soit à 0
        min_timestamp_seconds = df['Timestamp'].min()
        df['Timestamp'] = df['Timestamp'] - min_timestamp_seconds

        # Trier le DataFrame par 'Timestamp' et réinitialiser l'index
        df_sorted = df.sort_values(by='Timestamp').reset_index(drop=True)

        # Réordonner les colonnes dans l'ordre désiré
        df_final = df_sorted[['Timestamp', 'Actor', 'Verb', 'Object']]
        return df_final

    def save_model(self):
        if self.model is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Model", "", "Pickle Files (*.pkl)")
            if file_path:
                with open(file_path, 'wb') as f:
                    import pickle
                    pickle.dump(self.model, f)
                self.show_message(f"Modèle sauvegardé avec succès dans {file_path}")
        else:
            self.show_message("Erreur : Aucun modèle disponible à sauvegarder. Veuillez charger ou entraîner un modèle d'abord.")

    def show_message(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
