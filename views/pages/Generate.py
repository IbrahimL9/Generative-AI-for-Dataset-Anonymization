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
from views.Styles import BUTTON_STYLE, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, INFO_MESSAGE_STYLE, BUTTON_STYLE2


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
        self.session_data = pd.DataFrame()

        self.session_id_map = {}
        self.actor_id_map = {}
        self.session_actor_map = {}

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addSpacing(20)

        title = QLabel("Generate")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        main_layout.addSpacing(100)

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

        txt_users = QLabel("Number of Unique Actors (0 = default):")
        txt_users.setFont(QFont("Montserrat", 14))
        txt_users.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.users_input = QLineEdit("0")
        self.users_input.setFixedWidth(200)
        self.users_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.users_input.setStyleSheet(self.records_input.styleSheet())
        form_layout.addRow(txt_users, self.users_input)

        form_container = QHBoxLayout()
        form_container.addStretch(1)
        form_container.addLayout(form_layout)
        form_container.addStretch(1)
        main_layout.addLayout(form_container)
        main_layout.addSpacing(40)

        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE2)
        self.generate_button.setFixedSize(200, 150)
        self.generate_button.setIcon(QIcon("images/generate.png"))
        self.generate_button.setIconSize(QSize(45, 45))
        self.generate_button.clicked.connect(self.generate_data)
        main_layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(200)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

    def load_session_data(self, data):
        self.session_data = data
        self.main_app.session_data = data

    def on_model_loaded(self, model):
        self.model = model
        self.model_loaded = True
        self.check_enable_generate_button()

    def on_file_loaded(self, json_data):
        self.json_data = json_data
        self.check_enable_generate_button()

    def check_enable_generate_button(self):
        if self.model is not None and getattr(self.model, "fitted", False):
            self.generate_button.setEnabled(True)

    def generate_data(self):
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

    def finish_generation(self, num_records):
        try:
            self.progress_bar.setVisible(False)

            if self.model:
                df = self.model.sample(num_records)
                df["Actor"] = df["Actor"].astype(str)

                try:
                    num_actors = int(self.users_input.text())
                except ValueError:
                    num_actors = 0

                # generation des actors rand
                if num_actors > 0:
                    chosen_ids = [self.random_id(6) for _ in range(num_actors)]
                    base_ids = chosen_ids[:]
                    remaining = len(df) - len(base_ids)
                    if remaining > 0:
                        base_ids += random.choices(chosen_ids, k=remaining)
                    random.shuffle(base_ids)
                    df["Actor"] = base_ids

                    self.actor_id_map = {actor: actor for actor in set(df["Actor"])}

                if "session_id" in df.columns:
                    df_sessions = (
                        df.groupby("session_id")
                          .apply(lambda grp: self._build_session(grp))
                          .reset_index(name="actions")
                    )
                    df_sessions.drop("session_id", axis=1, inplace=True)
                    self.generated_data = df_sessions
                    self.main_app.session_data = df_sessions.copy()
                    self.show_message(f"{len(df_sessions)} generated sessions.")
                else:
                    actions = [self._build_action(row, session_id=None) for _, row in df.iterrows()]
                    self.generated_data = actions
                    self.main_app.session_data = pd.DataFrame(actions)
                    self.show_message(f"{num_records} generated actions.")

                # Reinitialiser les mappings pour les sessions
                self.session_id_map.clear()
                self.session_actor_map.clear()
                # Ne vider le mapping des acteurs que si on n'a pas forcé un nombre spécifique (0 = génération naturelle)
                if int(self.users_input.text()) == 0:
                    self.actor_id_map.clear()

                self.data_generated = True
                self.data_generated_signal.emit()

        except Exception as e:
            self.show_message(f"Error while generating : {str(e)}", message_type="error")

    def _build_session(self, grp):
        session_id_value = grp["session_id"].iloc[0]
        if session_id_value not in self.session_id_map:
            self.session_id_map[session_id_value] = self.random_id(6)
        same_id_for_session = self.session_id_map[session_id_value]

        real_actor = grp["Actor"].iloc[0]
        if real_actor not in self.actor_id_map:
            self.actor_id_map[real_actor] = self.random_id(6)
        same_actor_for_session = self.actor_id_map[real_actor]

        actions_list = []
        for _, row in grp.iterrows():
            action_dict = self._build_action(
                row,
                session_id=session_id_value,
                override_id=same_id_for_session,
                override_actor=same_actor_for_session
            )
            actions_list.append(action_dict)
        return actions_list

    def _build_action(self, row, session_id=None, override_id=None, override_actor=None):
        action_id = override_id if override_id else self.random_id(6)

        # Utiliser l'actor_id_map si dispo
        raw_actor = str(row.get("Actor"))
        actor_id = override_actor if override_actor else self.actor_id_map.get(raw_actor, self.random_id(6))

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

    def random_id(self, length=6):
        return ''.join(random.choices(string.digits, k=length))

    def to_iso8601_timestamp(self, value):
        try:
            dt = pd.to_datetime(value, errors='coerce')
            if pd.isnull(dt):
                return str(value)
            return dt.isoformat(timespec='seconds')
        except:
            return str(value)

    def save_generated_data(self):
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