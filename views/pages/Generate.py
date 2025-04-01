import sys
import random
import string
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QProgressBar, QMessageBox, QDialog, QFileDialog, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE, BUTTON_STYLE2

class Generate(QWidget):
    data_generated_signal = pyqtSignal()

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.model = None
        self.json_data = None
        self.model_loaded = False
        self.data_generated = False
        self.generated_data = None

        # Pour forcer le même ID dans une session
        # session_id -> ID unique pour toutes les actions
        self.session_id_map = {}

        # Pour forcer le même Actor dans une session
        # session_id -> ID unique d'acteur (qui ira dans actor/mbox)
        self.session_actor_map = {}


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

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        txt = QLabel("Number of Data to Generate:")
        txt.setFont(QFont("Montserrat", 14))
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        form_container = QHBoxLayout()
        form_container.addStretch(1)
        form_container.addLayout(form_layout)
        form_container.addStretch(1)
        main_layout.addLayout(form_container)

        main_layout.addSpacing(40)

        # Bouton Generate
        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE2)
        self.generate_button.setFixedSize(200, 150)
        self.generate_button.setIcon(QIcon("images/generate.png"))
        self.generate_button.setIconSize(QSize(45, 45))
        self.generate_button.clicked.connect(self.generate_data)
        main_layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(200)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

    def on_model_loaded(self, model):
        """Appelé quand le modèle est chargé ou entraîné."""
        self.model = model
        self.model_loaded = True
        self.check_enable_generate_button()

    def on_file_loaded(self, json_data):
        """Appelé quand un fichier JSON est chargé."""
        self.json_data = json_data
        self.check_enable_generate_button()

    def check_enable_generate_button(self):
        """Active le bouton Generate si le modèle est prêt."""
        if self.model is not None and getattr(self.model, "fitted", False):
            self.generate_button.setEnabled(True)

    def generate_data(self):
        """Cliqué sur 'Generate'."""
        if self.model is None or not getattr(self.model, "fitted", False):
            QMessageBox.warning(self, "Error", "Please train a model before generating data.")
            return

        try:
            num_records = int(self.records_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid number.")
            return

        self.progress_bar.setVisible(True)
        QTimer.singleShot(2000, lambda: self.finish_generation(num_records))

    # -----------------------------------------------------------------------
    #  FINISH GENERATION
    # -----------------------------------------------------------------------


    def finish_generation(self, num_records):
        """
        Génère les données. Dans le cas "Sessions", TOUTES les actions
        de la même session auront le même 'id' ET le même 'actor'.
        """
        try:
            self.progress_bar.setVisible(False)

            if self.model:
                # On sample num_records lignes
                df = self.model.sample(num_records)

                # On nettoie les dictionnaires
                self.session_id_map.clear()
                self.session_actor_map.clear()

                # Vérifie si "session_id" existe
                if "session_id" in df.columns:
                    # => MODE SESSIONS
                    df_sessions = (
                        df.groupby("session_id")
                          .apply(lambda grp: self._build_session(grp))
                          .reset_index(name="actions")
                    )
                    df_sessions.drop("session_id", axis=1, inplace=True)
                    self.generated_data = df_sessions
                    self.show_message(f"{len(df_sessions)} sessions générées.")
                else:
                    # => MODE ACTIONS
                    # Pas de notion de session => on génère action par action
                    actions = [self._build_action(row, session_id=None) for _, row in df.iterrows()]
                    self.generated_data = actions
                    self.show_message(f"{num_records} actions générées.")

            self.data_generated = True
            self.data_generated_signal.emit()

        except Exception as e:
            self.show_message(f"Erreur pendant la génération : {str(e)}", message_type="error")

    def _build_session(self, grp):
        """
        Construit la liste d'actions pour UNE session,
        en forçant le même 'id' ET le même actor pour toutes les actions.
        """
        session_id_value = grp["session_id"].iloc[0]  # la valeur de la session

        # - 1) Récupère ou crée un ID unique pour TOUTES les actions de cette session
        if session_id_value not in self.session_id_map:
            self.session_id_map[session_id_value] = self.random_id(6)
        same_id_for_session = self.session_id_map[session_id_value]

        # - 2) Récupère ou crée un Actor unique pour TOUTES les actions de cette session
        if session_id_value not in self.session_actor_map:
            self.session_actor_map[session_id_value] = self.random_id(6)
        same_actor_for_session = self.session_actor_map[session_id_value]

        actions_list = []
        for _, row in grp.iterrows():
            # On construit une action
            action_dict = self._build_action(
                row,
                session_id=session_id_value,
                override_id=same_id_for_session,
                override_actor=same_actor_for_session
            )
            actions_list.append(action_dict)
        return actions_list

    def _build_action(self, row, session_id=None, override_id=None, override_actor=None):
        """
        Construit un dictionnaire xAPI-like pour une action.
        - override_id : si fourni, c'est l'ID qu'on va utiliser pour l'action
        - override_actor : si fourni, c'est l'actor qu'on va utiliser
        """
        # ID d'action => soit override_id, soit un ID random
        if override_id:
            action_id = override_id
        else:
            action_id = self.random_id(6)

        # Actor => soit override_actor, soit un ID random
        if override_actor:
            actor_id = override_actor
        else:
            actor_id = self.random_id(6)

        return {
            "id": action_id,
            "timestamp": self.to_iso8601_timestamp(row.get("timestamp")),
            "verb": {
                "id": f"https://w3id.org/xapi/dod-isd/verbs/{row.get('Verb', 'unknown')}"
            },
            "actor": {
                "mbox": f"mailto:{actor_id}@open.ac.uk"
            },
            "object": {
                "id": f"http://open.ac.uk/{row.get('Object', 'unknown')}"
            },
            "duration": float(row.get("Duration", 0.0))
        }

    # -----------------------------------------------------------------------
    #  OUTILS
    # -----------------------------------------------------------------------

    def random_id(self, length=6):
        import string, random
        return ''.join(random.choices(string.digits, k=length))

    def to_iso8601_timestamp(self, value):
        """Convertit value en 'YYYY-MM-DDTHH:MM:SS' ou renvoie str(value) si impossible."""
        import pandas as pd
        try:
            dt = pd.to_datetime(value, errors='coerce')
            if pd.isnull(dt):
                return str(value)
            return dt.isoformat(timespec='seconds')
        except:
            return str(value)

    # -----------------------------------------------------------------------
    #  SAUVEGARDE
    # -----------------------------------------------------------------------


    def save_generated_data(self):
        """
        Si mode "Sessions", self.generated_data est un DataFrame avec col "actions" (list of dicts)
        Sinon, c'est une liste de dicts.
        """
        if not self.data_generated or not self.generated_data:
            QMessageBox.warning(self, "Error", "No data to save.")
            return

        dialog = QFileDialog()
        file_name, _ = dialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
        if not file_name:
            return

        import json
        if isinstance(self.generated_data, pd.DataFrame) and "actions" in self.generated_data.columns:
            data_to_save = self.generated_data["actions"].tolist()
        else:
            data_to_save = self.generated_data

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)

        self.show_message(f"Data successfully saved to {file_name}", "success")

    def show_message(self, message, message_type="info"):
        dlg = QDialog(self)
        dlg.setWindowTitle("Information")
        layout = QVBoxLayout(dlg)
        lbl = QLabel(message)
        if message_type == "success":
            lbl.setStyleSheet(SUCCESS_MESSAGE_STYLE)
        elif message_type == "error":
            lbl.setStyleSheet(ERROR_MESSAGE_STYLE)
        elif message_type == "warning":
            lbl.setStyleSheet(WARNING_MESSAGE_STYLE)
        else:
            lbl.setStyleSheet(INFO_MESSAGE_STYLE)
        layout.addWidget(lbl)
        dlg.exec()
