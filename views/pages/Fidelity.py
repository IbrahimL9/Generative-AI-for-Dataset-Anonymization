from sdmetrics.single_column import KSComplement
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QPlainTextEdit
import pandas as pd

class Fidelity(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app  # Référence à l'application principale
        self.synthetic_data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Titre
        layout.addWidget(QLabel("Fidelity Analysis"))

        # Ajouter les boutons
        self.ksc_button = QPushButton("Calculate KS Complement")
        self.ksc_button.clicked.connect(self.calculate_ksc)
        layout.addWidget(self.ksc_button)

        # Zone de texte pour afficher les résultats
        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def on_data_generated(self):
        """Référence aux données générées et originales après leur chargement."""
        self.synthetic_data = self.main_app.pages["generate"].generated_data
        self.original_data = self.main_app.pages["open"].json_data

        self.original_data = self.ensure_dataframe(self.original_data)
        self.synthetic_data = self.ensure_dataframe(self.synthetic_data)

        # Mise en minuscules des colonnes
        self.original_data.columns = self.original_data.columns.str.lower()
        self.synthetic_data.columns = self.synthetic_data.columns.str.lower()

        if self.original_data.empty or self.synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available or incorrect.")

    def ensure_dataframe(self, data):
        """Convertit les données en DataFrame si nécessaire."""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def convert_column_types(self, df, columns):
        """Convertit les colonnes en types compatibles (str ou numérique)."""
        for column in columns:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df

    def calculate_ksc(self):
        """Calcul et affichage du score KS Complement pour chaque colonne."""
        df = self.original_data
        synthetic_data = self.synthetic_data

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available.")
            return

        categorical_columns = ['actor', 'verb', 'object']  # Remplacer avec les colonnes que tu veux comparer
        ksc_scores = {}

        # Convertir les colonnes en types compatibles
        df = self.convert_column_types(df, categorical_columns)
        synthetic_data = self.convert_column_types(synthetic_data, categorical_columns)

        # Calcul du KS Complement pour chaque colonne
        for column in categorical_columns:
            if column in df.columns and column in synthetic_data.columns:
                ksc_score = KSComplement.compute(real_data=df[column], synthetic_data=synthetic_data[column])
                ksc_scores[column] = ksc_score
                self.results_text.appendPlainText(f"KS Complement Score for {column}: {ksc_score:.4f}")
            else:
                self.results_text.appendPlainText(f"Column '{column}' missing in data.")

        # Si on a calculé des scores, les afficher
        if ksc_scores:
            self.plot_ksc_scores(ksc_scores)

    def plot_ksc_scores(self, ksc_scores):
        """Affiche un graphique des scores KS Complement."""
        import matplotlib.pyplot as plt

        columns = list(ksc_scores.keys())
        scores = list(ksc_scores.values())

        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, scores, color='skyblue')
        plt.title("KS Complement Scores")
        plt.xlabel("Columns")
        plt.ylabel("KS Complement Score")
        plt.ylim(0, 1)  # Les scores de KS complement sont entre 0 et 1

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval, round(yval, 4), va='bottom')

        plt.show()