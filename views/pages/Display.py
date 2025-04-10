from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os


def extract_name(value):
    """Fonction utilitaire pour extraire un nom lisible depuis une URL ou un mailto."""
    if isinstance(value, str):
        if value.startswith("mailto:"):
            return value.replace("mailto:", "")
        elif value.startswith("http"):
            return value.split("/")[-1]
    return str(value)


class UpdateWorker(QObject):

    finished = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, data):
        super().__init__()
        self.data = data

    @pyqtSlot()
    def run(self):
        try:
            events = sum(self.data, []) if isinstance(self.data[0], list) else self.data

            # Conversion en DataFrame
            df = pd.DataFrame(events)
            if 'timestamp' not in df.columns:
                # On renvoie les données sans modification si on ne trouve pas la colonne
                self.finished.emit(events, df)
                return

            # Convertir les timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # Extraire le nom de l'acteur
            df['actor_name'] = df['actor'].apply(lambda a: extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a))
            # Trier par acteur et timestamp
            df = df.sort_values(by=['actor_name', 'timestamp'])
            session_gap = 300      # 5 minutes
            estimated_duration = 60  # Durée par défaut

            # Calcul vectorisé de la différence de temps par acteur
            df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds()
            # Pour le premier événement de chaque groupe, diff() renvoie NaN : on le remplace
            df['Duration'] = df['Duration'].fillna(estimated_duration)
            # Si la différence dépasse le seuil, on affecte la durée par défaut
            df.loc[df['Duration'] > session_gap, 'Duration'] = estimated_duration
            # Pour le dernier événement de chaque groupe, forcer la durée estimée
            last_indices = df.groupby('actor_name').tail(1).index
            df.loc[last_indices, 'Duration'] = estimated_duration

            # Mise à jour de la liste events avec les durées calculées
            for i, d in enumerate(df['Duration']):
                events[i]['Duration'] = float(d)

            self.finished.emit(events, df)
        except Exception as e:
            self.error.emit(str(e))


