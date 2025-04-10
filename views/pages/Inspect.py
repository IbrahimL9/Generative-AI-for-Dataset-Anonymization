from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os


class Inspect(QWidget):
    def __init__(self, download_button, main_app):
        super().__init__()
        self.download_button = download_button
        self.main_app = main_app
        self.web_view = None  # Pour conserver le QWebEngineView existant
        self.initUI()

        # Optionnel : regénérer les statistiques à chaque fois qu'un fichier est chargé.
        self.download_button.file_loaded.connect(self.updateStatistics)

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(20)

        # Titre
        title = QLabel("STATISTICS")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Zone de défilement pour afficher le rapport HTML
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.setWindowTitle("Statistics Viewer")
        self.resize(1600, 2000)
        self.setLayout(layout)

    def updateStatistics(self):
        """
        1) Tente de lire le DataFrame dans main_app.processed_dataframe.
        2) S'il n'existe pas ou est vide, on le crée à partir de download_button.json_data.
        3) Puis on génère les statistiques et graphiques.
        """
        df = getattr(self.main_app, 'processed_dataframe', None)

        # Créer le DataFrame si nécessaire
        if df is None or df.empty:
            data = self.download_button.json_data
            if not data:
                print("❌ Aucune donnée JSON chargée. Veuillez charger un fichier.")
                return

            # Si data est une liste de listes, on l'aplatit
            events = sum(data, []) if isinstance(data[0], list) else data

            # Calculer la durée entre événements
            events = self.convert_to_duration(events)

            # Construire le DataFrame et le stocker dans main_app
            df = pd.DataFrame(events)
            self.main_app.processed_dataframe = df

        if df.empty:
            print("❌ Le DataFrame est vide (0 lignes).")
            return

        # Nettoyer l'affichage avant de recréer les widgets
        self.clearStatistics()

        print(f"Nombre total d'événements : {len(df)}")

        # Extraction des noms
        if 'verb' in df.columns:
            df['verb_name'] = df['verb'].apply(lambda v: self.extract_name(v.get('id', 'Unknown')) if isinstance(v, dict) else str(v))
        else:
            df['verb_name'] = "Unknown"

        if 'actor' in df.columns:
            df['actor_name'] = df['actor'].apply(lambda a: self.extract_name(a.get('mbox', 'Unknown')) if isinstance(a, dict) else str(a))
        else:
            df['actor_name'] = "Unknown"

        if 'object' in df.columns:
            df['object_name'] = df['object'].apply(lambda o: self.extract_name(o.get('id', 'Unknown')) if isinstance(o, dict) else str(o))
        else:
            df['object_name'] = "Unknown"

        # Gestion des timestamps
        timestamps = pd.to_datetime(df.get('timestamp'), errors='coerce').dropna()
        if not timestamps.empty:
            first_event = timestamps.min().strftime("%Y-%m-%d %H:%M:%S")
            last_event = timestamps.max().strftime("%Y-%m-%d %H:%M:%S")
        else:
            first_event = last_event = "N/A"

        # Statistiques
        verb_counts = Counter(df['verb_name'])
        object_counts = dict(Counter(df['object_name']).most_common(6))
        actor_counts = Counter(df['actor_name'])

        if actor_counts:
            avg_events = mean(actor_counts.values())
            std_events = stdev(actor_counts.values()) if len(actor_counts) > 1 else 0
            min_events = min(actor_counts.values())
            max_events = max(actor_counts.values())
        else:
            avg_events = std_events = min_events = max_events = 0

        # Durée moyenne par verbe
        if 'Duration' in df.columns:
            durations_per_verb = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration_per_verb = {v: mean(d) for v, d in durations_per_verb.items() if d}
        else:
            avg_duration_per_verb = {}

        # Génération du rapport HTML
        self.create_html_report(
            verb_counts,
            object_counts,
            first_event, last_event,
            avg_events, min_events, max_events,
            avg_events, std_events,
            actor_counts=actor_counts,
            avg_duration_per_verb=avg_duration_per_verb
        )
        self.display_html_report()

    def clearStatistics(self):
        """Supprime tous les widgets de la zone de scroll."""
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def extract_name(self, value):
        """Extrait un nom lisible depuis un mailto: ou une URL, sinon retourne la valeur brute."""
        if isinstance(value, str):
            if value.startswith("mailto:"):
                return value.replace("mailto:", "")
            elif value.startswith("http"):
                return value.split("/")[-1]
        return str(value)

    def convert_to_duration(self, events):
        """
        Convertit le timestamp en datetime, trie les événements par acteur et timestamp,
        calcule la durée entre événements successifs et réinjecte cette durée dans les événements.
        """
        if not events:
            return events

        df = pd.DataFrame(events)
        if 'timestamp' not in df.columns:
            return events

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['actor_name'] = df['actor'].apply(lambda a: self.extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a))
        df = df.sort_values(by=['actor_name', 'timestamp'])
        df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds().fillna(0)

        for idx, dur in zip(df.index, df['Duration']):
            events[idx]['Duration'] = float(dur)

        return events

    # --- Génération et affichage du rapport HTML via Plotly ---
    def create_html_report(self, verb_counts, object_counts,
                           first_event, last_event,
                           avg_events, min_events, max_events,
                           avg_value, std_value,
                           actor_counts=None, avg_duration_per_verb=None):
        fig_list = []
        # Graphiques principaux
        fig_list.append(self.create_bar_chart(verb_counts, "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts))
        fig_list.append(self.create_event_time_chart(first_event, last_event))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_value, std_value))
        # Graphiques additionnels
        if avg_duration_per_verb:
            fig_list.append(self.create_bar_chart(avg_duration_per_verb, "Average Duration per Verb", y_axis="Avg Duration (s)"))
        if actor_counts:
            fig_list.append(self.create_actor_per_verb_pie_chart())
        html_content = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        html_file_path = "all_charts_report.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def display_html_report(self):
        """Affiche le rapport HTML dans un QWebEngineView. On conserve le widget pour éviter une recréation complète."""
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        report_url = QUrl.fromLocalFile(os.path.abspath("all_charts_report.html"))
        if hasattr(self, 'web_view') and self.web_view is not None:
            self.web_view.setUrl(report_url)
        else:
            self.web_view = QWebEngineView()
            self.web_view.setUrl(report_url)
            self.scroll_layout.addWidget(self.web_view)

    # --- Fonctions de création de graphiques Plotly ---
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

    def create_actor_per_verb_pie_chart(self):
        """
        Calcule le nombre d'acteurs distincts par verbe et retourne un graphique camembert.
        """
        df = self.main_app.processed_dataframe
        actor_per_verb = df.groupby('verb_name')['actor_name'].nunique().to_dict()

        fig = px.pie(
            names=list(actor_per_verb.keys()),
            values=list(actor_per_verb.values()),
            title="Nombre d'acteurs distincts par verbe",
            width=1000,
            height=500
        )
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig.update_traces(marker_colors=colors[:len(actor_per_verb)])
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
