import time
import pandas as pd
import seaborn as sns
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
        layout.addWidget(QLabel("Fidelity Analysis"))

        self.ksc_button = QPushButton("Compute the KS Complement")
        self.ksc_button.clicked.connect(self.calculate_ksc)
        layout.addWidget(self.ksc_button)

        self.tvc_button = QPushButton("Compute the TV Complement")
        self.tvc_button.clicked.connect(self.calculate_tvc)
        layout.addWidget(self.tvc_button)

        self.sequence_button = QPushButton("Check the logic of verb sequences")
        self.sequence_button.clicked.connect(self.calculate_verb_sequence_similarity)
        layout.addWidget(self.sequence_button)

        self.markov_button = QPushButton("Display the Markov transition matrix")
        self.markov_button.clicked.connect(self.plot_markov_transition_matrices)
        layout.addWidget(self.markov_button)

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
            self.results_text.appendPlainText("Error : No available data.")

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

    def calculate_verb_sequence_similarity(self):
        df_real = self.ensure_dataframe(self.original_data)
        df_synth = self.flatten_synthetic_data(self.synthetic_data)

        if df_real.empty or df_synth.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        required_cols = ['actor', 'verb', 'timestamp']
        for col in required_cols:
            if col not in df_real.columns or col not in df_synth.columns:
                self.results_text.appendPlainText(f"Erreur : Colonne manquante → {col}")
                return

        df_real = df_real.dropna(subset=required_cols).copy()
        df_synth = df_synth.dropna(subset=required_cols).copy()

        df_real['timestamp'] = pd.to_datetime(df_real['timestamp'], errors='coerce')
        df_synth['timestamp'] = pd.to_datetime(df_synth['timestamp'], errors='coerce')

        df_real = df_real.dropna(subset=['timestamp'])
        df_synth = df_synth.dropna(subset=['timestamp'])

        # 🔄 Extraire uniquement le nom du verbe (ex: 'viewed')
        def extract_verb_name(v):
            if isinstance(v, dict):
                return v.get('id', '').split('/')[-1]
            elif isinstance(v, str) and v.startswith("{"):
                try:
                    parsed = eval(v)
                    return parsed.get('id', '').split('/')[-1]
                except:
                    return v.split('/')[-1]
            elif isinstance(v, str):
                return v.split('/')[-1]
            return str(v)

        df_real['verb'] = df_real['verb'].apply(extract_verb_name)
        df_synth['verb'] = df_synth['verb'].apply(extract_verb_name)

        df_real['actor'] = df_real['actor'].astype(str)
        df_synth['actor'] = df_synth['actor'].astype(str)

        df_real.sort_values(by=['actor', 'timestamp'], inplace=True)
        df_synth.sort_values(by=['actor', 'timestamp'], inplace=True)

        real_seqs = df_real.groupby('actor')['verb'].apply(list).tolist()
        synth_seqs = df_synth.groupby('actor')['verb'].apply(list).tolist()

        def extract_bigrams(seqs):
            return [(seq[i], seq[i + 1]) for seq in seqs for i in range(len(seq) - 1)]

        real_bigrams = extract_bigrams(real_seqs)
        synth_bigrams = extract_bigrams(synth_seqs)

        from collections import Counter
        real_counter = Counter(real_bigrams)
        synth_counter = Counter(synth_bigrams)

        top_real = real_counter.most_common(10)
        top_synth = synth_counter.most_common(10)

        total_real = sum(real_counter.values())
        total_synth = sum(synth_counter.values())

        self.results_text.appendPlainText("\n🔎 Top 10 bigrams réels (normalisés) :")
        for pair, freq in top_real:
            percent = (freq / total_real) * 100 if total_real else 0
            self.results_text.appendPlainText(f"{pair} : {percent:.4f}%")

        self.results_text.appendPlainText("\n🧪 Top 10 bigrams synthétiques (normalisés) :")
        for pair, freq in top_synth:
            percent = (freq / total_synth) * 100 if total_synth else 0
            self.results_text.appendPlainText(f"{pair} : {percent:.4f}%")

        real_set = set(pair for pair, _ in top_real)
        synth_set = set(pair for pair, _ in top_synth)
        intersection = real_set & synth_set
        union = real_set | synth_set
        jaccard = len(intersection) / len(union) if union else 0.0

        self.results_text.appendPlainText(f"\n✅ Indice de similarité Jaccard (Top 10 bigrams) : {jaccard:.2f}")

    def plot_markov_transition_matrices(self):
        df_real = self.ensure_dataframe(self.original_data)
        df_synth = self.flatten_synthetic_data(self.synthetic_data)

        if df_real.empty or df_synth.empty:
            self.results_text.appendPlainText("Erreur : Données non disponibles.")
            return

        required_cols = ['actor', 'verb', 'timestamp']
        for col in required_cols:
            if col not in df_real.columns or col not in df_synth.columns:
                self.results_text.appendPlainText(f"Erreur : Colonne manquante → {col}")
                return

        df_real = df_real.dropna(subset=required_cols).copy()
        df_synth = df_synth.dropna(subset=required_cols).copy()
        df_real['timestamp'] = pd.to_datetime(df_real['timestamp'], errors='coerce')
        df_synth['timestamp'] = pd.to_datetime(df_synth['timestamp'], errors='coerce')
        df_real = df_real.dropna(subset=['timestamp'])
        df_synth = df_synth.dropna(subset=['timestamp'])

        def extract_verb_name(v):
            if isinstance(v, dict):
                return v.get('id', '').split('/')[-1]
            elif isinstance(v, str) and v.startswith("{"):
                try:
                    parsed = eval(v)
                    return parsed.get('id', '').split('/')[-1]
                except:
                    return v.split('/')[-1]
            elif isinstance(v, str):
                return v.split('/')[-1]
            return str(v)

        df_real['verb'] = df_real['verb'].apply(extract_verb_name)
        df_synth['verb'] = df_synth['verb'].apply(extract_verb_name)
        df_real['actor'] = df_real['actor'].astype(str)
        df_synth['actor'] = df_synth['actor'].astype(str)

        def compute_transition_matrix(df):
            df = df.sort_values(by=['actor', 'timestamp'])
            verb_seqs = df.groupby('actor')['verb'].apply(list)

            transitions = []
            for seq in verb_seqs:
                transitions += [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]

            trans_df = pd.DataFrame(transitions, columns=['from', 'to'])
            matrix = pd.crosstab(trans_df['from'], trans_df['to'], normalize='index')
            return matrix.fillna(0)

        real_matrix = compute_transition_matrix(df_real)
        synth_matrix = compute_transition_matrix(df_synth)

        verbs = sorted(set(real_matrix.index) | set(real_matrix.columns) |
                       set(synth_matrix.index) | set(synth_matrix.columns))

        real_matrix = real_matrix.reindex(index=verbs, columns=verbs, fill_value=0)
        synth_matrix = synth_matrix.reindex(index=verbs, columns=verbs, fill_value=0)

        # Heatmaps
        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        sns.heatmap(real_matrix, ax=axs[0], cmap="Blues", annot=False, fmt=".2f")
        axs[0].set_title("Matrice de transition (Réelle)")
        sns.heatmap(synth_matrix, ax=axs[1], cmap="Oranges", annot=False, fmt=".2f")
        axs[1].set_title("Matrice de transition (Synthétique)")
        plt.tight_layout()
        plt.show()

        # Distance globale L1
        distance = np.abs(real_matrix.values - synth_matrix.values).sum()
        self.results_text.appendPlainText(f"\nL1 divergence between transition matrices : {distance:.4f}")