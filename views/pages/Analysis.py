import os
from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView


# -------------------------------
# Worker pour exécuter le traitement en arrière-plan
# -------------------------------
class AnalysisWorker(QObject):
    finished = pyqtSignal(str)  # Émet le chemin absolu du fichier HTML généré
    error = pyqtSignal(str)     # Émet un message d'erreur en cas de problème

    def __init__(self, main_app, html_file_path, analysis_inst):
        """
        :param main_app: Référence à l'application principale.
        :param html_file_path: Chemin de sauvegarde du rapport HTML.
        :param analysis_inst: Instance de la classe Analysis pour accéder aux méthodes utilitaires.
        """
        super().__init__()
        self.main_app = main_app
        self.html_file_path = html_file_path
        self.analysis_inst = analysis_inst

    @pyqtSlot()
    def run(self):
        try:
            session_data = self.main_app.session_data
            df_original = getattr(self.main_app, "processed_dataframe", None)
            generate_page = self.main_app.pages.get("generate", None)

            # Vérifications préliminaires sur les données
            if session_data is None or session_data.empty:
                final_html = "<h2>Error</h2><p>No session data found. Please load or create session data first.</p>"
            elif df_original is None or df_original.empty:
                final_html = "<h2>Error</h2><p>No original DataFrame found. Please load a file in 'Display' first.</p>"
            elif generate_page is None:
                final_html = "<h2>Error</h2><p>No generated data found. Please generate data in 'Generate' first.</p>"
            else:
                events_gen = generate_page.generated_data

                if isinstance(events_gen, pd.DataFrame) and events_gen.empty:
                    final_html = "<h2>Error</h2><p>Generated data is empty. Please generate data in 'Generate' first.</p>"
                elif isinstance(events_gen, list) and not events_gen:
                    final_html = "<h2>Error</h2><p>Generated data list is empty. Please generate data in 'Generate' first.</p>"
                else:
                    # Conversion des données générées en DataFrame
                    df_generated = self.analysis_inst.convert_generated_data(events_gen)
                    if not self.analysis_inst.validate_dataframe(df_generated):
                        final_html = "<h2>Error</h2><p>Generated data structure is not compatible with original data.</p>"
                    else:
                        # Vérifie si les données de session contiennent la colonne 'actions'
                        is_session_data = 'actions' in session_data.columns
                        if is_session_data:
                            all_session_data = []
                            for row in session_data['actions']:
                                if isinstance(row, list) and all(isinstance(action, dict) for action in row):
                                    all_session_data.extend(row)
                            df_all_sessions = pd.DataFrame(all_session_data)
                            html_original = self.analysis_inst.create_analysis_html(df_original, "ORIGINAL DATA")
                            html_all_sessions = self.analysis_inst.create_analysis_html(df_all_sessions, "GENERATED SESSION DATA")
                            final_html = f"""
                            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                                <div style="flex: 1; margin: 10px;">{html_original}</div>
                                <div style="flex: 1; margin: 10px;">{html_all_sessions}</div>
                            </div>
                            """
                        else:
                            html_original = self.analysis_inst.create_analysis_html(df_original, "ORIGINAL DATA")
                            html_generated = self.analysis_inst.create_analysis_html(df_generated, "GENERATED ACTION DATA")
                            final_html = f"""
                            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                                <div style="flex: 1; margin: 10px;">{html_original}</div>
                                <div style="flex: 1; margin: 10px;">{html_generated}</div>
                            </div>
                            """
            with open(self.html_file_path, "w", encoding="utf-8") as f:
                f.write(final_html)
            self.finished.emit(os.path.abspath(self.html_file_path))
        except Exception as e:
            self.error.emit(str(e))


