from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
import pandas as pd
from datetime import datetime

class Display(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Display Generated Data")
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Filtres
        self.filter_group = QGroupBox("🔍 Filters")
        self.filter_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #7E88AB;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                margin-top: 10px;
                background: transparent;
            }
        """)
        filter_layout = QHBoxLayout()
        self.filter_group.setLayout(filter_layout)

        # Verbe
        verb_layout = QHBoxLayout()
        verb_label = QLabel("Verb:")
        self.verb_combobox = QComboBox()
        self.verb_combobox.setFixedWidth(120)
        self.verb_combobox.setVisible(False)
        self.verb_checkbox = QCheckBox("Enable")
        self.verb_checkbox.stateChanged.connect(self.toggle_verb_combobox)
        verb_layout.addWidget(verb_label)
        verb_layout.addWidget(self.verb_combobox)
        verb_layout.addWidget(self.verb_checkbox)

        # Acteur
        actor_layout = QHBoxLayout()
        actor_label = QLabel("Actor:")
        self.actor_combobox = QComboBox()
        self.actor_combobox.setFixedWidth(120)
        self.actor_combobox.setVisible(False)
        self.actor_checkbox = QCheckBox("Enable")
        self.actor_checkbox.stateChanged.connect(self.toggle_actor_combobox)
        actor_layout.addWidget(actor_label)
        actor_layout.addWidget(self.actor_combobox)
        actor_layout.addWidget(self.actor_checkbox)

        # Limite
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Max Events:")
        self.number_input = QSpinBox()
        self.number_input.setMinimum(0)
        self.number_input.setMaximum(10000)
        self.number_input.setValue(0)
        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.number_input)

        # Bouton appliquer
        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.setStyleSheet("""
            QPushButton {
                background-color: #6B748F;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A627D;
            }
        """)
        self.filter_button.clicked.connect(self.appliquer_filtre)

        # Ajout au layout des filtres
        filter_layout.addLayout(verb_layout)
        filter_layout.addLayout(actor_layout)
        filter_layout.addLayout(limit_layout)
        filter_layout.addWidget(self.filter_button)
        self.layout.addWidget(self.filter_group)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Duration (s)", "Actor", "Verb", "Object"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #F1F3F8;
                border: 2px solid #7E88AB;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                selection-background-color: #D0D7E5;
                alternate-background-color: #E5E9F2;
            }
            QHeaderView::section {
                background-color: #7E88AB;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #5F6889;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #D0D7E5;
                color: black;
            }
        """)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        self.updateTable()

    def showEvent(self, event):
        self.updateTable()
        super().showEvent(event)

    def extract_name(self, value):
        if isinstance(value, str):
            if "mailto:" in value:
                return value.replace("mailto:", "")
            elif value.startswith("http"):
                return value.split("/")[-1]
        return str(value)

    def toggle_verb_combobox(self, checked):
        self.verb_combobox.setVisible(checked)

    def toggle_actor_combobox(self, checked):
        self.actor_combobox.setVisible(checked)

    def updateTable(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            raw_data = self.download_button.json_data

            if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], list):
                all_events = []
                for batch in raw_data:
                    all_events.extend(batch)
            else:
                all_events = raw_data

            all_events = self.convert_to_duration(all_events)
            self.afficher_tableau(all_events)

            # Filtres
            verbs = list(set(self.extract_name(e.get("verb", {}).get("id", "")) for e in all_events if isinstance(e.get("verb"), dict)))
            self.verb_combobox.clear()
            self.verb_combobox.addItems(verbs)

            actors = list(set(self.extract_name(e.get("actor", {}).get("mbox", "")) for e in all_events if isinstance(e.get("actor"), dict)))
            self.actor_combobox.clear()
            self.actor_combobox.addItems(actors)
        else:
            self.table.setRowCount(0)

    def appliquer_filtre(self):
        if not self.download_button.json_data:
            QMessageBox.warning(self, "Error", "No data loaded.")
            return

        selected_actor = self.actor_combobox.currentText() if self.actor_checkbox.isChecked() else ""
        selected_verb = self.verb_combobox.currentText() if self.verb_checkbox.isChecked() else ""
        max_events = self.number_input.value()

        filtered_events = []

        for e in self.download_button.json_data:
            if isinstance(e, dict):
                actor = e.get("actor", {})
                actor_name = self.extract_name(actor.get("mbox", ""))
                verb = e.get("verb", {})
                verb_name = self.extract_name(verb.get("id", ""))

                if (not selected_actor or selected_actor.strip().lower() == actor_name.strip().lower()) and \
                   (not selected_verb or selected_verb.strip().lower() == verb_name.strip().lower()):
                    filtered_events.append(e)

        if filtered_events:
            if max_events > 0:
                filtered_events = filtered_events[:max_events]
            self.afficher_tableau(filtered_events)
        else:
            QMessageBox.warning(self, "No Events", "No events found for the selected actor and verb.")

    def afficher_tableau(self, events):
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            try:
                duration = event.get("Duration", 0)
                if isinstance(duration, (int, float)):
                    duration = f"{duration:.2f}"
                self.table.setItem(row, 0, QTableWidgetItem(str(duration)))
                self.table.setItem(row, 1, QTableWidgetItem(self.extract_name(event.get("actor", {}).get("mbox", ""))))
                self.table.setItem(row, 2, QTableWidgetItem(self.extract_name(event.get("verb", {}).get("id", ""))))
                self.table.setItem(row, 3, QTableWidgetItem(self.extract_name(event.get("object", {}).get("id", ""))))

                if row % 2 == 0:
                    for col in range(4):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(QColor("#E5E9F2"))
            except Exception as e:
                pass

    def convert_to_duration(self, events):
        try:
            df = pd.DataFrame(events)

            if 'timestamp' not in df.columns:
                if 'Timestamp' in df.columns:
                    df['timestamp'] = df['Timestamp']
                else:
                    return events

            if 'actor' not in df.columns:
                if 'Actor' in df.columns:
                    df['actor'] = df['Actor']
                else:
                    return events

            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            df['actor_name'] = df['actor'].apply(
                lambda a: self.extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a)
            )

            df = df.sort_values(by=['actor_name', 'timestamp'])
            df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds()
            df['Duration'] = df['Duration'].fillna(0)

            for i in range(len(df)):
                if i < len(events):
                    events[i]['Duration'] = float(df.iloc[i]['Duration'])

        except Exception:
            pass

        return events
