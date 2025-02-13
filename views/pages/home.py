import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolButton, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QComboBox, QSpinBox, QGroupBox, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from collections import Counter
from datetime import datetime

class HomePage(QWidget):
    fileDownloaded = pyqtSignal()

    def __init__(self, download_button):
        super().__init__()
        # Utiliser l'instance partagée passée en paramètre
        self.download_button = download_button
        self.json_data = None

        self.initUI()

        # Créer un timer qui vérifie périodiquement si un fichier a été téléchargé.
        self.checkTimer = QTimer(self)
        self.checkTimer.timeout.connect(self.updateViewButtonState)
        self.checkTimer.start(500)

    def initUI(self):
        layout = QVBoxLayout()

        layout.addSpacing(30)

        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Utiliser directement l'instance de DownloadButton passée au constructeur
        button_layout.addWidget(self.download_button)

        button_layout.addSpacing(10)

        self.view_button = QToolButton()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        eye_icon_path = os.path.join(current_dir, "..", "eye.png")
        self.view_button.setIcon(QIcon(eye_icon_path))
        self.view_button.setIconSize(QSize(32, 32))
        self.view_button.setStyleSheet("QToolButton { border: none; }")
        self.view_button.setToolTip("View generated file")
        self.view_button.clicked.connect(self.view_generated_file)
        button_layout.addWidget(self.view_button)

        button_layout.addSpacing(10)

        self.stats_button = QToolButton()
        stats_icon_path = os.path.join(current_dir, "..", "statistiques.png")
        self.stats_button.setIcon(QIcon(stats_icon_path))
        self.stats_button.setIconSize(QSize(32, 32))
        self.stats_button.setStyleSheet("QToolButton { border: none; }")
        self.stats_button.setToolTip("View file statistics")
        self.stats_button.clicked.connect(self.view_statistics)
        button_layout.addWidget(self.stats_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch(2)

        # Ajouter un layout central pour afficher le tableau et les statistiques
        self.central_layout = QVBoxLayout()
        layout.addLayout(self.central_layout)

        # Conteneur pour les statistiques
        self.stats_container = QGroupBox()
        self.stats_container_layout = QVBoxLayout()
        self.stats_container.setLayout(self.stats_container_layout)
        self.central_layout.addWidget(self.stats_container)
        self.stats_container.setVisible(False)  # Masquer par défaut
        self.stats_container.setStyleSheet("")
        self.setLayout(layout)

        # Désactiver par défaut les boutons afficher stats et data
        self.view_button.setEnabled(False)
        self.stats_button.setEnabled(False)

    def updateViewButtonState(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            self.view_button.setEnabled(True)
            self.stats_button.setEnabled(True)
            self.checkTimer.stop()
            self.fileDownloaded.emit()  # Signaler que le fichier est téléchargé
        else:
            self.view_button.setEnabled(False)
            self.stats_button.setEnabled(False)

    ######### VIEW DATA ##########
    def view_generated_file(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            events = self.download_button.json_data.get("events", [])

            # Création d'une nouvelle fenêtre de dialogue pour afficher le tableau
            table_dialog = QDialog(self)
            table_dialog.setWindowTitle("Generated File")
            table_dialog.resize(800, 600)
            table_layout = QVBoxLayout(table_dialog)

            # -- SECTION DE FILTRE SOUS FORME DE "MENU" HORIZONTAL --
            filter_group = QGroupBox("Filters")
            filter_group.setStyleSheet("border: 2px solid #000; padding: 10px;")
            filter_group_layout = QHBoxLayout()
            filter_group.setLayout(filter_group_layout)

            # Checkbox pour le filtre sur le verbe
            self.verb_checkbox = QCheckBox("Filter by Verb")
            self.verb_checkbox.setStyleSheet("border: 2px solid  #000; padding: 10px;")
            self.verb_checkbox.stateChanged.connect(self.toggle_verb_combobox)
            filter_group_layout.addWidget(self.verb_checkbox)

            # Combobox pour sélectionner le verbe
            self.verb_combobox = QComboBox()
            self.verb_combobox.setVisible(False)
            self.verb_combobox.setStyleSheet("border: 2px solid #000; padding: 5px;")
            filter_group_layout.addWidget(QLabel("Verb:"))
            filter_group_layout.addWidget(self.verb_combobox)

            # Checkbox pour le filtre sur l'acteur
            self.actor_checkbox = QCheckBox("Filter by Actor")
            self.actor_checkbox.setStyleSheet("border: 2px solid #000; padding: 5px;")
            self.actor_checkbox.stateChanged.connect(self.toggle_actor_combobox)
            filter_group_layout.addWidget(self.actor_checkbox)

            # Combobox pour sélectionner l'acteur
            self.actor_combobox = QComboBox()
            self.actor_combobox.setVisible(False)
            self.actor_combobox.setStyleSheet("border: 2px solid #000; padding: 5px;")
            filter_group_layout.addWidget(QLabel("Actor:"))
            filter_group_layout.addWidget(self.actor_combobox)

            # SpinBox pour limiter le nombre d'événements
            filter_group_layout.addWidget(QLabel("Max Events:"))
            self.number_input = QSpinBox()
            self.number_input.setMinimum(0)
            self.number_input.setMaximum(1000)
            self.number_input.setValue(0)
            self.number_input.setStyleSheet("border: 2px solid #000; padding: 5px;")
            filter_group_layout.addWidget(self.number_input)

            # Bouton pour appliquer le filtre
            filter_button = QPushButton("Apply Filter")
            filter_button.setStyleSheet("border: 2px solid #000; padding: 5px;")
            filter_button.clicked.connect(self.appliquer_filtre)
            filter_group_layout.addWidget(filter_button)

            table_layout.addWidget(filter_group)

            # Création et remplissage du QTableWidget
            self.table = QTableWidget()
            self.table.setRowCount(len(events))
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Timestamp", "Actor", "Verb", "Object"])
            self.table.setStyleSheet("border: 2px solid #000;")
            for row, event in enumerate(events):
                self.table.setItem(row, 0, QTableWidgetItem(event.get("timestamp", "")))
                self.table.setItem(row, 1, QTableWidgetItem(event.get("actor", "")))
                self.table.setItem(row, 2, QTableWidgetItem(event.get("verb", "")))
                self.table.setItem(row, 3, QTableWidgetItem(event.get("object", "")))

            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.setStyleSheet("QTableWidget { font-size: 14px; border: 2px solid #000; }")
            table_layout.addWidget(self.table)

            table_dialog.exec()
        else:
            dialog = QDialog(self)
            dialog.setWindowTitle("No Data Available")
            dialog_layout = QVBoxLayout(dialog)
            message = QLabel("No generated file available. Please download a file first.")
            message.setStyleSheet("border: 2px solid #000; padding: 10px;")
            dialog_layout.addWidget(message)
            dialog.exec()

    def toggle_verb_combobox(self, checked):
        if checked:
            verbs = list(
                set(event.get("verb")
                    for event in self.download_button.json_data["events"]
                    if event.get("verb"))
            )
            self.verb_combobox.clear()
            self.verb_combobox.addItems(verbs)
            self.verb_combobox.setVisible(True)
        else:
            self.verb_combobox.setVisible(False)

    def toggle_actor_combobox(self, checked):
        if checked:
            actors = list(
                set(event.get("actor")
                    for event in self.download_button.json_data["events"]
                    if event.get("actor"))
            )
            self.actor_combobox.clear()
            self.actor_combobox.addItems(actors)
            self.actor_combobox.setVisible(True)
        else:
            self.actor_combobox.setVisible(False)

    def appliquer_filtre(self):
        events = self.download_button.json_data.get("events", [])
        filtered_events = events  # On commence avec tous les événements

        # Récupérer les cases à cocher et les valeurs
        verb_filter = self.verb_checkbox.isChecked()
        actor_filter = self.actor_checkbox.isChecked()
        max_events = self.number_input.value()  # Valeur modifiée par l'utilisateur

        # Appliquer les filtres sur le verb et actor
        if verb_filter:
            selected_verb = self.verb_combobox.currentText()
            filtered_events = [event for event in filtered_events if event.get("verb") == selected_verb]

        if actor_filter:
            selected_actor = self.actor_combobox.currentText()
            filtered_events = [event for event in filtered_events if event.get("actor") == selected_actor]

        # Limiter le nombre d'événements si max_events != 0
        if max_events != 0:
            filtered_events = filtered_events[:max_events]

        # Affichage des événements filtrés
        self.afficher_tableau(filtered_events)

    def afficher_tableau(self, events):
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.table.setItem(row, 0, QTableWidgetItem(event.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(event.get("actor", "")))
            self.table.setItem(row, 2, QTableWidgetItem(event.get("verb", "")))
            self.table.setItem(row, 3, QTableWidgetItem(event.get("object", "")))

    ######### VIEW STATS ##########
    def view_statistics(self):
        try:
            if self.stats_container.isVisible():
                self.stats_container.setVisible(False)
                return

            if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
                data = self.download_button.json_data
                events = data.get("events", [])

                if not events:
                    self.clear_stats_container()
                    message = QLabel("Aucun événement disponible pour afficher les statistiques.")
                    self.stats_container_layout.addWidget(message)
                    self.stats_container.setVisible(True)
                    return

                # Extraction des données clés
                unique_actors = set(event["actor"] for event in events)
                unique_verbs = set(event["verb"] for event in events)
                unique_objects = set(event["object"] for event in events)

                total_events = len(events)
                num_actors = len(unique_actors)
                num_verbs = len(unique_verbs)
                num_objects = len(unique_objects)

                # Comptage des événements par acteur et par verbe
                actor_counts = Counter(event["actor"] for event in events)
                verb_counts = Counter(event["verb"] for event in events)

                avg_events_per_actor = total_events / num_actors if num_actors > 0 else 0
                min_events_per_actor = min(actor_counts.values()) if actor_counts else 0
                max_events_per_actor = max(actor_counts.values()) if actor_counts else 0

                avg_events_per_verb = total_events / num_verbs if num_verbs > 0 else 0
                min_events_per_verb = min(verb_counts.values()) if verb_counts else 0
                max_events_per_verb = max(verb_counts.values()) if verb_counts else 0

                # Analyse des timestamps
                timestamps = [datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%S") for event in events]
                timestamps.sort()
                first_event = timestamps[0].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"
                last_event = timestamps[-1].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"

                # Effacer les anciennes statistiques
                self.clear_stats_container()

                # Supprimer la bordure du conteneur et ajuster les marges
                self.stats_container.setStyleSheet("border: none; padding: 5px;")
                self.stats_container_layout.setContentsMargins(10, 5, 10, 5)

                # Titre principal
                title_label = QLabel("STATISTICS")
                title_label.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                title_label.setStyleSheet("color: black; margin-bottom: 5px;")

                # Statistiques générales
                general_stats_text = QLabel(
                    f"🔹 **Total Events:** {total_events}\n"
                    f"🔹 **Unique Actors:** {num_actors}\n"
                    f"🔹 **Unique Verbs:** {num_verbs}\n"
                    f"🔹 **Unique Objects:** {num_objects}\n\n"
                    f"🕒 **Time Analysis:**\n"
                    f"   - First Event: {first_event}\n"
                    f"   - Last Event: {last_event}"
                )
                general_stats_text.setWordWrap(True)
                general_stats_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
                general_stats_text.setStyleSheet("font-size: 14px; color: black;")

                # Statistiques détaillées
                detailed_stats_text = QLabel(
                    f"📌 **Events per Actor:**\n"
                    f"   - Average: {avg_events_per_actor:.2f}\n"
                    f"   - Min: {min_events_per_actor}\n"
                    f"   - Max: {max_events_per_actor}\n\n"
                    f"📌 **Events per Verb:**\n"
                    f"   - Average: {avg_events_per_verb:.2f}\n"
                    f"   - Min: {min_events_per_verb}\n"
                    f"   - Max: {max_events_per_verb}"
                )
                detailed_stats_text.setWordWrap(True)
                detailed_stats_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                detailed_stats_text.setStyleSheet("font-size: 14px; color: black;")

                # Layout horizontal pour séparer les stats
                stats_layout = QHBoxLayout()

                # Layout de gauche (détails)
                left_layout = QVBoxLayout()
                left_layout.addWidget(detailed_stats_text)
                left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Layout de droite (général)
                right_layout = QVBoxLayout()
                right_layout.addWidget(general_stats_text)
                right_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                stats_layout.addLayout(left_layout, 1)
                stats_layout.addSpacing(20)
                stats_layout.addLayout(right_layout, 1)

                # Espacement en bas
                bottom_spacer = QSpacerItem(160, 160, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

                # Ajout au layout principal
                self.stats_container_layout.addWidget(title_label)
                self.stats_container_layout.addLayout(stats_layout)
                self.stats_container_layout.addSpacerItem(bottom_spacer)
                self.stats_container.setVisible(True)

            else:
                self.clear_stats_container()
                message = QLabel("Aucun fichier généré. Veuillez télécharger un fichier d'abord.")
                message.setAlignment(Qt.AlignmentFlag.AlignLeft)
                message.setStyleSheet("font-size: 14px; color: black;")
                self.stats_container_layout.addWidget(message)
                self.stats_container.setVisible(True)

        except Exception as e:
            print(f"Erreur dans view_statistics: {e}")

    def clear_stats_container(self):
        # Effacer tous les widgets précédents du conteneur de statistiques.
        while self.stats_container_layout.count():
            item = self.stats_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
