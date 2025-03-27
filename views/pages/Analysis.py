import os
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


class Analysis(QWidget):
    """
    Compare le DataFrame original (main_app.processed_dataframe)
    et les données générées (par Generate).
    """
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(20)

        title = QLabel("COMPARATIVE ANALYSIS")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.setWindowTitle("Analysis - Real vs. Generated")
        self.resize(1600, 2000)
        self.setLayout(layout)

    def showEvent(self, event):
        # À chaque fois que la page s'affiche, on relance l'analyse
        self.runAnalysis()
        super().showEvent(event)

    def runAnalysis(self):
        """
        Récupère le DataFrame "réel" + les données générées
        et construit le rapport comparatif.
        """
        self.clearLayout()

        df_original = getattr(self.main_app, "processed_dataframe", None)
        if df_original is None or df_original.empty:
            # pas de DF original
            no_data_label = QLabel("No original DataFrame found. Please load a file in 'Display' first.")
            self.scroll_layout.addWidget(no_data_label)
            return

        # Récupérer la liste "generated_data" depuis la page Generate
        # Vous pouvez l’avoir stockée ailleurs, par ex. main_app.generated_data
        generate_page = self.main_app.pages.get("generate", None)
        if not generate_page or not generate_page.generated_data:
            no_gen_label = QLabel("No generated data found. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return

        events_gen = generate_page.generated_data

        # Convertir la liste de dict en DataFrame
        # (vous pouvez adapter si votre structure est différente)
        df_generated = pd.DataFrame(events_gen)

        # --- Effectuer la même analyse pour "df_original" et "df_generated" ---
        # On produit deux rapports, qu’on concatène en un seul HTML
        html_original = self.create_analysis_html(df_original, "ORIGINAL DATA")
        html_generated = self.create_analysis_html(df_generated, "GENERATED DATA")

        # On fusionne le tout
        final_html = html_original + "<hr>" + html_generated

        # On sauvegarde localement
        html_file_path = "comparative_analysis.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        # On affiche via QWebEngineView
        web_view = QWebEngineView()
        web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(html_file_path)))
        self.scroll_layout.addWidget(web_view)

    def create_analysis_html(self, df, dataset_title):
        """
        Calcule les stats & graphiques pour un DataFrame donné (df),
        et génère un HTML (sans le conteneur <html><body> complet).
        """
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        # Extraction des colonnes
        df['verb_name'] = df['verb'].apply(self.extract_verb) if 'verb' in df.columns else "Unknown"
        df['actor_name'] = df['actor'].apply(self.extract_actor) if 'actor' in df.columns else "Unknown"
        df['object_name'] = df['object'].apply(self.extract_object) if 'object' in df.columns else "Unknown"

        # Timestamps
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
            if not timestamps.empty:
                first_event = timestamps.min().strftime("%Y-%m-%d %H:%M:%S")
                last_event = timestamps.max().strftime("%Y-%m-%d %H:%M:%S")
            else:
                first_event = last_event = "N/A"
        else:
            first_event = last_event = "N/A"

        # Stats
        verb_counts = Counter(df['verb_name'])
        object_counts = dict(Counter(df['object_name']).most_common(6))
        actor_counts = Counter(df['actor_name'])

        if len(actor_counts) > 0:
            avg_events = mean(actor_counts.values())
            min_events = min(actor_counts.values())
            max_events = max(actor_counts.values())
            std_events = stdev(actor_counts.values()) if len(actor_counts) > 1 else 0
        else:
            avg_events = min_events = max_events = std_events = 0

        # Moyenne des durées par verbe
        if 'Duration' in df.columns:
            durations_per_verb = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration_per_verb = {v: mean(d) for v, d in durations_per_verb.items() if d}
        else:
            avg_duration_per_verb = {}

        # Création des figures Plotly
        fig_list = []

        title_prefix = f"[{dataset_title}] "

        fig_list.append(self.create_bar_chart(verb_counts, title_prefix + "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts, title_prefix + "Object Distribution"))
        fig_list.append(self.create_event_time_chart(first_event, last_event, title_prefix + "Event Timestamps"))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, title_prefix + "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_events, std_events, title_prefix + "Avg & Std Dev"))

        if avg_duration_per_verb:
            fig_list.append(self.create_bar_chart(
                avg_duration_per_verb, title_prefix + "Average Duration per Verb", y_axis="Avg Duration (s)"
            ))

        # Distribution des acteurs
        if actor_counts:
            fig_list.append(self.create_actor_pie_chart(actor_counts, title_prefix + "Actor Distribution"))

        # Convertit toutes les figures en un unique bloc HTML
        fig_html = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>{dataset_title}</h2>" + fig_html

    # --- Fonctions utilitaires d’extraction ---
    def extract_verb(self, verb_dict):
        if not isinstance(verb_dict, dict):
            return "Unknown"
        vid = verb_dict.get('id', '')
        if vid.startswith("http"):
            return vid.split("/")[-1]
        return vid

    def extract_actor(self, actor_dict):
        if not isinstance(actor_dict, dict):
            return "Unknown"
        mbox = actor_dict.get('mbox', '')
        if mbox.startswith("mailto:"):
            return mbox.replace("mailto:", "")
        elif mbox.startswith("http"):
            return mbox.split("/")[-1]
        return mbox

    def extract_object(self, object_dict):
        if not isinstance(object_dict, dict):
            return "Unknown"
        oid = object_dict.get('id', '')
        if oid.startswith("http"):
            return oid.split("/")[-1]
        return oid

    # --- Fonctions de création de graphiques Plotly ---
    def create_bar_chart(self, data, title, y_axis="Count"):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Category", "y": y_axis},
            title=title,
            width=800, height=400
        )
        fig.update_layout(showlegend=False)
        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title, width=800, height=400
        )
        fig.update_layout(showlegend=False)
        return fig

    def create_event_time_chart(self, first_event, last_event, title):
        labels = ["First Event", "Last Event"]
        values = [1, 1]
        fig = px.bar(
            x=labels, y=values,
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Count"},
            title=title, width=800, height=400
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        return fig

    def create_statistics_bar_chart(self, avg_value, std_value, title):
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Value"},
            title=title, width=800, height=400
        )
        fig.update_layout(showlegend=False)
        return fig

    def create_actor_pie_chart(self, actor_counts, title):
        labels = list(actor_counts.keys())
        sizes = list(actor_counts.values())
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title, width=800, height=400
        )
        fig.update_layout(showlegend=False)
        return fig

    def create_object_pie_chart(self, object_counts, title):
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title, width=800, height=400
        )
        fig.update_layout(showlegend=False)
        return fig

    def clearLayout(self):
        """
        Supprime tous les widgets du layout scroll_layout,
        pour pouvoir régénérer un nouveau rapport.
        """
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
