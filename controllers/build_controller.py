# build_controller.py
from models.build_model import BuildModel, TrainingThread
from views.pages.build_view import BuildView
from PyQt6.QtCore import QObject
import pandas as pd


class BuildController(QObject):
    def __init__(self, main_app, download_button, tools):
        super().__init__()
        self.main_app = main_app
        self.download_button = download_button
        self.tools = tools
        self.model_instance = BuildModel()
        self.view = BuildView(main_app, download_button, tools)

        # Connect signals from view to controller
        self.view.train_clicked.connect(self.train_model)
        self.view.save_clicked.connect(self.save_model)

    def get_data_and_mode(self):
        json_data = self.download_button.json_data
        mode = self.view.data_mode_combo.currentText()
        if json_data is None:
            self.view.show_message("Error: No data loaded. Please load a JSON file.", "error")
            return None, None
        df = self.model_instance.preprocess_data(pd.DataFrame(json_data), mode)
        return df, mode

    def extract_training_params(self):
        params = {
            "epochs": int(self.tools.epochs_edit.text()),
            "batch_size": int(self.tools.batch_size_edit.text()),
            "embedding_dim": int(self.tools.embedding_dim_edit.text()),
            "generator_dim": tuple(map(int, self.tools.generator_dim_edit.text().split(','))),
            "discriminator_dim": tuple(map(int, self.tools.discriminator_dim_edit.text().split(','))),
            "pac": int(self.tools.pac_edit.text()),
            "verbose": self.tools.verbose_combo.currentText() == "True",
            "minmax": self.tools.minmax_combo.currentText() == "True",
        }
        return params

    def train_model(self):
        df, mode = self.get_data_and_mode()
        if df is None or df.empty:
            self.view.update_output("\u274c Données invalides ou vides. Veuillez charger un fichier JSON valide.")
            return

        try:
            training_params = self.extract_training_params()
            model = self.model_instance.create_model(df, training_params)

            self.training_thread = TrainingThread(model, df)
            self.training_thread.progress_update.connect(self.view.update_output)
            self.training_thread.training_finished.connect(self.training_done)
            self.training_thread.start()
        except Exception as e:
            self.view.update_output(f"\u274c Erreur pendant l'entraînement : {e}")

    def training_done(self, trained_model):
        if trained_model is None:
            self.view.update_output("The model was not trained.")
            return

        self.model_instance.model = trained_model
        self.main_app.model_instance = trained_model
        self.view.update_output("✅ Training completed successfully!")
        self.view.enable_save()

        if hasattr(self.main_app, "pages") and "generate" in self.main_app.pages:
            self.main_app.pages["generate"].on_model_loaded(trained_model)


    def save_model(self, file_path):
        try:
            self.model_instance.save_model(file_path)
            self.view.show_message(f"Model successfully saved to {file_path}", "success")
        except Exception as e:
            self.view.show_message(f"Error while saving model: {e}", "error")
