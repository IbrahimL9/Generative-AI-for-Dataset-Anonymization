from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from collections import Counter
from datetime import datetime

class Inspect(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.initUI()
        # Connecter le signal file_loaded pour mettre à jour les statistiques dès que le fichier est téléchargé
        self.download_button.file_loaded.connect(self.updateStatistics)

    def initUI(self):
        self.layout = QVBoxLayout()

        # Titre de la page Inspect
        title = QLabel("Statistics")
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # Label pour afficher les statistiques
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Montserrat", 14))
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.stats_label)

        # Spacer pour occuper l'espace restant
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(self.layout)

        # Tentative initiale de mise à jour (au cas où les données seraient déjà disponibles)
        self.updateStatistics()

    def updateStatistics(self):
        # Pour le débogage, vous pouvez activer la ligne suivante :
        # print("updateStatistics appelée, json_data =", getattr(self.download_button, 'json_data', None))
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            data = self.download_button.json_data
            events = data.get("events", [])
            if not events:
                self.stats_label.setText("Aucun événement disponible pour afficher les statistiques.")
                return

            # Extraction des statistiques
            total_events = len(events)
            unique_actors = set(event.get("actor") for event in events)
            unique_verbs = set(event.get("verb") for event in events)
            unique_objects = set(event.get("object") for event in events)
            num_actors = len(unique_actors)
            num_verbs = len(unique_verbs)
            num_objects = len(unique_objects)

            # Calculs complémentaires
            actor_counts = Counter(event.get("actor") for event in events)
            verb_counts = Counter(event.get("verb") for event in events)
            avg_events_per_actor = total_events / num_actors if num_actors > 0 else 0
            avg_events_per_verb = total_events / num_verbs if num_verbs > 0 else 0

            # Analyse des timestamps
            timestamps = []
            for event in events:
                ts = event.get("timestamp")
                if ts:
                    try:
                        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
                        timestamps.append(dt)
                    except Exception:
                        pass
            timestamps.sort()
            first_event = timestamps[0].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"
            last_event = timestamps[-1].strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"

            stats_text = (
                f"Total Events: {total_events}\n"
                f"Unique Actors: {num_actors}\n"
                f"Unique Verbs: {num_verbs}\n"
                f"Unique Objects: {num_objects}\n\n"
                f"Time Analysis:\n"
                f"  - First Event: {first_event}\n"
                f"  - Last Event: {last_event}\n\n"
                f"Events per Actor: Average {avg_events_per_actor:.2f}\n"
                f"Events per Verb: Average {avg_events_per_verb:.2f}"
            )
            self.stats_label.setText(stats_text)
        else:
            self.stats_label.setText("Aucun fichier généré. Veuillez télécharger un fichier d'abord.")
