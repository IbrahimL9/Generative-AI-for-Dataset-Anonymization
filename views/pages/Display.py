from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont, QColor
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
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Section des filtres
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

        # Filtre par verbe
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

        # Filtre par acteur
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

        # Limite des événements
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Max Events:")
        self.number_input = QSpinBox()
        self.number_input.setMinimum(0)
        self.number_input.setMaximum(1000)
        self.number_input.setValue(0)

        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.number_input)

        # Bouton de filtre
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

        # Ajout des éléments au layout des filtres
        filter_layout.addLayout(verb_layout)
        filter_layout.addLayout(actor_layout)
        filter_layout.addLayout(limit_layout)
        filter_layout.addWidget(self.filter_button)

        self.layout.addWidget(self.filter_group)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Actor", "Verb", "Object"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Appliquer un style CSS amélioré
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
        """ Extrait uniquement le nom utile d'un lien ou d'une adresse email """
        if "mailto:" in value:
            return value.replace("mailto:", "")
        elif value.startswith("http"):
            return value.split("/")[-1]
        return value

    def updateTable(self):
        """ Met à jour le tableau avec les données JSON fusionnées """
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            # Si le premier élément est lui-même une liste, on itère sur des batches
            if isinstance(self.download_button.json_data, list) and len(
                    self.download_button.json_data) > 0 and isinstance(self.download_button.json_data[0], list):
                all_events = []
                for batch in self.download_button.json_data:
                    all_events.extend(batch)
            else:
                # Sinon, c'est déjà une liste d'événements
                all_events = self.download_button.json_data

            self.afficher_tableau(all_events)

            # Mise à jour des filtres
            verbs = list(set(self.extract_name(event["verb"]["id"]) for event in all_events if "verb" in event))
            self.verb_combobox.clear()
            self.verb_combobox.addItems(verbs)

            actors = list(set(self.extract_name(event["actor"]["mbox"]) for event in all_events if "actor" in event))
            self.actor_combobox.clear()
            self.actor_combobox.addItems(actors)
        else:
            self.table.setRowCount(0)

    def toggle_verb_combobox(self, checked):
        self.verb_combobox.setVisible(checked)

    def toggle_actor_combobox(self, checked):
        self.actor_combobox.setVisible(checked)

    def appliquer_filtre(self):
        """ Applique les filtres sélectionnés """
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            all_events = []
            for batch in self.download_button.json_data:
                all_events.extend(batch)

            filtered_events = all_events

            if self.verb_checkbox.isChecked():
                selected_verb = self.verb_combobox.currentText()
                filtered_events = [event for event in filtered_events if self.extract_name(event.get("verb", {}).get("id", "")) == selected_verb]

            if self.actor_checkbox.isChecked():
                selected_actor = self.actor_combobox.currentText()
                filtered_events = [event for event in filtered_events if self.extract_name(event.get("actor", {}).get("mbox", "")) == selected_actor]

            max_events = self.number_input.value()
            if max_events != 0:
                filtered_events = filtered_events[:max_events]

            self.afficher_tableau(filtered_events)

    def afficher_tableau(self, events):
        """ Affiche les données dans le tableau """
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.table.setItem(row, 0, QTableWidgetItem(event.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(self.extract_name(event.get("actor", {}).get("mbox", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(self.extract_name(event.get("verb", {}).get("id", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(self.extract_name(event.get("object", {}).get("id", ""))))

            if row % 2 == 0:
                for col in range(4):
                    self.table.item(row, col).setBackground(QColor("#E5E9F2"))
