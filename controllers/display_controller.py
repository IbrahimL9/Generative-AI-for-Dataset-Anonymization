from PyQt6.QtCore import QThread
from models.display_model import UpdateWorker
from views.pages.display_view import DisplayView


class DisplayController:
    def __init__(self, main_app, download_button):
        self.main_app = main_app
        self.download_button = download_button
        self.view = DisplayView(download_button, main_app)

        # Connecte le bouton "Apply Filter" à l'action de filtrage
        self.view.filter_button.clicked.connect(self.apply_filter)

        # Drapeau pour éviter rechargement multiple
        self.data_loaded_once = False

    def get_view(self):
        return self.view

    def load_data(self):

        if not hasattr(self.download_button, "json_data") or not self.download_button.json_data:
            self.view.clear_table()
            return
        print(f"📄 JSON data: {self.download_button.json_data[:1]}")  # affiche un seul élément

        self.thread = QThread()
        self.worker = UpdateWorker(self.download_button.json_data)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)

        self.thread.start()

    def on_data_loaded(self, events, df):
        print("✅ DisplayController: on_data_loaded called")

        self.view.show_data(events, df)

    def on_error(self, err_msg):
        print(f"[DisplayController] Error loading data: {err_msg}")
        self.view.show_error(err_msg)

    def apply_filter(self):
        if not self.download_button.json_data:
            self.view.show_error("No data loaded.")
            return

        events = sum(self.download_button.json_data, []) if isinstance(self.download_button.json_data[0], list) else self.download_button.json_data

        selected_actor = self.view.actor_combobox.currentText() if self.view.actor_checkbox.isChecked() else ""
        selected_verb = self.view.verb_combobox.currentText() if self.view.verb_checkbox.isChecked() else ""
        max_events = self.view.number_input.value()

        filtered = []
        for e in events:
            actor = self.view.extract_name(e.get("actor", {}).get("mbox", ""))
            verb = self.view.extract_name(e.get("verb", {}).get("id", ""))
            if (not selected_actor or selected_actor.lower() == actor.lower()) and \
               (not selected_verb or selected_verb.lower() == verb.lower()):
                filtered.append(e)

        if max_events > 0:
            filtered = filtered[:max_events]

        if not filtered:
            self.view.show_error("No events found for selected filters.")
        else:
            self.view.populate_table(filtered)
