from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
import pandas as pd
from datetime import datetime

class Display(QWidget):
    def __init__(self, download_button, main_app):
        super().__init__()
        self.download_button = download_button
        self.main_app = main_app  # Needed to store processed dataframe
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("Display Generated Data")
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        self.filter_group = QGroupBox("\U0001F50D Filters")
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

        self.verb_checkbox = QCheckBox("Enable Verb")
        self.verb_combobox = QComboBox()
        self.verb_combobox.setFixedWidth(120)
        self.verb_combobox.setVisible(False)
        self.verb_checkbox.stateChanged.connect(lambda state: self.verb_combobox.setVisible(state == Qt.CheckState.Checked))

        verb_layout = QHBoxLayout()
        verb_layout.addWidget(QLabel("Verb:"))
        verb_layout.addWidget(self.verb_combobox)
        verb_layout.addWidget(self.verb_checkbox)

        self.actor_checkbox = QCheckBox("Enable Actor")
        self.actor_combobox = QComboBox()
        self.actor_combobox.setFixedWidth(120)
        self.actor_combobox.setVisible(False)
        self.actor_checkbox.stateChanged.connect(lambda state: self.actor_combobox.setVisible(state == Qt.CheckState.Checked))

        actor_layout = QHBoxLayout()
        actor_layout.addWidget(QLabel("Actor:"))
        actor_layout.addWidget(self.actor_combobox)
        actor_layout.addWidget(self.actor_checkbox)

        limit_layout = QHBoxLayout()
        self.number_input = QSpinBox()
        self.number_input.setRange(0, 10000)
        self.number_input.setValue(0)
        limit_layout.addWidget(QLabel("Max Events:"))
        limit_layout.addWidget(self.number_input)

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

        filter_layout.addLayout(verb_layout)
        filter_layout.addLayout(actor_layout)
        filter_layout.addLayout(limit_layout)
        filter_layout.addWidget(self.filter_button)
        self.layout.addWidget(self.filter_group)

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
            if value.startswith("mailto:"):
                return value.replace("mailto:", "")
            elif value.startswith("http"):
                return value.split("/")[-1]
        return str(value)

    def updateTable(self):
        data = self.download_button.json_data
        if not data:
            self.table.setRowCount(0)
            return

        events = sum(data, []) if isinstance(data[0], list) else data
        events = self.convert_to_duration(events)

        self.main_app.processed_dataframe = pd.DataFrame(events)  # Store for reuse in Inspect

        verbs = sorted(set(self.extract_name(e.get("verb", {}).get("id", "")) for e in events))
        self.verb_combobox.clear()
        self.verb_combobox.addItems(verbs)

        actors = sorted(set(self.extract_name(e.get("actor", {}).get("mbox", "")) for e in events))
        self.actor_combobox.clear()
        self.actor_combobox.addItems(actors)

        self.afficher_tableau(events)

    def appliquer_filtre(self):
        data = self.download_button.json_data
        if not data:
            QMessageBox.warning(self, "Error", "No data loaded.")
            return

        events = sum(data, []) if isinstance(data[0], list) else data

        selected_actor = self.actor_combobox.currentText() if self.actor_checkbox.isChecked() else ""
        selected_verb = self.verb_combobox.currentText() if self.verb_checkbox.isChecked() else ""
        max_events = self.number_input.value()

        filtered = [e for e in events if
                    (not selected_actor or self.extract_name(e.get("actor", {}).get("mbox", "")).lower() == selected_actor.lower()) and
                    (not selected_verb or self.extract_name(e.get("verb", {}).get("id", "")).lower() == selected_verb.lower())]

        if not filtered:
            QMessageBox.warning(self, "No Events", "No events found for the selected filters.")
            return

        self.afficher_tableau(filtered[:max_events] if max_events > 0 else filtered)

    def afficher_tableau(self, events):
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            duration = event.get("Duration", 0)
            duration = f"{float(duration):.2f}" if isinstance(duration, (int, float)) else "0.00"

            items = [
                QTableWidgetItem(duration),
                QTableWidgetItem(self.extract_name(event.get("actor", {}).get("mbox", ""))),
                QTableWidgetItem(self.extract_name(event.get("verb", {}).get("id", ""))),
                QTableWidgetItem(self.extract_name(event.get("object", {}).get("id", "")))
            ]

            for col, item in enumerate(items):
                self.table.setItem(row, col, item)
                if row % 2 == 0:
                    item.setBackground(QColor("#E5E9F2"))

    def convert_to_duration(self, events):
        try:
            df = pd.DataFrame(events)

            if 'timestamp' not in df:
                return events

            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['actor_name'] = df['actor'].apply(lambda a: self.extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a))

            df = df.sort_values(by=['actor_name', 'timestamp'])
            df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds().fillna(0)

            for i, d in enumerate(df['Duration']):
                events[i]['Duration'] = float(d)
        except Exception:
            pass

        return events