class Display(QWidget):
    def __init__(self, download_button, main_app):
        super().__init__()
        self.download_button = download_button
        self.main_app = main_app
        self.loading_label = None  # Pour afficher le message de chargement
        self.thread = None         # Référence au thread pour le worker
        self.worker = None
        self.table_already_loaded = False
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("Display Generated Data")
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Groupe de filtres
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

        # Configuration du filtre "Verb"
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

        # Configuration du filtre "Actor"
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

        # Filtre sur le nombre maximal d'événements
        limit_layout = QHBoxLayout()
        self.number_input = QSpinBox()
        self.number_input.setRange(0, 10000)
        self.number_input.setValue(0)
        limit_layout.addWidget(QLabel("Max Events:"))
        limit_layout.addWidget(self.number_input)

        # Bouton d'application du filtre
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

        # Table d'affichage
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Duration (s)", "Actor", "Verb", "Object"])
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
        super().showEvent(event)
        if not self.table_already_loaded:
            self.updateTable()
            self.table_already_loaded = True

    def extract_name(self, value):
        return extract_name(value)

    def toggle_verb_combobox(self, checked):
        self.verb_combobox.setVisible(checked)

    def toggle_actor_combobox(self, checked):
        self.actor_combobox.setVisible(checked)

    def updateTable(self):
        data = self.download_button.json_data
        if not data:
            self.table.setRowCount(0)
            return

        # Affichage d'un indicateur de chargement
        self.showLoadingIndicator()

        # Démarrage de la mise à jour en arrière-plan via un worker
        self.thread = QThread()
        self.worker = UpdateWorker(data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_update_finished)
        self.worker.error.connect(self.on_update_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.start()

    def on_update_finished(self, events, df):
        # Stocke le DataFrame pour une réutilisation ultérieure
        self.main_app.processed_dataframe = df

        # Mise à jour des combobox pour les filtres
        verbs = sorted(set(self.extract_name(e.get("verb", {}).get("id", "")) for e in events))
        self.verb_combobox.clear()
        self.verb_combobox.addItems(verbs)

        actors = sorted(set(self.extract_name(e.get("actor", {}).get("mbox", "")) for e in events))
        self.actor_combobox.clear()
        self.actor_combobox.addItems(actors)

        # Remplissage de la table
        self.afficher_tableau(events)

        # Masquer l'indicateur de chargement
        self.hideLoadingIndicator()

    def on_update_error(self, err_msg):
        print(f"[Display] update error: {err_msg}")
        self.hideLoadingIndicator()

    def showLoadingIndicator(self):
        if not hasattr(self, "loading_label") or self.loading_label is None:
            txt = "<b>Loading data, please wait...</b>"
            self.loading_label = QLabel(txt, self)
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # On insère ce label en haut du layout
            self.layout.insertWidget(3, self.loading_label)
        self.loading_label.show()

    def hideLoadingIndicator(self):
        if hasattr(self, "loading_label") and self.loading_label is not None:
            self.loading_label.hide()

    def afficher_tableau(self, events):
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            # Traitement du timestamp
            ts_raw = event.get("timestamp", "")
            try:
                dt = pd.to_datetime(ts_raw)
                ts_seconds = dt.timestamp()
                ts_str = str(int(ts_seconds))
            except Exception:
                ts_str = "N/A"

            # Traitement de la durée
            duration = event.get("Duration", 0)
            try:
                duration_str = str(int(float(duration)))
            except Exception:
                duration_str = "0"

            items = [
                QTableWidgetItem(ts_str),
                QTableWidgetItem(duration_str),
                QTableWidgetItem(self.extract_name(event.get("actor", {}).get("mbox", ""))),
                QTableWidgetItem(self.extract_name(event.get("verb", {}).get("id", ""))),
                QTableWidgetItem(self.extract_name(event.get("object", {}).get("id", "")))
            ]
            for col, item in enumerate(items):
                self.table.setItem(row, col, item)
                if row % 2 == 0:
                    item.setBackground(QColor("#E5E9F2"))

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

    def convert_to_duration(self, events):
        """
        Méthode synchronisée utilisée lors de la mise à jour en mode asynchrone.
        Cette méthode n'est plus appelée directement depuis updateTable, mais elle est
        utilisée dans la classe Worker pour le traitement vectorisé.
        """
        try:
            df = pd.DataFrame(events)
            if 'timestamp' not in df:
                return events

            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['actor_name'] = df['actor'].apply(lambda a: self.extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a))
            df = df.sort_values(by=['actor_name', 'timestamp'])
            session_gap = 300  # 5 minutes
            estimated_duration = 60  # valeur par défaut

            df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds().fillna(estimated_duration)
            df.loc[df['Duration'] > session_gap, 'Duration'] = estimated_duration
            last_indices = df.groupby('actor_name').tail(1).index
            df.loc[last_indices, 'Duration'] = estimated_duration

            for i, d in enumerate(df['Duration']):
                events[i]['Duration'] = float(d)
        except Exception as e:
            print(f"[ERROR convert_to_duration] {e}")
        return events

    # --- Fonctions de création des graphiques Plotly ---
    def create_bar_chart(self, data, title, y_axis="Count"):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Category", "y": y_axis},
            title=title,
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title,
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B', '#00CC96']
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_event_time_chart(self, first_event, last_event):
        labels = ["First Event", "Last Event"]
        values = [1, 1]
        fig = px.bar(
            x=labels,
            y=values,
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Timestamp"},
            title="Event Timestamps",
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B']
        fig.update_traces(marker_color=colors[:len(labels)], textposition="outside")
        fig.update_layout(showlegend=False)
        return fig

    def create_statistics_bar_chart(self, avg_value, std_value):
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Stats", "y": "Value"},
            title="Average & Std Dev of Events per Actor",
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B']
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_actor_pie_chart(self, actor_counts):
        labels = list(actor_counts.keys())
        sizes = list(actor_counts.values())
        fig = px.pie(
            names=labels,
            values=sizes,
            title="Actor Distribution",
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig.update_traces(marker_colors=colors[:len(labels)])
        return fig

    def create_object_pie_chart(self, object_counts):
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())
        fig = px.pie(
            names=labels,
            values=sizes,
            title="Object Distribution",
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig.update_traces(marker_colors=colors[:len(labels)])
        return fig
