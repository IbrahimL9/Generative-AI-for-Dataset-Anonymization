from datetime import datetime
from statistics import mean, stdev
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


def extract_name(value):
    """Extraire un nom lisible à partir d’un mailto ou URL."""
    if isinstance(value, str):
        if value.startswith("mailto:"):
            return value.replace("mailto:", "")
        elif value.startswith("http"):
            return value.split("/")[-1]
    return str(value)


class UpdateWorker(QObject):
    finished = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, data):
        super().__init__()
        self.data = data

    @pyqtSlot()
    def run(self):
        try:
            # Aplatir les événements si c’est une liste de listes
            events = sum(self.data, []) if isinstance(self.data[0], list) else self.data
            df = pd.DataFrame(events)

            if df.empty or 'timestamp' not in df.columns or 'actor' not in df.columns:
                self.finished.emit(events, df)
                return

            # Convertir les timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            # Extraire les noms d'acteurs
            df['actor_name'] = df['actor'].apply(
                lambda a: extract_name(a.get('mbox', '')) if isinstance(a, dict) else str(a)
            )

            # Trier les événements par acteur et temps
            df = df.sort_values(by=['actor_name', 'timestamp'])

            # Calcul des durées
            session_gap = 300  # 5 minutes
            estimated_duration = 60  # valeur par défaut

            df['Duration'] = df.groupby('actor_name')['timestamp'].diff().dt.total_seconds()
            df['Duration'] = df['Duration'].fillna(estimated_duration)
            df.loc[df['Duration'] > session_gap, 'Duration'] = estimated_duration

            # Forcer la dernière action à estimated_duration
            last_indices = df.groupby('actor_name').tail(1).index
            df.loc[last_indices, 'Duration'] = estimated_duration

            # Injecter dans les objets events
            for i, d in enumerate(df['Duration']):
                events[i]['Duration'] = float(d)

            self.finished.emit(events, df)

        except Exception as e:
            self.error.emit(f"❌ Error in UpdateWorker: {str(e)}")
