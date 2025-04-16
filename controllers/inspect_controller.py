import os
import pandas as pd
from PyQt6.QtCore import QTimer
from models.inspect_model import InspectModel
from views.pages.inspect_view import InspectView
from statistics import mean, stdev
from collections import Counter


class InspectController:
    def __init__(self, download_button, main_app, view=None):
        self.download_button = download_button
        self.main_app = main_app
        self.model = InspectModel()
        self.view = view if view is not None else InspectView()

    def schedule_update(self):
        self.view.show_loading_message()
        QTimer.singleShot(300, self.update_statistics)

    def update_statistics(self):
        print("📊 InspectController: update_statistics()")
        df = getattr(self.main_app, 'processed_dataframe', None)

        if df is None or df.empty:
            data = self.download_button.json_data
            if not data:
                print("❌ No JSON data available.")
                return
            events = sum(data, []) if isinstance(data[0], list) else data
            events = self.model.convert_to_duration(events)
            df = pd.DataFrame(events)
            self.main_app.processed_dataframe = df

        if df.empty:
            print("❌ DataFrame is empty.")
            return

        self.view.clear_report()

        # Enrichir le DataFrame avec des colonnes lisibles
        df['verb_name'] = df['verb'].apply(lambda v: self.model.extract_name(v.get('id')) if isinstance(v, dict) else str(v))
        df['actor_name'] = df['actor'].apply(lambda a: self.model.extract_name(a.get('mbox')) if isinstance(a, dict) else str(a))
        df['object_name'] = df['object'].apply(lambda o: self.model.extract_name(o.get('id')) if isinstance(o, dict) else str(o))

        timestamps = pd.to_datetime(df.get('timestamp'), errors='coerce').dropna()
        first_event = timestamps.min().strftime("%Y-%m-%d %H:%M:%S") if not timestamps.empty else "N/A"
        last_event = timestamps.max().strftime("%Y-%m-%d %H:%M:%S") if not timestamps.empty else "N/A"

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

        if 'Duration' in df.columns:
            durations_per_verb = df.groupby('verb_name')['Duration'].apply(list)
            avg_duration_per_verb = {v: mean(d) for v, d in durations_per_verb.items() if d}
        else:
            avg_duration_per_verb = {}

        # Générer le HTML
        html = self.model.create_html_report(
            verb_counts, object_counts,
            first_event, last_event,
            avg_events, min_events, max_events,
            avg_events, std_events,
            actor_counts=actor_counts,
            avg_duration_per_verb=avg_duration_per_verb,
            df=df  # requis pour les graphiques détaillés dans model
        )

        # Sauvegarder & afficher
        html_path = os.path.abspath("all_charts_report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        self.view.display_report(html_path)
