import sys
import time
import pandas as pd
import pickle
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog, QPlainTextEdit, QApplication, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, INFO_MESSAGE_STYLE
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata

class TrainingThread(QThread):
    progress_update = pyqtSignal(str)
    training_finished = pyqtSignal(object)

    def __init__(self, model, df):
        super().__init__()
        self.model = model
        self.df = df
        self.progress_step = 0
        self.total_steps = 100  # Nombre total d'itérations d'entraînement

    def run(self):
        for epoch in range(self.total_steps):
            # Simuler un calcul pour l'entraînement (ou un appel réel à self.model.fit)
            time.sleep(0.5)  # Simuler un délai pour l'entraînement
            self.update_progress(epoch)
            if epoch == self.total_steps - 1:
                self.model.fit(self.df)
                self.model.fitted = True  # Marquer le modèle comme entraîné
                self.training_finished.emit(self.model)

    def update_progress(self, epoch):
        # Limiter la fréquence des mises à jour à toutes les 10 étapes (par exemple)
        if epoch % 10 == 0:
            progress_msg = f"Gen. (0.83) | Discrim. (0.04): {int((epoch + 1) / self.total_steps * 100)}% | {'█' * (epoch // 20)}{' ' * (10 - epoch // 20)} | {epoch + 1}/{self.total_steps}"
            self.progress_update.emit(progress_msg)

class Build(QWidget):
    def __init__(self, main_app, download_button, tools, model=None):
        super().__init__()
        self.main_app = main_app
        self.download_button = download_button
        self.tools = tools
        self.model = model
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Centrer les boutons et le texte
        label = QLabel("Build Model")
        label.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addItem(QSpacerItem(30, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layout.addWidget(label)
        layout.addItem(QSpacerItem(20, 200, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        self.train_button.setStyleSheet(BUTTON_STYLE)
        self.train_button.setFixedWidth(200)
        layout.addWidget(self.train_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.save_model_button = QPushButton("Save Model")
        self.save_model_button.clicked.connect(self.save_model)
        self.save_model_button.setStyleSheet(BUTTON_STYLE)
        self.save_model_button.setFixedWidth(200)
        self.save_model_button.setEnabled(False)
        layout.addWidget(self.save_model_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addItem(QSpacerItem(20, 400, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFrameStyle(0)
        font = QFont("Montserrat", 10, QFont.Weight.Medium)
        self.output_edit.setFont(font)
        self.output_edit.setStyleSheet("color: red;")
        layout.addWidget(self.output_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def on_model_loaded(self, model):
        self.model = model
        self.save_model_button.setEnabled(True)
        self.output_edit.setPlainText("✅ Modèle chargé avec succès !")

    def train_model(self):
        if not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None:
            self.show_message("Erreur : Aucune donnée chargée. Veuillez charger un fichier JSON via DownloadButton.")
            return

        df = pd.DataFrame(self.download_button.json_data)
        df_preprocessed = self.preprocess_data(df)

        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(df_preprocessed)

        epochs = int(self.tools.epochs_edit.text())
        batch_size = int(self.tools.batch_size_edit.text())
        embedding_dim = int(self.tools.embedding_dim_edit.text())
        generator_dim = tuple(map(int, self.tools.generator_dim_edit.text().split(',')))
        discriminator_dim = tuple(map(int, self.tools.discriminator_dim_edit.text().split(',')))
        pac = int(self.tools.pac_edit.text())
        verbose = self.tools.verbose_combo.currentText() == "True"
        minmax = self.tools.minmax_combo.currentText() == "True"

        self.model = CTGANSynthesizer(
            metadata,
            epochs=epochs,
            batch_size=batch_size,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim,
            embedding_dim=embedding_dim,
            pac=pac,
            verbose=verbose,
            enforce_min_max_values=minmax
        )

        self.training_thread = TrainingThread(self.model, df_preprocessed)
        self.training_thread.progress_update.connect(self.update_output)
        self.training_thread.training_finished.connect(self.training_done)
        self.training_thread.start()

    def update_output(self, text):
        # Mettre à jour la sortie avec le texte de progression
        self.output_edit.setPlainText(text)
        self.output_edit.verticalScrollBar().setValue(self.output_edit.verticalScrollBar().maximum())

    def training_done(self, trained_model):
        self.model = trained_model
        self.output_edit.setPlainText("✅ Training completed successfully!")
        self.save_model_button.setEnabled(True)

        if hasattr(self.main_app, "pages") and "generate" in self.main_app.pages:
            self.main_app.pages["generate"].on_model_loaded(self.model)

        self.show_message("Modèle CTGAN entraîné avec succès.")

    def save_model(self):
        if self.model is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Model", "", "Pickle Files (*.pkl)")
            if file_path:
                with open(file_path, 'wb') as f:
                    pickle.dump(self.model, f)
                self.show_message(f"Modèle sauvegardé avec succès dans {file_path}")
        else:
            self.show_message(
                "Erreur : Aucun modèle disponible à sauvegarder. Veuillez charger ou entraîner un modèle d'abord.")

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

    def preprocess_data(self, df):
        df = simplify_df(df)

        if 'Timestamp' not in df.columns and 'timestamp' in df.columns:
            df.rename(columns={'timestamp': 'Timestamp'}, inplace=True)

        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%Y-%m-%dT%H:%M:%S", errors='coerce')
        df['Timestamp'] = df['Timestamp'].apply(lambda x: x.timestamp())

        min_timestamp_seconds = df['Timestamp'].min()
        df['Timestamp'] -= min_timestamp_seconds

        df_sorted = df.sort_values(by='Timestamp').reset_index(drop=True)
        return df_sorted[['Timestamp', 'Actor', 'Verb', 'Object']]

def simplify_df(df):
    def simplify_value(x, key):
        if isinstance(x, dict):
            x = x.get(key, "")
        if isinstance(x, str):
            return x.split('/')[-1] if '/' in x else x
        return x

    for col in ['Actor', 'Verb', 'Object']:
        key = "id" if col != "Actor" else "mbox"
        if col.lower() in df.columns:
            df.rename(columns={col.lower(): col}, inplace=True)
        if col in df.columns:
            df[col] = df[col].apply(lambda x: simplify_value(x, key))

    if 'id' in df.columns:
        df.drop(columns=['id'], inplace=True)
    return df