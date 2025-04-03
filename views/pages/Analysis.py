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
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.analysis_generated = False  # Flag indiquant si l'analyse a déjà été générée
        self.html_file_path = "comparative_analysis.html"  # Chemin du fichier HTML
        self.web_view = None  # Widget pour afficher le rapport HTML
        self.session_data = self.main_app.session_data
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
        print("showEvent called")  # Vérification du moment où showEvent est exécuté
        if not self.analysis_generated:
            print("Running analysis...")
            self.runAnalysis()
        super().showEvent(event)

    def runAnalysis(self):
        # Vérification des données de session
        session_data = self.main_app.session_data
        if session_data is None or session_data.empty:
            no_session_label = QLabel("No session data found. Please load or create session data first.")
            self.scroll_layout.addWidget(no_session_label)
            return

        # Vérification des données originales
        df_original = getattr(self.main_app, "processed_dataframe", None)
        if df_original is None or df_original.empty:
            no_data_label = QLabel("No original DataFrame found. Please load a file in 'Display' first.")
            self.scroll_layout.addWidget(no_data_label)
            return

        # Vérification des données générées
        generate_page = self.main_app.pages.get("generate", None)
        if generate_page is None:
            no_gen_label = QLabel("No generated data found. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return

        events_gen = generate_page.generated_data

        # Vérification si generated_data est vide
        if isinstance(events_gen, pd.DataFrame) and events_gen.empty:
            no_gen_label = QLabel("Generated data is empty. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return
        elif isinstance(events_gen, list) and not events_gen:
            no_gen_label = QLabel("Generated data list is empty. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return

        # Conversion des données générées en DataFrame
        df_generated = self.convert_generated_data(events_gen)

        # Vérification de la structure des données
        if not self.validate_dataframe(df_generated):
            error_label = QLabel("Generated data structure is not compatible with original data.")
            self.scroll_layout.addWidget(error_label)
            return

        # Déterminer si les données générées sont des sessions ou des actions
        is_session_data = 'actions' in session_data.columns

        if is_session_data:
            # Combiner toutes les actions de toutes les sessions en un seul DataFrame
            all_session_data = []
            for row in session_data['actions']:
                if isinstance(row, list) and all(isinstance(action, dict) for action in row):
                    all_session_data.extend(row)
                else:
                    print("Invalid 'actions' format in session_data")
            df_all_sessions = pd.DataFrame(all_session_data)

            # Génération des rapports HTML pour les données réelles et les sessions
            html_original = self.create_analysis_html(df_original, "ORIGINAL DATA")
            html_all_sessions = self.create_analysis_html(df_all_sessions, "GENERATED SESSION DATA")

            # Fusionner les rapports dans un seul bloc HTML côte à côte avec Flexbox
            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_all_sessions}</div>
            </div>
            """
        else:
            # Génération des rapports HTML pour les données réelles et les actions
            html_original = self.create_analysis_html(df_original, "ORIGINAL DATA")
            html_generated = self.create_analysis_html(df_generated, "GENERATED ACTION DATA")

            # Fusionner les rapports dans un seul bloc HTML côte à côte avec Flexbox
            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_generated}</div>
            </div>
            """

        # Sauvegarde du rapport dans un fichier HTML local
        with open(self.html_file_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        # Création ou rechargement du QWebEngineView
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.html_file_path)))
        self.analysis_generated = True  # Marquer que l'analyse a été générée

    def convert_generated_data(self, events_gen):
        """
        Convertit les données générées en DataFrame avec le même format que les données originales.
        """
        if isinstance(events_gen, pd.DataFrame) and 'actions' in events_gen.columns:
            # Si les données sont déjà sous forme de DataFrame avec une colonne 'actions'
            data_list = []
            for actions in events_gen['actions']:
                for action in actions:
                    data_list.append({
                        'id': action['id'],
                        'timestamp': action['timestamp'],
                        'verb': action['verb']['id'],
                        'actor': action['actor']['mbox'],
                        'object': action['object']['id'],
                        'duration': action.get('duration', 0.0)  # Utiliser 0.0 si 'duration' n'existe pas
                    })
            return pd.DataFrame(data_list)
        elif isinstance(events_gen, list):
            # Si les données sont sous forme de liste de dictionnaires
            return pd.DataFrame(events_gen)
        else:
            return pd.DataFrame()




    def validate_dataframe(self, df):
        """
        Vérifie si le DataFrame a la structure attendue.
        """
        required_columns = {'id', 'timestamp', 'verb', 'actor', 'object', 'duration'}
        return required_columns.issubset(df.columns)

    def create_analysis_html(self, df, dataset_title):
        """
        Calcule les statistiques et génère des graphiques pour un DataFrame donné,
        retourne un contenu HTML (sans balises <html>/<body> complètes).
        """
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        # Extraction des noms depuis les colonnes 'verb', 'actor' et 'object'
        df['verb_name'] = df['verb'].apply(self.extract_verb) if 'verb' in df.columns else "Unknown"
        df['actor_name'] = df['actor'].apply(self.extract_actor) if 'actor' in df.columns else "Unknown"
        df['object_name'] = df['object'].apply(self.extract_object) if 'object' in df.columns else "Unknown"

        # Traitement des timestamps avec formatage explicite pour éviter l'avertissement
        if 'timestamp' in df.columns:
            sample = df['timestamp'].iloc[0] if not df['timestamp'].empty else None
            if sample is not None and isinstance(sample, str):
                if "-" in sample or ":" in sample:
                    timestamps = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce').dropna()
                elif sample.isdigit():
                    timestamps = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='s', errors='coerce').dropna()
                else:
                    timestamps = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
            else:
                timestamps = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
            if not timestamps.empty:
                first_event = timestamps.min().strftime("%Y-%m-%d %H:%M:%S")
                last_event = timestamps.max().strftime("%Y-%m-%d %H:%M:%S")
            else:
                first_event = last_event = "N/A"
        else:
            first_event = last_event = "N/A"

        # Calcul des statistiques
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

        if 'duration' in df.columns:
            durations_per_verb = df.groupby('verb_name')['duration'].apply(list)
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

        if actor_counts:
            fig_list.append(self.create_actor_pie_chart(actor_counts, title_prefix + "Actor Distribution"))

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
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Category", "y": y_axis},
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        colors = ['#636EFA', '#EF553B', '#00CC96']
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_event_time_chart(self, first_event, last_event, title):
        labels = ["First Event", "Last Event"]
        values = [1, 1]
        colors = ['#636EFA', '#EF553B']
        fig = px.bar(
            x=labels, y=values,
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Count"},
            title=title,
            width=800, height=400
        )
        fig.update_traces(textposition="outside", marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_statistics_bar_chart(self, avg_value, std_value, title):
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]
        # Palette pour deux barres
        colors = ['#636EFA', '#EF553B']
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Value"},
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_actor_pie_chart(self, actor_counts, title):
        labels = list(actor_counts.keys())
        sizes = list(actor_counts.values())
        # Palette pour le diagramme en camembert
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker=dict(colors=colors[:len(labels)]))
        return fig


    def clear_layout(self, layout):
        """Supprimer tous les widgets d'un layout donné."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()



    def create_object_pie_chart(self, object_counts, title):
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())
        # Palette pour le diagramme en camembert
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker=dict(colors=colors[:len(labels)]))
        return fig
