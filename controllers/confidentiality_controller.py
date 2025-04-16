# confidentiality_controller.py
import matplotlib.pyplot as plt
from models.confidentiality_model import ConfidentialityModel
from views.pages.confidentiality_view import ConfidentialityView
import pandas as pd

class ConfidentialityController:
    def __init__(self, main_app, view=None):
        """
        main_app doit contenir :
          - main_app.pages["generate"].generated_data (les données générées)
          - main_app.pages["open"].json_data (les données originales)
        """
        self.main_app = main_app
        self.model = ConfidentialityModel()
        self.view = view if view is not None else ConfidentialityView()
        self.connect_signals()

    def connect_signals(self):
        self.view.cramers_v_button.clicked.connect(self.calculate_cramers_v)
        self.view.dcr_button.clicked.connect(self.calculate_dcr)
        self.view.pmse_button.clicked.connect(self.calculate_pmse)

    def on_data_generated(self):
        # Récupère et prépare les données
        original = self.model.ensure_dataframe(self.main_app.pages["open"].json_data)
        synthetic = self.model.ensure_dataframe(self.main_app.pages["generate"].generated_data)
        # Convertir les noms de colonnes en minuscules
        original.columns = original.columns.str.lower()
        synthetic.columns = synthetic.columns.str.lower()
        self.original_data = original
        self.synthetic_data = synthetic

    def calculate_cramers_v(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Error: Data not available or incorrect.")
            return
        categorical_columns = ['actor', 'verb', 'object']
        results = self.model.compute_cramers_v(self.original_data, self.synthetic_data, categorical_columns)
        for col, value in results.items():
            self.view.append_result(f"Cramer's V for {col}: {value:.4f}")
        if results:
            fig = self.model.plot_cramers_v(results)
            if fig is not None:
                plt.show()

    def calculate_dcr(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Error: Data not available.")
            return
        dcr_train, dcr_holdout = self.model.compute_dcr(self.original_data, self.synthetic_data)
        self.view.append_result(f"DCR Train: {dcr_train:.4f}")
        self.view.append_result(f"DCR Holdout: {dcr_holdout:.4f}")

    def calculate_pmse(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Error: Data not available.")
            return
        try:
            pmse_value = self.model.compute_pmse(self.original_data, self.synthetic_data)
            self.view.append_result(f"pMSE: {pmse_value:.4f}")
        except Exception as e:
            self.view.append_result(f"Error calculating pMSE: {str(e)}")
