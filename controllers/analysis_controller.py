# analysis_controller.py
import os
import pandas as pd
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from models.analysis_model import AnalysisModel
from views.pages.analysis_view import AnalysisView

class AnalysisController:
    def __init__(self, main_app, view=None):
        """
        main_app : Référence à l'application principale, qui doit contenir
                   - main_app.session_data
                   - main_app.processed_dataframe (les données originales)
                   - main_app.pages["generate"].generated_data (les données générées)
        view : instance de AnalysisView (si None, une nouvelle sera créée)
        """
        self.main_app = main_app
        self.model = AnalysisModel()
        self.view = view if view is not None else AnalysisView()
        self.html_file_path = os.path.abspath("comparative_analysis.html")
        self.analysis_generated = False

        # Pour déclencher l'analyse dès l'affichage de la vue :
        self.view.showEvent = self._wrapped_showEvent(self.view.showEvent)

    def _wrapped_showEvent(self, original_show_event):
        # On crée une fonction wrapper pour lancer runAnalysis après l'affichage
        def new_show_event(event):
            original_show_event(event)
            if not self.analysis_generated:
                self.view.show_loading_screen()
                QTimer.singleShot(300, self.run_analysis)
        return new_show_event

    def run_analysis(self):
        print("Running analysis...")
        # 1) Récupérer session_data depuis main_app
        session_data = self.main_app.session_data

        # 2) Récupérer le DataFrame original
        df_original = getattr(self.main_app, "processed_dataframe", None)
        if df_original is None or df_original.empty:
            label = self._create_label("No original DataFrame found. Please load a file in 'Display' first.")
            self.view.scroll_layout.addWidget(label)
            return

        # 3) Récupérer les données générées depuis la page Generate
        generate_page = self.main_app.pages.get("generate", None)
        if generate_page is None:
            label = self._create_label("No generated data found. Please generate data in 'Generate' first.")
            self.view.scroll_layout.addWidget(label)
            return

        events_gen = generate_page.generated_data
        if isinstance(events_gen, pd.DataFrame) and events_gen.empty:
            label = self._create_label("Generated data is empty. Please generate data in 'Generate' first.")
            self.view.scroll_layout.addWidget(label)
            return
        elif isinstance(events_gen, list) and not events_gen:
            label = self._create_label("Generated data list is empty. Please generate data in 'Generate' first.")
            self.view.scroll_layout.addWidget(label)
            return

        # Convertir les données générées en DataFrame via le modèle
        df_generated = self.model.convert_generated_data(events_gen)

        if not self.model.validate_dataframe(df_generated):
            label = self._create_label("Generated data structure is not compatible with original data.")
            self.view.scroll_layout.addWidget(label)
            return

        # Déterminer si on a des sessions
        is_session_data = hasattr(session_data, "columns") and "actions" in session_data.columns

        # Construire la map de couleurs globale pour les verbes
        all_verbs_set = set()
        if 'verb' in df_original.columns:
            df_original['verb_name'] = df_original['verb'].apply(self.model.extract_verb)
            all_verbs_set.update(df_original['verb_name'])
        if 'verb' in df_generated.columns:
            df_generated['verb_name'] = df_generated['verb'].apply(self.model.extract_verb)
            all_verbs_set.update(df_generated['verb_name'])

        color_palette = [
            '#636EFA', '#EF553B', '#00CC96', '#FFD700',
            '#FF1493', '#32CD32', '#FFA500', '#8A2BE2',
            '#FF4500', '#00CED1'
        ]
        verb_color_map = {verb: color_palette[i % len(color_palette)] for i, verb in enumerate(sorted(all_verbs_set))}

        # Générer le rapport HTML
        if is_session_data:
            all_session_data = []
            for row in session_data['actions']:
                if isinstance(row, list) and all(isinstance(action, dict) for action in row):
                    all_session_data.extend(row)
                else:
                    print("Invalid 'actions' format in session_data")
            df_all_sessions = pd.DataFrame(all_session_data)

            html_original = self.model.create_analysis_html(df_original, "ORIGINAL DATA", verb_color_map)
            html_all_sessions = self.model.create_analysis_html(df_all_sessions, "GENERATED SESSION DATA", verb_color_map)

            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_all_sessions}</div>
            </div>
            """
        else:
            html_original = self.model.create_analysis_html(df_original, "ORIGINAL DATA", verb_color_map)
            html_generated = self.model.create_analysis_html(df_generated, "GENERATED ACTION DATA", verb_color_map)
            final_html = f"""
            <div style="display: flex; flex-direction: row; justify-content: space-around;">
                <div style="flex: 1; margin: 10px;">{html_original}</div>
                <div style="flex: 1; margin: 10px;">{html_generated}</div>
            </div>
            """

        with open(self.model.__class__.__module__ + "/../" + "comparative_analysis.html", "w", encoding="utf-8") as f:
            f.write(final_html)

        # Charger le rapport dans la vue
        self.view.load_report(os.path.abspath("comparative_analysis.html"))
        self.analysis_generated = True

    def _create_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Montserrat", 14))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
