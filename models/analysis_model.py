import os
from statistics import mean, stdev
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.io as pio


class AnalysisModel:

    @staticmethod
    def convert_generated_data(events_gen):
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
        return pd.DataFrame()

    @staticmethod
    def validate_dataframe(df):
        required_columns = {'id', 'timestamp', 'verb', 'actor', 'object', 'duration'}
        return required_columns.issubset(df.columns)

    @staticmethod
    def extract_name(value):
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
        return vid.split("/")[-1] if "http" in vid else vid

    @staticmethod
    def extract_actor(actor_dict):
        if not isinstance(actor_dict, dict):
            return "Unknown"
        mbox = actor_dict.get('mbox', '')
        return mbox.replace("mailto:", "") if mbox.startswith("mailto:") else mbox.split("/")[-1] if "http" in mbox else mbox

    @staticmethod
    def extract_object(object_dict):
        if not isinstance(object_dict, dict):
            return "Unknown"
        oid = object_dict.get('id', '')
        return oid.split("/")[-1] if "http" in oid else oid

    def _get_palette(self):
        return [
            "#6497b1", "#005b96", "#b3cde0", "#03396c", "#011f4b", "#7baedc", "#4a90e2", "#6A8CAF",
            "#4D6D9A", "#8FB7CC", "#A6BFE4", "#C9D9F0", "#B1C7E0", "#DDEBF7", "#7CA7C1", "#5D8AA8",
            "#9CB4CC", "#ADCBE3", "#BDD7EE", "#AAC6D8"
        ]

    def create_bar_chart(self, data, title, y_axis="Count", width=800, height=400):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        color_map = {label: self._get_palette()[i % len(self._get_palette())] for i, label in enumerate(labels)}
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

    def create_statistics_combined_chart(self, avg, min_val, max_val, std, title, width=800, height=400):
        labels = ["Average", "Min", "Max", "Std Dev"]
        values = [avg, min_val, max_val, std]
        fig = px.bar(
            x=labels,
            y=values,
            labels={"x": "Stats", "y": "Events per Actor"},
            title=title,
            width=width,
            height=height
        )
        fig.update_traces(marker_color=self._get_palette()[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_event_time_chart(self, first_event, last_event, title, width=800, height=400):
        fig = px.bar(
            x=["First Event", "Last Event"],
            y=[1, 1],
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Count"},
            title=title,
            width=width,
            height=height
        )
        fig.update_traces(textposition="outside", marker_color=self._get_palette()[:2])
        fig.update_layout(showlegend=False)
        return fig

    def create_actor_per_verb_pie_chart(self, df, title, verb_color_map=None, width=1000, height=500):
        actor_per_verb = df.groupby('verb_name')['actor_name'].nunique().to_dict()
        labels = list(actor_per_verb.keys())
        values = list(actor_per_verb.values())
        color_map = {label: self._get_palette()[i % len(self._get_palette())] for i, label in enumerate(labels)}
        fig = px.pie(
            names=labels,
            values=values,
            title=title,
            width=width,
            height=height,
            color=labels,
            color_discrete_map=color_map
        )
        return fig

    def create_object_pie_chart(self, object_counts, title, width=800, height=400):
        fig = px.pie(
            names=list(object_counts.keys()),
            values=list(object_counts.values()),
            title=title,
            width=width,
            height=height
        )
        fig.update_traces(marker=dict(colors=self._get_palette()))
        return fig

    def create_analysis_html(self, df, dataset_title, verb_color_map=None):
        if df.empty:
            return f"<h2>{dataset_title}</h2><p>No data</p>"

        df['verb_name'] = df['verb'].apply(self.extract_verb)
        df['actor_name'] = df['actor'].apply(self.extract_actor)
        df['object_name'] = df['object'].apply(self.extract_object)

        timestamps = pd.to_datetime(df['timestamp'], errors='coerce').dropna()
        first_event = timestamps.min().strftime("%Y-%m-%d %H:%M:%S") if not timestamps.empty else "N/A"
        last_event = timestamps.max().strftime("%Y-%m-%d %H:%M:%S") if not timestamps.empty else "N/A"

        verb_counts = Counter(df['verb_name'])
        object_counts = dict(Counter(df['object_name']).most_common(6))
        actor_counts = Counter(df['actor_name'])

        if actor_counts:
            actor_values = list(actor_counts.values())
            avg_events = mean(actor_values)
            min_events = min(actor_values)
            max_events = max(actor_values)
            std_events = stdev(actor_values) if len(actor_values) > 1 else 0
        else:
            avg_events = min_events = max_events = std_events = 0

        durations_per_verb = {}
        for col in ['duration', 'Duration']:
            if col in df.columns:
                grouped = df.groupby('verb_name')[col].apply(list)
                for verb, values in grouped.items():
                    durations_per_verb.setdefault(verb, []).extend(values)

        avg_duration_per_verb = {}
        for verb, durations in durations_per_verb.items():
            cleaned = [float(d) for d in durations if isinstance(d, (int, float)) or (isinstance(d, str) and d.replace('.', '', 1).isdigit())]
            if cleaned:
                avg_duration_per_verb[verb] = mean(cleaned)

        fig_list = []
        prefix = f"[{dataset_title}] "

        fig_list.append(self.create_bar_chart(verb_counts, prefix + "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts, prefix + "Object Distribution"))
        fig_list.append(self.create_event_time_chart(first_event, last_event, prefix + "Event Timestamps"))
        fig_list.append(self.create_statistics_combined_chart(avg_events, min_events, max_events, std_events, prefix + "Events per Actor"))

        if avg_duration_per_verb:
            fig_list.append(self.create_bar_chart(avg_duration_per_verb, prefix + "Average Duration per Verb", y_axis="Avg duration (s)"))

        if actor_counts:
            fig_list.append(self.create_actor_per_verb_pie_chart(df, prefix + "Actors per Verb", verb_color_map))

        fig_html = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>{dataset_title}</h2>" + fig_html
