from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import plotly.express as px
import plotly.io as pio
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os

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
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Widget pour les graphiques
        self.scroll_widget = QWidget()  # Créer un QWidget qui contiendra les graphiques
        self.scroll_layout = QVBoxLayout(self.scroll_widget)  # Ajouter un QVBoxLayout à ce QWidget

        # QScrollArea pour permettre le défilement si le contenu est trop grand
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # Redimensionner la fenêtre principale si nécessaire
        self.setWindowTitle("Statistics Viewer")
        self.resize(1600, 2000)  # Taille de la fenêtre principale plus grande (1600x1000 pixels)

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

        # Fusionner toutes les listes imbriquées ou utiliser directement la liste d'événements
        data = self.download_button.json_data
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            events = []
            for batch in data:
                events.extend(batch)
        else:
            events = data

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
                try:
                    timestamps.append(datetime.fromisoformat(timestamp))  # Convertir en datetime
                except ValueError:
                    print(f"Erreur de conversion de timestamp : {timestamp}")  # Gestion des erreurs de format

            verbs.append(verb)
            actors.append(actor)
            objects.append(obj)
            events_per_actor[actor] += 1

        # Calcul des statistiques des timestamps
        if timestamps:
            # Trier les timestamps du plus ancien au plus récent
            timestamps.sort()
            first_event = timestamps[0].strftime("%Y-%m-%d %H:%M:%S")  # Première date
            last_event = timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")  # Dernière date
        else:
            first_event = last_event = "N/A"

        verb_counts = Counter(verbs)
        # Ne garder que les 6 objets les plus utilisés
        object_counts = dict(Counter(objects).most_common(6))
        avg_events = mean(events_per_actor.values()) if events_per_actor else 0
        std_events = stdev(events_per_actor.values()) if len(events_per_actor) > 1 else 0
        min_events = min(events_per_actor.values(), default=0)
        max_events = max(events_per_actor.values(), default=0)

        # Créer un fichier HTML unique pour afficher tous les graphiques
        self.create_html_report(
            verb_counts, 
            object_counts, 
            first_event, last_event,
            avg_events, min_events, max_events,
            avg_events, std_events,
            actor_counts=events_per_actor
        )

        # Charger et afficher le fichier HTML dans QWebEngineView
        self.display_html_report()

    def clearStatistics(self):
        """Efface les graphiques précédents"""
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def create_html_report(self, verb_counts, object_counts, first_event, last_event, 
                           avg_events, min_events, max_events, avg_value, std_value, actor_counts=None):
        """Génère un rapport HTML avec tous les graphiques"""
        # Créer une liste pour stocker les figures
        fig_list = []

        # Ajouter les graphiques à la liste
        fig_list.append(self.create_bar_chart(verb_counts, "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts))
        fig_list.append(self.create_event_time_chart(first_event, last_event))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_value, std_value))
        
        # Remplacer le graphique de verbes par celui des acteurs si fourni
        if actor_counts:
            fig_list.append(self.create_actor_pie_chart(actor_counts))

        # Créer le contenu HTML pour les graphiques
        html_content = ""

        for fig in fig_list:
            # Convertir chaque graphique en HTML
            fig_html = pio.to_html(fig, full_html=False)
            html_content += fig_html

        # Sauvegarder le contenu HTML dans un fichier avec l'encodage UTF-8
        html_file_path = "all_charts_report.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def display_html_report(self):
        """Affiche le rapport HTML dans un QWebEngineView"""
        web_view = QWebEngineView()
        web_view.setUrl(QUrl.fromLocalFile(os.path.abspath("all_charts_report.html")))  # Charger le fichier HTML
        self.scroll_layout.addWidget(web_view)  # Ajouter à la vue scrollable

    def create_bar_chart(self, data, title):
        """Crée un graphique en barres avec Plotly."""
        labels = list(data.keys())
        values = [data[label] for label in labels]

        # Définir des couleurs différentes pour chaque barre
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32']  # Liste de couleurs

        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Verbs", "y": "Count"},
            title=title,
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque barre
        fig.update_traces(marker_color=colors[:len(labels)])  # Limiter à la taille des barres

        # Désactiver la légende
        fig.update_layout(showlegend=False)

        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        """Crée un histogramme avec Plotly."""
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]

        # Définir des couleurs différentes pour chaque barre
        colors = ['#636EFA', '#EF553B', '#00CC96']  # Liste des couleurs personnalisées

        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title,
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque barre
        fig.update_traces(marker_color=colors)

        # Désactiver la légende
        fig.update_layout(showlegend=False)

        return fig

    def create_event_time_chart(self, first_event, last_event):
        """Crée un graphique d'événements avec Plotly."""
        labels = ["First Event", "Last Event"]
        values = [1, 1]

        # Définir des couleurs différentes pour chaque barre
        colors = ['#636EFA', '#EF553B']  # Liste de couleurs personnalisées

        fig = px.bar(
            x=labels, y=values,
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Timestamp"},
            title="Event Timestamps",
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque barre
        fig.update_traces(marker_color=colors)

        # Désactiver la légende
        fig.update_layout(showlegend=False)

        return fig

    def create_statistics_bar_chart(self, avg_value, std_value):
        """Crée un graphique pour la moyenne et l'écart-type avec Plotly."""
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]

        # Définir des couleurs différentes pour chaque barre
        colors = ['#636EFA', '#EF553B']  # Liste de couleurs personnalisées

        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Value"},
            title="Average & Std Dev of Events per Actor",
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque barre
        fig.update_traces(marker_color=colors)

        # Désactiver la légende
        fig.update_layout(showlegend=False)

        return fig

    def create_actor_pie_chart(self, actor_counts):
        """Crée un graphique en camembert pour la distribution des acteurs avec Plotly."""
        labels = list(actor_counts.keys())
        sizes = list(actor_counts.values())

        # Définir des couleurs différentes pour chaque segment
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32']  # Liste de couleurs

        fig = px.pie(
            names=labels, values=sizes,
            title="Actor Distribution",  # Nouveau titre pour les acteurs
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque segment
        fig.update_traces(marker_colors=colors[:len(labels)])  # Limiter à la taille des segments

        return fig

    def create_object_pie_chart(self, object_counts):
        """Crée un graphique en camembert pour les objets avec Plotly."""
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())

        # Définir des couleurs différentes pour chaque segment
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32']  # Liste de couleurs

        fig = px.pie(
            names=labels, values=sizes,
            title="Object Distribution",
            width=1000,  # Largeur du graphique
            height=500  # Hauteur du graphique
        )

        # Appliquer les couleurs à chaque segment
        fig.update_traces(marker_colors=colors[:len(labels)])  # Limiter à la taille des segments

        return fig
