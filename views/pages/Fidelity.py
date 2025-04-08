import time
import pandas as pd
import pickle
import numpy as np
from scipy.stats import ks_2samp
from sklearn.preprocessing import LabelEncoder
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog, QPlainTextEdit, QApplication, QSpacerItem,
    QSizePolicy, QHBoxLayout, QComboBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdmetrics.single_column import KSComplement, TVComplement
import matplotlib.pyplot as plt

# Fonction d'encodage des catégories en nombres
def encode_categorical(df, columns):
    encoders = {}
    for col in columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders

class Fidelity(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.synthetic_data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Analyse de Fidélité"))

        self.ksc_button = QPushButton("Calculer le KS Complement")
        self.ksc_button.clicked.connect(self.calculate_ksc)
        layout.addWidget(self.ksc_button)

        self.tvc_button = QPushButton("Calculer le TV Complement")
        self.tvc_button.clicked.connect(self.calculate_tvc)
        layout.addWidget(self.tvc_button)

        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def on_data_generated(self):
        self.synthetic_data = self.main_app.pages["generate"].generated_data
        self.original_data = self.main_app.pages["open"].json_data

        self.original_data = self.ensure_dataframe(self.original_data)
        self.synthetic_data = self.ensure_dataframe(self.synthetic_data)

        # Mettre les colonnes en minuscules
        self.original_data.columns = self.original_data.columns.str.lower()
        self.synthetic_data.columns = self.synthetic_data.columns.str.lower()

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

    def convert_column_types(self, df, columns):
        for column in columns:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df

    def flatten_synthetic_data(self, synthetic_data):
        """Aplatir les données synthétiques pour correspondre à la structure de original_data."""
        if 'actions' in synthetic_data.columns:
            flattened_data = []
            for actions in synthetic_data['actions']:
                for action in actions:
                    flattened_data.append({
                        'id': action.get('id'),
                        'timestamp': action.get('timestamp'),
                        'verb': action.get('verb', {}).get('id'),
                        'actor': action.get('actor', {}).get('mbox'),
                        'object': action.get('object', {}).get('id'),
                        'duration': action.get('duration', 0.0)
                    })
            return pd.DataFrame(flattened_data)
        return synthetic_data

    def calculate_ksc(self):
        df = self.original_data
        synthetic_data = self.flatten_synthetic_data(self.synthetic_data)

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        categorical_columns = ['actor', 'verb', 'object']
        ksc_scores = {}

        df = self.convert_column_types(df, categorical_columns)
        synthetic_data = self.convert_column_types(synthetic_data, categorical_columns)

        df, _ = encode_categorical(df, categorical_columns)
        synthetic_data, _ = encode_categorical(synthetic_data, categorical_columns)

        for column in categorical_columns:
            if column in df.columns and column in synthetic_data.columns:
                ksc_score = KSComplement.compute(real_data=df[column], synthetic_data=synthetic_data[column])
                ksc_scores[column] = ksc_score
                self.results_text.appendPlainText(f"KS Complement Score pour {column} : {ksc_score:.4f}")
            else:
                self.results_text.appendPlainText(f"Colonne '{column}' manquante dans les données.")

        if ksc_scores:
            self.plot_ksc_scores(ksc_scores)

    def calculate_tvc(self):
        df = self.original_data
        synthetic_data = self.flatten_synthetic_data(self.synthetic_data)

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        categorical_columns = ['actor', 'verb', 'object']
        tvc_scores = {}

        df = self.convert_column_types(df, categorical_columns)
        synthetic_data = self.convert_column_types(synthetic_data, categorical_columns)

        df, _ = encode_categorical(df, categorical_columns)
        synthetic_data, _ = encode_categorical(synthetic_data, categorical_columns)

        for column in categorical_columns:
            if column in df.columns and column in synthetic_data.columns:
                tvc_score = TVComplement.compute(real_data=df[column], synthetic_data=synthetic_data[column])
                tvc_scores[column] = tvc_score
                self.results_text.appendPlainText(f"TV Complement Score pour {column} : {tvc_score:.4f}")
            else:
                self.results_text.appendPlainText(f"Colonne '{column}' manquante dans les données.")

        if tvc_scores:
            self.plot_tvc_scores(tvc_scores)

    def plot_ksc_scores(self, ksc_scores):
        columns = list(ksc_scores.keys())
        scores = list(ksc_scores.values())

        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, scores, color='skyblue')
        plt.title("Scores KS Complement")
        plt.xlabel("Colonnes")
        plt.ylabel("Score KS Complement")
        plt.ylim(0, 1)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval, round(yval, 4), va='bottom')

        plt.show()

    def plot_tvc_scores(self, tvc_scores):
        columns = list(tvc_scores.keys())
        scores = list(tvc_scores.values())

        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, scores, color='lightcoral')
        plt.title("Scores TV Complement")
        plt.xlabel("Colonnes")
        plt.ylabel("Score TV Complement")
        plt.ylim(0, 1)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval, round(yval, 4), va='bottom')

        plt.show()
