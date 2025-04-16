# analysis_model.py
import os
from datetime import datetime
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio


class AnalysisModel:
    # ---------------------------------------------------
    #             DATAFRAME HELPERS
    # ---------------------------------------------------
    @staticmethod
    def convert_generated_data(events_gen):
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

    @staticmethod
    def validate_dataframe(df):
        """
        Checks if the DataFrame has the required columns.
        """
        required_columns = {'id', 'timestamp', 'verb', 'actor', 'object', 'duration'}
        return required_columns.issubset(df.columns)

    # ---------------------------------------------------
    #            EXTRACTION UTILITIES
    # ---------------------------------------------------
    @staticmethod
    def extract_name(value):
        """Extracts a readable name from a URL or mailto."""
        if isinstance(value, str):
            if value.startswith("mailto:"):
                return value.replace("mailto:", "")
            elif value.startswith("http"):
                return value.split("/")[-1]
        return str(value)

    @staticmethod
    def extract_verb(verb_dict):
        if not isinstance(verb_dict, dict):
            return "Unknown"
        vid = verb_dict.get('id', '')
        if vid.startswith("http"):
            return vid.split("/")[-1]
        return vid

    @staticmethod
    def extract_actor(actor_dict):
        if not isinstance(actor_dict, dict):
            return "Unknown"
        mbox = actor_dict.get('mbox', '')
        if mbox.startswith("mailto:"):
            return mbox.replace("mailto:", "")
        elif mbox.startswith("http"):
            return mbox.split("/")[-1]
        return mbox

    @staticmethod
    def extract_object(object_dict):
        if not isinstance(object_dict, dict):
            return "Unknown"
        oid = object_dict.get('id', '')
        if oid.startswith("http"):
            return oid.split("/")[-1]
        return oid

    # ---------------------------------------------------
    #           PLOTLY CHART CREATION FUNCTIONS
    # ---------------------------------------------------
    @staticmethod
    def create_bar_chart(data, title, y_axis="Count", width=800, height=400):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700',
                  '#FF1493', '#32CD32', '#FFA500']
        color_map = {label: colors[i % len(colors)] for i, label in enumerate(sorted(set(labels)))}
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Category", "y": y_axis},
            title=title,
            width=width, height=height,
            color=labels,
            color_discrete_map=color_map
        )
        fig.update_layout(showlegend=False)
        return fig

    @staticmethod
    def create_histogram(avg_value, min_value, max_value, title, width=800, height=400):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        colors = ['#636EFA', '#EF553B', '#00CC96']
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title,
            width=width, height=height
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    @staticmethod
    def create_event_time_chart(first_event, last_event, title, width=800, height=400):
        labels = ["First Event", "Last Event"]
        values = [1, 1]
        colors = ['#636EFA', '#EF553B']
        fig = px.bar(
            x=labels, y=values,
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Count"},
            title=title,
            width=width, height=height
        )
        fig.update_traces(textposition="outside", marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    @staticmethod
    def create_statistics_bar_chart(avg_value, std_value, title, width=800, height=400):
        labels = ["Average", "Std Dev"]
        values = [avg_value, std_value]
        colors = ['#636EFA', '#EF553B']
        fig = px.bar(
            x=labels, y=values,
            labels={"x": "Stats", "y": "Value"},
            title=title,
            width=width, height=height
        )
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    @staticmethod
    def create_actor_per_verb_pie_chart(df, title, verb_color_map=None, width=1000, height=500):
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
            width=width, height=height
        )
        fig.update_traces(marker=dict(colors=colors))
        return fig

    @staticmethod
    def create_object_pie_chart(object_counts, title, width=800, height=400):
        labels = list(object_counts.keys())
        sizes = list(object_counts.values())
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig = px.pie(
            names=labels,
            values=sizes,
            title=title,
            width=width, height=height
        )
        fig.update_traces(marker=dict(colors=colors[:len(labels)]))
        return fig

    # ---------------------------------------------------
    #             HTML ANALYSIS CREATION
    # ---------------------------------------------------
    def create_analysis_html(self, df, dataset_title, verb_color_map=None):
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        # Extraire les noms lisibles pour les colonnes
        df['verb_name'] = df['verb'].apply(self.extract_verb) if 'verb' in df.columns else "Unknown"
        df['actor_name'] = df['actor'].apply(self.extract_actor) if 'actor' in df.columns else "Unknown"
        df['object_name'] = df['object'].apply(self.extract_object) if 'object' in df.columns else "Unknown"

        # Traitement des timestamps
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

        # Calcul des statistiques de base
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

        if 'Duration' in df.columns:
            durations_per_verbe = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration_per_verbe = {v: mean(d) for v, d in durations_per_verbe.items() if d}
        else:
            avg_duration_per_verbe = {}

        # Création des graphiques
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

        # Conversion des graphiques en HTML
        fig_html = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>{dataset_title}</h2>" + fig_html
