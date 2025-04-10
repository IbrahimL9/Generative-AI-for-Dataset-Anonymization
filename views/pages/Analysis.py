import os
from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio

from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtWebEngineWidgets import QWebEngineView


class Analysis(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.analysis_generated = False  # Flag indicating if the analysis has already been generated
        self.html_file_path = "comparative_analysis.html"  # Path to the HTML report
        self.web_view = None  # Web view widget for displaying the HTML report
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
        super().showEvent(event)

        if not self.analysis_generated:
            # 1. Afficher le message de chargement tout de suite
            self.showLoadingScreen()

            # 2. Lancer l'analyse juste après, pour permettre à l'UI d'afficher d'abord "Loading..."
            QTimer.singleShot(300, self.runAnalysis)

    def showLoadingScreen(self):
        """
        Displays an immediate 'Loading, please wait...' message in the QWebEngineView.
        """
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)

        # Simple HTML content for "loading" message
        loading_html = """
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; text-align: center;">
            <h2>Loading, please wait...</h2>
        </body>
        </html>
        """
        self.web_view.setHtml(loading_html)

    def runAnalysis(self):
        print("Running analysis...")
        # --- 1) Check session data ---
        session_data = self.main_app.session_data
        # If you need to handle empty session_data, add your logic here

        # --- 2) Original data check ---
        df_original = getattr(self.main_app, "processed_dataframe", None)
        if df_original is None or df_original.empty:
            no_data_label = QLabel("No original DataFrame found. Please load a file in 'Display' first.")
            self.scroll_layout.addWidget(no_data_label)
            return

        # --- 3) Generated data check ---
        generate_page = self.main_app.pages.get("generate", None)
        if generate_page is None:
            no_gen_label = QLabel("No generated data found. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return

        events_gen = generate_page.generated_data

        # If generated data is empty
        if isinstance(events_gen, pd.DataFrame) and events_gen.empty:
            no_gen_label = QLabel("Generated data is empty. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return
        elif isinstance(events_gen, list) and not events_gen:
            no_gen_label = QLabel("Generated data list is empty. Please generate data in 'Generate' first.")
            self.scroll_layout.addWidget(no_gen_label)
            return

        # Convert generated data to DataFrame
        df_generated = self.convert_generated_data(events_gen)

        # Check structure
        if not self.validate_dataframe(df_generated):
            error_label = QLabel("Generated data structure is not compatible with original data.")
            self.scroll_layout.addWidget(error_label)
            return

        # Determine if we have session data (looking for 'actions' col)
        is_session_data = 'actions' in session_data.columns

        # Build a global color map for the verbs
        all_verbs_set = set()

        if 'verb' in df_original.columns:
            df_original['verb_name'] = df_original['verb'].apply(self.extract_verb)
            all_verbs_set.update(df_original['verb_name'])

        if 'verb' in df_generated.columns:
            df_generated['verb_name'] = df_generated['verb'].apply(self.extract_verb)
            all_verbs_set.update(df_generated['verb_name'])

        color_palette = [
            '#636EFA', '#EF553B', '#00CC96', '#FFD700',
            '#FF1493', '#32CD32', '#FFA500', '#8A2BE2',
            '#FF4500', '#00CED1'
        ]
        verb_color_map = {
            verb: color_palette[i % len(color_palette)]
            for i, verb in enumerate(sorted(all_verbs_set))
        }

        # --- 4) Generate the HTML report ---
        if is_session_data:
            # Flatten actions from all sessions into a single DataFrame
            all_session_data = []
            for row in session_data['actions']:
                if isinstance(row, list) and all(isinstance(action, dict) for action in row):
                    all_session_data.extend(row)
                else:
                    print("Invalid 'actions' format in session_data")
            df_all_sessions = pd.DataFrame(all_session_data)

            html_original = self.create_analysis_html(df_original, "ORIGINAL DATA", verb_color_map)
            html_all_sessions = self.create_analysis_html(df_all_sessions, "GENERATED SESSION DATA", verb_color_map)

            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_all_sessions}</div>
            </div>
            """
        else:
            html_original = self.create_analysis_html(df_original, "ORIGINAL DATA", verb_color_map)
            html_generated = self.create_analysis_html(df_generated, "GENERATED ACTION DATA", verb_color_map)

            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_generated}</div>
            </div>
            """

        # --- 5) Save the HTML locally ---
        with open(self.html_file_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        # --- 6) Load the HTML file into the web view ---
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)

        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.html_file_path)))
        self.analysis_generated = True  # Mark the analysis as done

    # ---------------------------------------------------
    #                 DATAFRAME HELPERS
    # ---------------------------------------------------
    def convert_generated_data(self, events_gen):
        """
        Converts the generated data to a DataFrame matching the original structure.
        """
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
        """
        Checks if the DataFrame has the required columns.
        """
        required_columns = {'id', 'timestamp', 'verb', 'actor', 'object', 'duration'}
        return required_columns.issubset(df.columns)

    # ---------------------------------------------------
    #                HTML ANALYSIS CREATION
    # ---------------------------------------------------
    def create_analysis_html(self, df, dataset_title, verb_color_map=None):
        """
        Computes statistics and generates Plotly charts for the given DataFrame,
        returning HTML content (without full <html>/<body> wrappers).
        """
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        df['verb_name'] = (
            df['verb'].apply(self.extract_verb) if 'verb' in df.columns else "Unknown"
        )
        df['actor_name'] = (
            df['actor'].apply(self.extract_actor) if 'actor' in df.columns else "Unknown"
        )
        df['object_name'] = (
            df['object'].apply(self.extract_object) if 'object' in df.columns else "Unknown"
        )

        # Timestamps
        if 'timestamp' in df.columns:
            sample = df['timestamp'].iloc[0] if not df['timestamp'].empty else None
            if sample is not None and isinstance(sample, str):
                if "-" in sample or ":" in sample:
                    timestamps = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
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

        # Basic stats
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

        # If you have another column 'Duration' (capital D), handle similarly
        if 'Duration' in df.columns:
            durations_per_verbe = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration_per_verbe = {v: mean(d) for v, d in durations_per_verbe.items() if d}
        else:
            avg_duration_per_verbe = {}

        # Build charts
        fig_list = []
        title_prefix = f"[{dataset_title}] "

        fig_list.append(self.create_bar_chart(verb_counts, title_prefix + "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts, title_prefix + "Object Distribution"))
        fig_list.append(self.create_event_time_chart(first_event, last_event, title_prefix + "Event Timestamps"))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, title_prefix + "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_events, std_events, title_prefix + "Avg & Std Dev"))

        if avg_duration_per_verb:
            fig_list.append(self.create_bar_chart(
                avg_duration_per_verb, title_prefix + "Average duration per Verb", y_axis="Avg duration (s)"
            ))

        if avg_duration_per_verbe:
            fig_list.append(self.create_bar_chart(
                avg_duration_per_verbe, title_prefix + "Average Duration per Verb", y_axis="Avg Duration (s)"
            ))

        if actor_counts:
            fig_list.append(self.create_actor_per_verb_pie_chart(df, title_prefix + "Actors per Verb", verb_color_map))

        # Convert figures to HTML
        fig_html = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>{dataset_title}</h2>" + fig_html

    # ---------------------------------------------------
    #               EXTRACTION UTILITIES
    # ---------------------------------------------------
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

    # ---------------------------------------------------
    #             PLOTLY CHART CREATION
    # ---------------------------------------------------
    def create_bar_chart(self, data, title, y_axis="Count"):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        colors = [
            '#636EFA', '#EF553B', '#00CC96', '#FFD700',
            '#FF1493', '#32CD32', '#FFA500'
        ]
        color_map = {label: colors[i % len(colors)] for i, label in enumerate(sorted(set(labels)))}
        fig = px.bar(
            x=labels, y=values,
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

    def create_actor_per_verb_pie_chart(self, df, title, verb_color_map=None):
        actor_per_verb = df.groupby('verb_name')['actor_name'].nunique().to_dict()
        labels = list(actor_per_verb.keys())
        values = list(actor_per_verb.values())

        if verb_color_map:
            colors = [verb_color_map.get(v, '#CCCCCC') for v in labels]
        else:
            colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']

        fig = px.pie(
            names=labels,
            values=values,
            title=title,
            width=1000, height=500
        )
        fig.update_traces(marker=dict(colors=colors))
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

    def showLoadingScreen(self):

        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)

        # Simple HTML content pour le message "Loading"
        loading_html = """
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; text-align: center;">
            <h2>Loading, please wait...</h2>
        </body>
        </html>
        """

        self.web_view.setHtml(loading_html)
