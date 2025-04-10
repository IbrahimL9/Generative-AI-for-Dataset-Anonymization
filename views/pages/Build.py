import time
import pandas as pd
import pickle
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog, QPlainTextEdit, QApplication, QSpacerItem,
    QSizePolicy, QHBoxLayout, QComboBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE, BUTTON_STYLE2
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
        self.total_steps = 200

    def run(self):
        for epoch in range(self.total_steps):
            time.sleep(0.5)
            self.update_progress(epoch)
            if epoch == self.total_steps - 1:
                self.model.fit(self.df)
                self.model.fitted = True
                self.training_finished.emit(self.model)

    def update_progress(self, epoch):
        # Limit the frequency of updates to every 10 steps (for example)
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
        layout.addSpacing(30)

        # Centered title
        title = QLabel("Build Model", self)
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addSpacing(32)

        # Layout for data mode selection
        self.mode_selection_layout = QHBoxLayout()
        self.mode_selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ComboBox pour choisir le mode (Actions ou Sessions)
        self.mode_label = QLabel("Data Mode :")
        self.mode_label.setFont(QFont("Arial", 12))
        self.data_mode_combo = QComboBox()
        self.data_mode_combo.addItems(["Actions", "Sessions"])
        self.mode_selection_layout.addWidget(self.mode_label)
        self.mode_selection_layout.addWidget(self.data_mode_combo)

        # Add the mode selection layout
        layout.addLayout(self.mode_selection_layout)
        layout.addSpacing(20)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        # "Train Model" BUTTON
        self.train_model_button = QPushButton("Train Model", self)
        self.train_model_button.setStyleSheet(BUTTON_STYLE2)
        self.train_model_button.setFixedSize(200, 150)
        self.train_model_button.setIcon(QIcon("images/train.png"))
        self.train_model_button.setIconSize(QSize(45, 45))
        self.train_model_button.clicked.connect(self.train_model)
        button_layout.addWidget(self.train_model_button)

        # "Save Model" BUTTON
        self.save_model_button = QPushButton("Save Model", self)
        self.save_model_button.setStyleSheet(BUTTON_STYLE2)
        self.save_model_button.setFixedSize(200, 150)
        self.save_model_button.setIcon(QIcon("images/save.png"))
        self.save_model_button.setIconSize(QSize(40, 40))
        self.save_model_button.setEnabled(False)
        self.save_model_button.clicked.connect(self.save_model)
        button_layout.addWidget(self.save_model_button)

        # Add the button layout
        layout.addLayout(button_layout)
        layout.addSpacing(100)

        # Text area to display messages
        self.output_edit = QPlainTextEdit(self)
        self.output_edit.setReadOnly(True)
        self.output_edit.setFrameStyle(0)
        font = QFont("Montserrat", 10, QFont.Weight.Medium)
        self.output_edit.setFont(font)
        self.output_edit.setStyleSheet("color: red;")
        layout.addWidget(self.output_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(22)

        self.setLayout(layout)

    def on_model_loaded(self, model):
        self.model = model
        self.save_model_button.setEnabled(True)
        self.output_edit.setPlainText("✅ Model loaded successfully!")

    def train_model(self):
        if not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None:
            self.show_message("Error: No data loaded. Please load a JSON file via DownloadButton.")
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
        # Update the output with progress text
        self.output_edit.setPlainText(text)
        self.output_edit.verticalScrollBar().setValue(self.output_edit.verticalScrollBar().maximum())

    def training_done(self, trained_model):
        self.model = trained_model
        self.output_edit.setPlainText("✅ Training completed successfully!")
        self.save_model_button.setEnabled(True)

        if hasattr(self.main_app, "pages") and "generate" in self.main_app.pages:
            self.main_app.pages["generate"].on_model_loaded(self.model)

    def save_model(self):
        if self.model is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Model", "", "Pickle Files (*.pkl)")
            if file_path:
                with open(file_path, 'wb') as f:
                    pickle.dump(self.model, f)
                self.show_message(f"Model successfully saved to {file_path}")
        else:
            self.show_message("Error: No model available to save. Please load or train a model first.")

    def show_message(self, message, message_type="info"):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)

        # Apply style based on message type
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

        # 1) Convertir en datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['Actor'] = df['Actor'].astype(str)

        # 2) Trier
        df = df.sort_values(by=['Actor', 'timestamp'])

        # 3) Construire la durée de chaque évènement
        df['Duration'] = 0.0
        session_gap = 300  # 5 minutes
        estimated_duration = 60  # 60 secondes par défaut

        for actor, group in df.groupby('Actor'):
            timestamps = group['timestamp'].tolist()
            indices = group.index.tolist()

            for i in range(len(indices) - 1):
                current_idx = indices[i]
                next_idx = indices[i + 1]

                delta = (timestamps[i + 1] - timestamps[i]).total_seconds()
                if delta <= session_gap:
                    df.at[current_idx, 'Duration'] = delta
                else:
                    df.at[current_idx, 'Duration'] = estimated_duration

            # Dernier événement de l'utilisateur
            df.at[indices[-1], 'Duration'] = estimated_duration

        # 4) Si on est en mode "Sessions", identifier les sessions
        mode = self.data_mode_combo.currentText()
        if mode == "Sessions":
            # Important : on calcule la différence pendant que c'est encore un datetime
            df['time_diff'] = df.groupby('Actor')['timestamp'].diff().fillna(pd.Timedelta(seconds=0))
            df['new_session'] = (df['time_diff'] > pd.Timedelta(minutes=5)).astype(int)
            df['session_id'] = df.groupby('Actor')['new_session'].cumsum()
            df.drop(columns=['time_diff', 'new_session'], inplace=True)

            # On garde la colonne session_id
            cols = ['timestamp', 'Duration', 'Actor', 'Verb', 'Object', 'session_id']
        else:
            cols = ['timestamp', 'Duration', 'Actor', 'Verb', 'Object']

        df = df[cols]

        # 5) (Optionnel) Convertir le timestamp en string une fois la logique sessions terminée
        df['timestamp'] = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")

        return df


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
