# generate_controller.py
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from models.generate_model import GenerateModel


class GenerateController:
    def __init__(self, main_app, view):
        """
        - main_app est votre application principale qui contient (entre autres) le modèle entraîné et la propriété json_data.
        - view est une instance de GenerateView.
        """
        self.main_app = main_app
        self.view = view
        self.model = GenerateModel()
        self.generated_data = None
        self.session_data = None

        # Connecter le bouton de génération à la méthode generate_data.
        self.view.generate_button.clicked.connect(self.generate_data)

    def check_enable_generate_button(self):
        # Activer le bouton si le modèle est chargé et entraîné, et si json_data est disponible.
        if self.main_app.model_instance and getattr(self.main_app.model_instance, "fitted",
                                                    False) and self.main_app.json_data is not None:
            self.view.generate_button.setEnabled(True)
        else:
            self.view.generate_button.setEnabled(False)

    def generate_data(self):
        # Vérifier que le modèle est entraîné
        if self.main_app.model_instance is None or not getattr(self.main_app.model_instance, "fitted", False):
            QMessageBox.warning(self.view, "Error", "Please train a model before generating data.")
            return
        try:
            num_records = int(self.view.records_input.text())
        except ValueError:
            QMessageBox.warning(self.view, "Error", "Please enter a valid number.")
            return

        self.view.show_progress(True)
        # Utiliser un timer pour simuler un délai et laisser l'UI afficher la barre de progression
        QTimer.singleShot(2000, lambda: self.finish_generation(num_records))

    def finish_generation(self, num_records):
        try:
            self.view.show_progress(False)
            trained_model = self.main_app.model_instance
            if trained_model:
                generated_data, session_data = self.model.generate(
                    trained_model,
                    num_records,
                    self.view.users_input.text()
                )

                self.generated_data = generated_data
                self.session_data = session_data
                self.main_app.session_data = session_data  # Mettre à jour la session globalement si besoin

                # Afficher un message de succès
                if hasattr(session_data, 'columns') and "actions" in session_data.columns:
                    msg = f"{len(session_data)} generated sessions."
                else:
                    msg = f"{num_records} generated actions."
                self.view.show_message(msg, "success")
            else:
                QMessageBox.warning(self.view, "Error", "Model is not available.")
        except Exception as e:
            self.view.show_message(f"Error while generating: {str(e)}", "error")

        self.view.generated_data = generated_data
        self.view.data_generated_signal.emit(generated_data)  # ✅ EMISSION FINALE ICI

    def on_model_loaded(self, model):
        self.main_app.model_instance = model
        self.view.on_model_loaded(model)
        self.check_enable_generate_button()
