from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class Display(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Titre de la page
        title = QLabel("Display Generated Data")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Section de filtres
        self.filter_group = QGroupBox("Filters")
        self.filter_group.setStyleSheet("border: 2px solid #000; padding: 10px;")
        filter_layout = QHBoxLayout()
        self.filter_group.setLayout(filter_layout)

        # Filtre par verbe
        self.verb_checkbox = QCheckBox("Filter by Verb")
        self.verb_checkbox.setStyleSheet("border: 2px solid #000; padding: 10px;")
        self.verb_checkbox.stateChanged.connect(self.toggle_verb_combobox)
        filter_layout.addWidget(self.verb_checkbox)

        self.verb_combobox = QComboBox()
        self.verb_combobox.setVisible(False)
        self.verb_combobox.setStyleSheet("border: 2px solid #000; padding: 5px;")
        filter_layout.addWidget(QLabel("Verb:"))
        filter_layout.addWidget(self.verb_combobox)

        # Filtre par acteur
        self.actor_checkbox = QCheckBox("Filter by Actor")
        self.actor_checkbox.setStyleSheet("border: 2px solid #000; padding: 5px;")
        self.actor_checkbox.stateChanged.connect(self.toggle_actor_combobox)
        filter_layout.addWidget(self.actor_checkbox)

        self.actor_combobox = QComboBox()
        self.actor_combobox.setVisible(False)
        self.actor_combobox.setStyleSheet("border: 2px solid #000; padding: 5px;")
        filter_layout.addWidget(QLabel("Actor:"))
        filter_layout.addWidget(self.actor_combobox)

        # Limiter le nombre d'événements
        filter_layout.addWidget(QLabel("Max Events:"))
        self.number_input = QSpinBox()
        self.number_input.setMinimum(0)
        self.number_input.setMaximum(1000)
        self.number_input.setValue(0)
        self.number_input.setStyleSheet("border: 2px solid #000; padding: 5px;")
        filter_layout.addWidget(self.number_input)

        # Bouton pour appliquer le filtre
        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.setStyleSheet("border: 2px solid #000; padding: 5px;")
        self.filter_button.clicked.connect(self.appliquer_filtre)
        filter_layout.addWidget(self.filter_button)

        self.layout.addWidget(self.filter_group)

        # Tableau pour afficher les données
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Actor", "Verb", "Object"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget { font-size: 14px; border: 2px solid #000; }")
        self.layout.addWidget(self.table)

        # Appel initial (peut rester vide si les données ne sont pas encore disponibles)
        self.updateTable()

    def showEvent(self, event):
        # Chaque fois que la page Display devient visible, on met à jour le tableau.
        self.updateTable()
        super().showEvent(event)

    def updateTable(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            events = self.download_button.json_data.get("events", [])
            self.table.setRowCount(len(events))
            for row, event in enumerate(events):
                self.table.setItem(row, 0, QTableWidgetItem(event.get("timestamp", "")))
                self.table.setItem(row, 1, QTableWidgetItem(event.get("actor", "")))
                self.table.setItem(row, 2, QTableWidgetItem(event.get("verb", "")))
                self.table.setItem(row, 3, QTableWidgetItem(event.get("object", "")))
            # Mise à jour des options de filtrage
            verbs = list(set(event.get("verb") for event in events if event.get("verb")))
            self.verb_combobox.clear()
            self.verb_combobox.addItems(verbs)
            actors = list(set(event.get("actor") for event in events if event.get("actor")))
            self.actor_combobox.clear()
            self.actor_combobox.addItems(actors)
        else:
            self.table.setRowCount(0)

    def toggle_verb_combobox(self, checked):
        self.verb_combobox.setVisible(checked)

    def toggle_actor_combobox(self, checked):
        self.actor_combobox.setVisible(checked)

    def appliquer_filtre(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            events = self.download_button.json_data.get("events", [])
            filtered_events = events

            if self.verb_checkbox.isChecked():
                selected_verb = self.verb_combobox.currentText()
                filtered_events = [event for event in filtered_events if event.get("verb") == selected_verb]

            if self.actor_checkbox.isChecked():
                selected_actor = self.actor_combobox.currentText()
                filtered_events = [event for event in filtered_events if event.get("actor") == selected_actor]

            max_events = self.number_input.value()
            if max_events != 0:
                filtered_events = filtered_events[:max_events]

            self.afficher_tableau(filtered_events)

    def afficher_tableau(self, events):
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.table.setItem(row, 0, QTableWidgetItem(event.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(event.get("actor", "")))
            self.table.setItem(row, 2, QTableWidgetItem(event.get("verb", "")))
            self.table.setItem(row, 3, QTableWidgetItem(event.get("object", "")))
