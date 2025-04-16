# save_controller.py
from PyQt6.QtWidgets import QMessageBox
from models.save_model import SaveModel


class SaveController:
    def __init__(self, main_app, view):
        """
        main_app est l'application principale (pour accéder à main_app.pages["generate"].generated_data)
        view est une instance de SaveView.
        """
        self.main_app = main_app
        self.view = view
        self.model = SaveModel()

        # Connecter les boutons de la vue aux méthodes du contrôleur
        self.view.save_button.clicked.connect(self.save_data)
        self.view.display_button.clicked.connect(self.display_data)

    def on_data_generated(self):
        self.view.on_data_generated()

    def display_data(self):
        generated_data = self.main_app.pages["generate"].generated_data
        if generated_data is None:
            QMessageBox.warning(self.view, "Error", "No data found.")
            return

        data_to_display = self.model.prepare_data(generated_data)
        self.view.display_data(data_to_display)

    def save_data(self):
        generated_data = self.main_app.pages["generate"].generated_data
        if generated_data is None:
            QMessageBox.warning(self.view, "Error", "No data found.")
            return

        data_to_save = self.model.prepare_data(generated_data)
        file_name = self.view.get_save_file_name()
        if not file_name:
            return  # Annulation par l'utilisateur

        try:
            self.model.save_data(file_name, data_to_save)
            self.view.show_message(f"Data successfully saved to {file_name}", "success")
        except Exception as e:
            self.view.show_message(f"Error saving data: {e}", "error")