# -------------------------------
# Classe Analysis
# -------------------------------
class Analysis(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.analysis_generated = False
        self.html_file_path = "comparative_analysis.html"
        self.web_view = None
        self.analysis_thread = None
        self.worker = None
        self.loading_label = None
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
        # Lancement de l'analyse en arrière-plan dès l'affichage, si ce n'est pas déjà généré
        if not self.analysis_generated:
            self.showLoadingIndicator()
            self.startAnalysisThread()
        super().showEvent(event)

    def startAnalysisThread(self):
        self.analysis_thread = QThread()
        # Passe l'instance self à AnalysisWorker pour accéder aux fonctions d'extraction et de création de rapport
        self.worker = AnalysisWorker(self.main_app, self.html_file_path, self)
        self.worker.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.onAnalysisFinished)
        self.worker.error.connect(self.onAnalysisError)
        self.worker.finished.connect(self.analysis_thread.quit)
        self.worker.error.connect(self.analysis_thread.quit)
        self.analysis_thread.start()

    def onAnalysisFinished(self, html_file_abs_path):
        self.loading_label.deleteLater()
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)
        self.web_view.setUrl(QUrl.fromLocalFile(html_file_abs_path))
        self.analysis_generated = True

    def onAnalysisError(self, error_message):
        self.loading_label.setText(f"Erreur lors du chargement : {error_message}")

    def showLoadingIndicator(self):
        # Texte en gras grâce au HTML
        txt = "<b>Loading data, please wait...</b>"
        if not self.loading_label:
            self.loading_label = QLabel(txt, self)
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout().insertWidget(0, self.loading_label)
        self.loading_label.show()

    # --- Méthodes utilitaires d'Analysis ---
    def convert_generated_data(self, events_gen):
        if isinstance(events_gen, pd.DataFrame) and 'actions' in events_gen.columns:
            data_list = []
            for actions in events_gen['actions']:
                for action in actions:
                    data_list.append({
                        'id': action['id'],
                        'timestamp': action['timestamp'],
                        'verb': action['verb']['id'],
                        'actor': action['actor']['mbox'],
                        'object': action['object']['id'],
                        'duration': action.get('duration', 0.0)
                    })
            return pd.DataFrame(data_list)
        elif isinstance(events_gen, list):
            return pd.DataFrame(events_gen)
        else:
            return pd.DataFrame()

    def validate_dataframe(self, df):
        required_columns = {'id', 'timestamp', 'verb', 'actor', 'object', 'duration'}
        return required_columns.issubset(df.columns)

    def create_analysis_html(self, df, dataset_title):
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        # Extraction et transformation des données
        if 'verb' in df.columns:
            df['verb_name'] = df['verb'].apply(lambda v: self.extract_verb(v) if isinstance(v, dict) else str(v))
        else:
            df['verb_name'] = "Unknown"

        if 'actor' in df.columns:
            df['actor_name'] = df['actor'].apply(lambda a: self.extract_actor(a) if isinstance(a, dict) else str(a))
        else:
            df['actor_name'] = "Unknown"

        if 'object' in df.columns:
            df['object_name'] = df['object'].apply(lambda o: self.extract_object(o) if isinstance(o, dict) else str(o))
        else:
            df['object_name'] = "Unknown"

        # Traitement des timestamps
        if 'timestamp' in df.columns:
            sample = df['timestamp'].iloc[0] if not df['timestamp'].empty else None
            if sample is not None and isinstance(sample, str):
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

        # Traitement de la colonne de durée
        avg_duration = {}
        if 'duration' in df.columns:
            df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
            durations_per_verb = df.groupby('verb_name')['duration'].apply(list)
            avg_duration = {v: mean(d) for v, d in durations_per_verb.items() if d}
        elif 'Duration' in df.columns:
            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')
            durations_per_verb = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration = {v: mean(d) for v, d in durations_per_verb.items() if d}

        fig_list = []
        title_prefix = f"[{dataset_title}] "

        fig_list.append(self.create_bar_chart(verb_counts, title_prefix + "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts, title_prefix + "Object Distribution"))
        fig_list.append(self.create_event_time_chart(first_event, last_event, title_prefix + "Event Timestamps"))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, title_prefix + "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_events, std_events, title_prefix + "Avg & Std Dev"))

        if avg_duration:
            fig_list.append(self.create_bar_chart(avg_duration, title_prefix + "Average Duration per Verb", y_axis="Avg duration (s)"))

        if actor_counts:
            fig_list.append(self.create_actor_pie_chart(actor_counts, title_prefix + "Actor Distribution"))

        html_content = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>{dataset_title}</h2>" + html_content

    # --- Fonctions d'extraction utilitaires mises à jour ---
    def extract_verb(self, verb_value):
        """
        Extrait uniquement le nom du verbe.
        Si verb_value est un dictionnaire, on extrait la clé 'id' et on renvoie la dernière partie de l'URL.
        Sinon, si c'est une chaîne, on fait de même.
        """
        if isinstance(verb_value, dict):
            vid = verb_value.get('id', '')
            if isinstance(vid, str) and vid.startswith("http"):
                return vid.split("/")[-1]
            return vid
        elif isinstance(verb_value, str):
            if verb_value.startswith("http"):
                return verb_value.split("/")[-1]
            return verb_value
        return "Unknown"

    def extract_actor(self, actor_value):
        if isinstance(actor_value, dict):
            mbox = actor_value.get('mbox', '')
            if isinstance(mbox, str):
                if mbox.startswith("mailto:"):
                    return mbox.replace("mailto:", "")
                elif mbox.startswith("http"):
                    return mbox.split("/")[-1]
                return mbox
            return str(actor_value)
        elif isinstance(actor_value, str):
            if actor_value.startswith("mailto:"):
                return actor_value.replace("mailto:", "")
            elif actor_value.startswith("http"):
                return actor_value.split("/")[-1]
            return actor_value
        return "Unknown"

    def extract_object(self, object_value):
        if isinstance(object_value, dict):
            oid = object_value.get('id', '')
            if isinstance(oid, str) and oid.startswith("http"):
                return oid.split("/")[-1]
            return oid
        elif isinstance(object_value, str):
            if object_value.startswith("http"):
                return object_value.split("/")[-1]
            return object_value
        return "Unknown"

    # --- Fonctions de création de graphiques Plotly ---
    def create_bar_chart(self, data, title, y_axis="Count"):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        color_map = {label: colors[i % len(colors)] for i, label in enumerate(sorted(set(labels)))}
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Category", "y": y_axis},
            title=title,
            width=800, height=400,
            color=labels,
            color_discrete_map=color_map
        )
        fig.update_layout(showlegend=False)
        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        colors = ['#636EFA', '#EF553B', '#00CC96']
        fig = px.bar(
            x=labels,
            y=values,
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
            x=labels,
            y=values,
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
        colors = ['#636EFA', '#EF553B']
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Stats", "y": "Value"},
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_object_pie_chart(self, object_counts, title):
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker=dict(colors=colors[:len(labels)]))
        return fig

    def create_actor_pie_chart(self, actor_counts, title):
        labels = list(actor_counts.keys())
        sizes = list(actor_counts.values())
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title,
            width=800, height=400
        )
        fig.update_traces(marker=dict(colors=colors[:len(labels)]))
        return fig