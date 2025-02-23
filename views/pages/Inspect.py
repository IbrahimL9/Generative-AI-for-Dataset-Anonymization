from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QScrollArea, QSizePolicy
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
        """Initialisation de l'interface utilisateur"""
        self.layout = QVBoxLayout()

        # Titre principal
        title = QLabel("STATISTICS")
        title.setFont(QFont("Montserrat", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Widget pour les graphiques
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # Grille pour organiser les graphiques
        self.graph_layout = QGridLayout()
        self.graph_layout.setVerticalSpacing(50)  # Augmenter l'espacement vertical
        self.graph_layout.setHorizontalSpacing(20)  # Espacement horizontal
        self.scroll_layout.addLayout(self.graph_layout)

        # QScrollArea pour permettre le défilement
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.setLayout(self.layout)

        self.updateStatistics()

    def extract_name(self, value):
        """Extrait uniquement le nom utile d'un lien ou d'une adresse email"""
        if "mailto:" in value:
            return value.replace("mailto:", "")
        elif value.startswith("http"):
            return value.split("/")[-1]
        return value

    def updateStatistics(self):
        """Mise à jour des statistiques et affichage des graphiques"""
        if not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None:
            print("Aucune donnée JSON chargée.")
            return

        # Fusionner toutes les listes imbriquées
        data = self.download_button.json_data
        events = []
        for batch in data:
            if isinstance(batch, list):
                events.extend(batch)

        print(f"Nombre total d'événements : {len(events)}")

        if not events:
            print("Aucun événement trouvé.")
            return

        # Nettoyer les graphiques précédents
        self.clearStatistics()

        # Extraction des statistiques
        timestamps = []
        verbs = []
        actors = []
        objects = []
        events_per_actor = Counter()

        for event in events:
            timestamp = event.get("timestamp", "")
            verb = self.extract_name(event.get("verb", {}).get("id", "Unknown"))
            actor = self.extract_name(event.get("actor", {}).get("mbox", "Unknown"))
            obj = self.extract_name(event.get("object", {}).get("id", "Unknown"))

            if timestamp:
                timestamps.append(datetime.fromisoformat(timestamp))

            verbs.append(verb)
            actors.append(actor)
            objects.append(obj)
            events_per_actor[actor] += 1

        # Calcul des statistiques
        if timestamps:
            first_event = timestamps[0].strftime("%Y-%m-%d %H:%M:%S")
            last_event = timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")
        else:
            first_event = last_event = "N/A"

        verb_counts = Counter(verbs)
        # Ne garder que les 6 objets les plus utilisés
        object_counts = dict(Counter(objects).most_common(6))
        avg_events = mean(events_per_actor.values()) if events_per_actor else 0
        std_events = stdev(events_per_actor.values()) if len(events_per_actor) > 1 else 0
        min_events = min(events_per_actor.values(), default=0)
        max_events = max(events_per_actor.values(), default=0)

        # Ajout des graphiques
        self.graph_layout.addWidget(self.create_bar_chart(verb_counts, "Most Used Verbs"), 0, 0)
        self.graph_layout.addWidget(self.create_object_pie_chart(object_counts), 0, 1)
        self.graph_layout.addWidget(self.create_event_time_chart(first_event, last_event), 1, 0)
        self.graph_layout.addWidget(self.create_histogram(avg_events, min_events, max_events, "Events per Actor"), 1, 1)
        self.graph_layout.addWidget(self.create_statistics_bar_chart(avg_events, std_events), 2, 0)
        self.graph_layout.addWidget(self.create_verb_pie_chart(verb_counts), 2, 1)

    def clearStatistics(self):
        """Supprime les anciens graphiques pour éviter les doublons."""
        while self.graph_layout.count():
            widget = self.graph_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def create_bar_chart(self, data, title):
        """Crée un graphique en barres."""
        labels = list(data.keys())
        values = [data[label] for label in labels]

        fig, ax = plt.subplots(figsize=(4, 3))  # Réduire la largeur
        bars = ax.bar(labels, values, color='skyblue')

        ax.set_title(title)
        ax.set_ylabel("Count")
        ax.tick_params(axis='x', rotation=45)

        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{bar.get_height()}', ha='center')

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 250)  # Taille ajustée pour la grille
        return canvas

    def create_histogram(self, avg_value, min_value, max_value, title):
        """Crée un histogramme."""
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]

        fig, ax = plt.subplots(figsize=(4, 3))  # Réduire la largeur
        ax.bar(labels, values, color=['blue', 'red', 'green'])
        ax.set_title(title)
        ax.set_ylabel("Events per Actor")

        for i, v in enumerate(values):
            ax.text(i, v + 0.5, f"{v:.2f}", ha='center')

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 250)  # Taille ajustée pour la grille
        return canvas

    def create_event_time_chart(self, first_event, last_event):
        """Crée un graphique d'événements."""
        labels = ["First Event", "Last Event"]
        values = [1, 1]

        fig, ax = plt.subplots(figsize=(4, 3))  # Réduire la largeur
        bars = ax.bar(labels, values, color=['lightblue', 'lightgreen'])
        ax.set_title("Event Timestamps")

        ax.text(bars[0].get_x() + bars[0].get_width()/2, 0.5, first_event, ha='center')
        ax.text(bars[1].get_x() + bars[1].get_width()/2, 0.5, last_event, ha='center')

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 250)  # Taille ajustée pour la grille
        return canvas

    def create_statistics_bar_chart(self, avg_value, std_value):
        """Crée un graphique pour la moyenne et l'écart-type."""
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]

        fig, ax = plt.subplots(figsize=(4, 3))  # Réduire la largeur
        ax.bar(labels, values, color=['blue', 'orange'])
        ax.set_title("Average & Std Dev of Events per Actor")

        for i, v in enumerate(values):
            ax.text(i, v + 0.5, f"{v:.2f}", ha='center')

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 260)  # Taille ajustée pour la grille
        return canvas

    def create_verb_pie_chart(self, verb_counts):
        """Crée un camembert de distribution des verbes."""
        labels = list(verb_counts.keys())
        sizes = list(verb_counts.values())

        fig, ax = plt.subplots(figsize=(4, 3))  # Réduire la largeur
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.axis('equal')
        ax.set_title("Verb Distribution")

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 250)  # Taille ajustée pour la grille
        return canvas

    def create_object_pie_chart(self, object_counts):
        """Crée un camembert de distribution des objets."""
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())

        fig, ax = plt.subplots(figsize=(4, 3)) 
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.axis('equal')
        ax.set_title("Distribution of the Top 6 Objects")

        plt.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(300, 250)  # Taille ajustée pour la grille
        return canvas
