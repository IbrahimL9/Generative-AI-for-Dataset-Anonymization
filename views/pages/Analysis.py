import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QPlainTextEdit, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import pairwise_distances, mean_squared_error
from sklearn.ensemble import RandomForestClassifier
from sdv.metadata import Metadata
from sdv.single_table import CTGANSynthesizer

class Analysis(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.synthetic_data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("Analysis")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.cramers_v_button = QPushButton("Calculer V de Cramer")
        self.cramers_v_button.clicked.connect(self.calculate_cramers_v)
        layout.addWidget(self.cramers_v_button)

        self.dcr_button = QPushButton("Calculer DCR")
        self.dcr_button.clicked.connect(self.calculate_dcr)
        layout.addWidget(self.dcr_button)

        self.pmse_button = QPushButton("Calculer pMSE")
        self.pmse_button.clicked.connect(self.calculate_pmse)
        layout.addWidget(self.pmse_button)

        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def on_data_generated(self):
        self.synthetic_data = self.main_app.pages["generate"].generated_data
        self.original_data = self.main_app.pages["open"].json_data

        self.original_data = self.ensure_dataframe(self.original_data)
        self.synthetic_data = self.ensure_dataframe(self.synthetic_data)

        # Mettre les noms des colonnes en minuscules pour correspondre aux données
        self.original_data.columns = self.original_data.columns.str.lower()
        self.synthetic_data.columns = self.synthetic_data.columns.str.lower()

        print("Colonnes dans original_data:", self.original_data.columns)
        print("Colonnes dans synthetic_data:", self.synthetic_data.columns)

        if self.original_data.empty or self.synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles ou incorrectes.")

    def ensure_dataframe(self, data):
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def calculate_cramers_v(self):
        def cramers_v(x, y):
            # Convertir les valeurs en chaînes de caractères pour éviter les erreurs
            x = x.astype(str)
            y = y.astype(str)

            confusion_matrix = pd.crosstab(x, y)
            chi2 = chi2_contingency(confusion_matrix)[0]
            n = confusion_matrix.sum().sum()
            phi2 = chi2 / n
            r, k = confusion_matrix.shape
            phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
            rcorr = r - ((r - 1) ** 2) / (n - 1)
            kcorr = k - ((k - 1) ** 2) / (n - 1)
            return np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))

        df = self.original_data
        synthetic_data = self.synthetic_data

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        categorical_columns = ['actor', 'verb', 'object']
        results = {}
        for column in categorical_columns:
            if column in df.columns and column in synthetic_data.columns:
                v_cramer_value = cramers_v(df[column], synthetic_data[column])
                results[column] = v_cramer_value
                self.results_text.appendPlainText(f"V de Cramer pour {column}: {v_cramer_value:.4f}")
            else:
                self.results_text.appendPlainText(f"Colonne '{column}' manquante dans les données.")

        if results:
            self.plot_cramers_v(results)

    def plot_cramers_v(self, results):
        columns = list(results.keys())
        cramer_values = list(results.values())

        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, cramer_values, color=['blue', 'orange', 'green'])
        plt.axhline(y=0.1, color='r', linestyle='--', label='Seuil souhaité')
        plt.title('Valeurs du V de Cramer')
        plt.xlabel('Variables')
        plt.ylabel('Valeur du V de Cramer')
        plt.ylim(0, max(cramer_values) + 0.05)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval, round(yval, 4), va='bottom')

        plt.legend()
        plt.show()

    def calculate_dcr(self):
        df = self.original_data
        synthetic_data = self.synthetic_data

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        # Aligner les colonnes entre les données originales et synthétiques
        common_columns = list(set(df.columns).intersection(synthetic_data.columns))
        df = df[common_columns]
        synthetic_data = synthetic_data[common_columns]

        train_df, holdout_df = train_test_split(df, test_size=0.5)

        # Convertir les dictionnaires en chaînes de caractères
        train_df = train_df.apply(lambda x: x.map(str) if x.dtype == 'object' else x)
        synthetic_data = synthetic_data.apply(lambda x: x.map(str) if x.dtype == 'object' else x)

        # Création correcte des métadonnées
        metadata = Metadata()

        try:
            # Définir explicitement les métadonnées avec la syntaxe correcte
            metadata.add_table(
                name='data',  # Nom de la table
                fields={
                    'id': {'type': 'id'},  # Définir 'id' comme type 'id'
                    'timestamp': {'type': 'datetime'},  # Définir 'timestamp' comme 'datetime'
                    'verb': {'type': 'string'},  # 'verb' comme type 'string'
                    'actor': {'type': 'string'},  # 'actor' comme type 'string'
                    'object': {'type': 'string'}  # 'object' comme type 'string'
                }
            )

            # Afficher les colonnes détectées dans les métadonnées
            detected_columns = metadata.tables['data'].columns.keys()
            self.results_text.appendPlainText(f"Colonnes détectées dans les métadonnées: {detected_columns}")

            # Initialisation du modèle CTGAN avec les métadonnées
            ctgan = CTGANSynthesizer(metadata, epochs=200)
            ctgan.fit(train_df)
            synthetic_train = ctgan.sample(len(df))

            # Encodage des données pour la comparaison
            train_encoded = pd.get_dummies(train_df)
            holdout_encoded = pd.get_dummies(holdout_df)
            synthetic_encoded = pd.get_dummies(synthetic_train)

            # Aligner les colonnes entre train_encoded, holdout_encoded, et synthetic_encoded
            common_columns = set(train_encoded.columns) & set(holdout_encoded.columns) & set(synthetic_encoded.columns)
            train_encoded = train_encoded[list(common_columns)]
            holdout_encoded = holdout_encoded[list(common_columns)]
            synthetic_encoded = synthetic_encoded[list(common_columns)]

            # Vérification si les colonnes sont bien alignées
            print("Colonnes de train_encoded:", train_encoded.columns)
            print("Colonnes de holdout_encoded:", holdout_encoded.columns)
            print("Colonnes de synthetic_encoded:", synthetic_encoded.columns)

            def calculate_dcr(synthetic, reference):
                distances = pairwise_distances(synthetic, reference, metric='hamming')
                min_distances = distances.min(axis=1)
                return min_distances

            # Calculer le DCR
            dcr_train = calculate_dcr(synthetic_encoded, train_encoded)
            dcr_holdout = calculate_dcr(synthetic_encoded, holdout_encoded)

            self.results_text.appendPlainText(f"DCR Train: {dcr_train.mean()}")
            self.results_text.appendPlainText(f"DCR Holdout: {dcr_holdout.mean()}")

        except Exception as e:
            self.results_text.appendPlainText(f"Erreur lors du calcul du DCR : {str(e)}")

    def calculate_pmse(self):
        df = self.original_data
        synthetic_data = self.synthetic_data

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        # Combine les données originales et synthétiques, ajout d'une colonne 'origin'
        combined_df = pd.concat([df.assign(origin=0), synthetic_data.assign(origin=1)])

        # Convertir toutes les colonnes non hashables (comme dict) en chaînes de caractères
        for column in combined_df.columns:
            if combined_df[column].apply(lambda x: isinstance(x, dict)).any():
                # Convertir les dictionnaires en chaînes de caractères
                combined_df[column] = combined_df[column].apply(lambda x: str(x) if isinstance(x, dict) else x)

        # Création des variables dummies (one-hot encoding)
        try:
            X = pd.get_dummies(combined_df.drop('origin', axis=1))
            y = combined_df['origin']

            # Séparer en données d'entraînement et de test
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, stratify=y)

            # Entraînement du modèle RandomForestClassifier
            classifier = RandomForestClassifier()
            classifier.fit(X_train, y_train)

            # Prédictions de probabilité
            y_pred_prob = classifier.predict_proba(X_test)[:, 1]

            # Calcul du pMSE
            pmse_value = mean_squared_error(y_test, y_pred_prob)
            self.results_text.appendPlainText(f"pMSE: {pmse_value:.4f}")

        except Exception as e:
            self.results_text.appendPlainText(f"Erreur lors du calcul du pMSE : {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Analysis(None)
    window.show()
    # Utiliser QTimer pour éviter de bloquer la boucle d'événements
    QTimer.singleShot(0, app.exec)
