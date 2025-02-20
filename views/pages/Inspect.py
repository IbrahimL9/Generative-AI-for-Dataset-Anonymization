from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from statistics import mean, stdev

class Inspect(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.initUI()
        self.download_button.file_loaded.connect(self.updateStatistics)

    def initUI(self):
        # Layout principal
        self.layout = QVBoxLayout()

        # Titre principal
        title = QLabel("STATISTICS")
        title.setFont(QFont("Montserrat", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Widget pour contenir les graphiques
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # Layout pour organiser les graphiques
        self.graph_layout = QVBoxLayout()

        # Layout pour aligner les trois petits graphiques côte à côte
        self.bottom_graph_layout = QHBoxLayout()

        # Ajouter les layouts dans le principal
        self.scroll_layout.addLayout(self.graph_layout)
        self.scroll_layout.addLayout(self.bottom_graph_layout)

        # QScrollArea pour permettre le défilement
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)

        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

        self.updateStatistics()

    def updateStatistics(self):
        # Nettoyer les anciens graphiques
        self.clearStatistics()

        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            data = self.download_button.json_data
            events = data.get("events", [])
            if not events:
                return

            # Extraction des statistiques
            total_events = len(events)
            unique_actors = set(event.get("actor") for event in events)
            unique_verbs = set(event.get("verb") for event in events)
            unique_objects = set(event.get("object") for event in events)
            num_actors = len(unique_actors)
            num_verbs = len(unique_verbs)
            num_objects = len(unique_objects)

            actor_counts = Counter(event.get("actor") for event in events)
            verb_counts = Counter(event.get("verb") for event in events)

            min_events_per_actor = min(actor_counts.values(), default=0)
            max_events_per_actor = max(actor_counts.values(), default=0)
            avg_events_per_actor = total_events / num_actors if num_actors > 0 else 0

            min_events_per_verb = min(verb_counts.values(), default=0)
            max_events_per_verb = max(verb_counts.values(), default=0)
            avg_events_per_verb = total_events / num_verbs if num_verbs > 0 else 0

            # Calculer l'écart type
            std_events_per_actor = stdev(list(actor_counts.values()))

            # Extraction des horodatages
            timestamps = [datetime.strptime(event.get("timestamp"), "%Y-%m-%dT%H:%M:%S") for event in events if event.get("timestamp")]
            first_event = timestamps[0].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"
            last_event = timestamps[-1].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"

            # Graphique principal en haut
            overview_chart = self.create_bar_chart({
                "Total Events": total_events,
                "Unique Actors": num_actors,
                "Unique Verbs": num_verbs,
                "Unique Objects": num_objects
            }, "Statistics Overview")

            # Nouvel histogramme pour les horodatages
            event_time_chart = self.create_event_time_chart(first_event, last_event)

            # Layout pour aligner les deux graphiques côte à côte en haut
            top_graph_layout = QHBoxLayout()
            top_graph_layout.addWidget(overview_chart)
            top_graph_layout.addWidget(event_time_chart)

            # Graphiques en bas
            actor_chart = self.create_histogram(avg_events_per_actor, min_events_per_actor, max_events_per_actor, "Events per Actor")
            verb_chart = self.create_histogram(avg_events_per_verb, min_events_per_verb, max_events_per_verb, "Events per Verb")

            # Graphique en barres pour la moyenne et l'écart type
            statistics_bar_chart = self.create_statistics_bar_chart(avg_events_per_actor, std_events_per_actor)

            # Ajouter les layouts dans le principal
            self.graph_layout.addLayout(top_graph_layout)
            self.bottom_graph_layout.addWidget(actor_chart)
            self.bottom_graph_layout.addWidget(verb_chart)
            self.bottom_graph_layout.addWidget(statistics_bar_chart)

    def clearStatistics(self):
        """ Supprime les anciens graphiques pour éviter les doublons. """
        for layout in [self.graph_layout, self.bottom_graph_layout]:
            while layout.count():
                widget = layout.takeAt(0).widget()
                if widget:
                    widget.setParent(None)

    def create_bar_chart(self, data, title):
        """ Crée un graphique en barres. """
        labels = list(data.keys())
        values = [float(value) if isinstance(value, (int, float)) else 0 for value in data.values()]
        colors = ['skyblue', 'orange', 'green', 'red', 'purple', 'brown']

        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color=colors)

        ax.set_title(title, fontsize=12)
        ax.set_ylabel("Count", fontsize=10)
        ax.tick_params(axis='x', labelsize=9)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(450, 300)  # taille de celui en haut
        return canvas

    def create_histogram(self, avg_value, min_value, max_value, title):
        """ Crée un histogramme avec trois valeurs : moyenne, min, max. """
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        colors = ['skyblue', 'orange', 'green']

        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(labels, values, color=colors)

        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Number of Events", fontsize=9)
        ax.tick_params(axis='x', labelsize=8)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval:.2f}', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(450, 300)  # taille des 2 en bas
        return canvas

    def create_event_time_chart(self, first_event, last_event):
        """ Crée un histogramme pour les horodatages. """
        labels = ["First Event", "Last Event"]
        values = [1, 1]  # Juste pour afficher les étiquettes
        colors = ['lightblue', 'lightgreen']

        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(labels, values, color=colors)

        ax.set_title("Event Timestamps", fontsize=10)
        ax.set_ylabel("Occurrence", fontsize=9)
        ax.tick_params(axis='x', labelsize=8)

        # Ajouter les horodatages comme texte sur les barres
        ax.text(bars[0].get_x() + bars[0].get_width()/2, 0.5, first_event, ha='center', va='bottom', fontsize=8)
        ax.text(bars[1].get_x() + bars[1].get_width()/2, 0.5, last_event, ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(450, 300)  # taille des 2 en bas
        return canvas

    def create_statistics_bar_chart(self, avg_value, std_value):
        """ Crée un graphique en barres pour la moyenne et l'écart type. """
        labels = ["Average", "Standard Deviation"]
        values = [avg_value, std_value]
        colors = ['skyblue', 'orange']

        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(labels, values, color=colors)

        ax.set_title("Average and Standard Deviation of Events per Actor", fontsize=10)
        ax.set_ylabel("Value", fontsize=9)
        ax.tick_params(axis='x', labelsize=8)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval:.2f}', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(450, 300)  # taille des 2 en bas
        return canvas