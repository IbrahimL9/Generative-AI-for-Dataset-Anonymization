import os
import pandas as pd
from statistics import mean, stdev
from collections import Counter
import plotly.express as px
import plotly.io as pio


class InspectModel:
    def extract_name(self, value):
        if isinstance(value, str):
            if value.startswith("mailto:"):
                return value.replace("mailto:", "")
            elif value.startswith("http"):
                return value.split("/")[-1]
        return str(value)

    def convert_to_duration(self, events):
        if not events:
            return events

        df = pd.DataFrame(events)
        if 'timestamp' not in df.columns:
            return events

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['actor_name'] = df['actor'].apply(
            lambda a: self.extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a))
        df = df.sort_values(by=['actor_name', 'timestamp'])
        df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds().fillna(0)

        for idx, dur in zip(df.index, df['Duration']):
            events[idx]['Duration'] = float(dur)

        return events

    def create_html_report(self, verb_counts, object_counts,
                           first_event, last_event,
                           avg_events, min_events, max_events,
                           avg_value, std_value,
                           actor_counts=None, avg_duration_per_verb=None,
                           df=None):
        fig_list = []

        # Graphiques principaux
        fig_list.append(self.create_bar_chart(verb_counts, "Most Used Verbs"))
        fig_list.append(self.create_object_pie_chart(object_counts))
        fig_list.append(self.create_event_time_chart(first_event, last_event))
        fig_list.append(self.create_histogram(avg_events, min_events, max_events, "Events per Actor"))
        fig_list.append(self.create_statistics_bar_chart(avg_value, std_value))

        # Graphiques additionnels
        if avg_duration_per_verb:
            fig_list.append(
                self.create_bar_chart(avg_duration_per_verb, "Average Duration per Verb", y_axis="Avg Duration (s)"))
        if actor_counts and df is not None:
            actor_per_verb = df.groupby('verb_name')['actor_name'].nunique().to_dict()
            fig_list.append(self.create_actor_per_verb_pie_chart(actor_per_verb))

        html_content = "".join([pio.to_html(fig, full_html=False) for fig in fig_list])
        return f"<h2>STATISTICS REPORT</h2>" + html_content

    def create_bar_chart(self, data, title, y_axis="Count"):
        labels = list(data.keys())
        values = [data[label] for label in labels]
        fig = px.bar(x=labels, y=values, labels={"x": "Category", "y": y_axis}, title=title, width=1000, height=500)
        colors = ['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500']
        fig.update_traces(marker_color=colors[:len(labels)])
        fig.update_layout(showlegend=False)
        return fig

    def create_histogram(self, avg_value, min_value, max_value, title):
        labels = ["Average", "Min", "Max"]
        values = [avg_value, min_value, max_value]
        fig = px.bar(x=labels, y=values, labels={"x": "Stats", "y": "Events per Actor"}, title=title, width=1000, height=500)
        fig.update_traces(marker_color=['#636EFA', '#EF553B', '#00CC96'])
        fig.update_layout(showlegend=False)
        return fig

    def create_event_time_chart(self, first_event, last_event):
        fig = px.bar(
            x=["First Event", "Last Event"],
            y=[1, 1],
            text=[first_event, last_event],
            labels={"x": "Event Type", "y": "Timestamp"},
            title="Event Timestamps",
            width=1000,
            height=500
        )
        fig.update_traces(marker_color=['#636EFA', '#EF553B'], textposition="outside")
        fig.update_layout(showlegend=False)
        return fig

    def create_statistics_bar_chart(self, avg_value, std_value):
        fig = px.bar(
            x=["Average", "Std Dev"],
            y=[avg_value, std_value],
            labels={"x": "Stats", "y": "Value"},
            title="Average & Std Dev of Events per Actor",
            width=1000,
            height=500
        )
        fig.update_traces(marker_color=['#636EFA', '#EF553B'])
        fig.update_layout(showlegend=False)
        return fig

    def create_actor_per_verb_pie_chart(self, actor_per_verb):
        fig = px.pie(
            names=list(actor_per_verb.keys()),
            values=list(actor_per_verb.values()),
            title="Number of Distinct Actors per Verb",
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
        fig.update_traces(marker_colors=['#636EFA', '#EF553B', '#00CC96', '#FFD700', '#FF1493', '#32CD32', '#FFA500'])
        return fig
