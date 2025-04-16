# fidelity_model.py
import pandas as pd
import numpy as np
from statistics import mean, stdev
from collections import Counter
from sklearn.preprocessing import LabelEncoder
from sdmetrics.single_column import KSComplement, TVComplement
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import pairwise_distances, mean_squared_error
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def encode_categorical(df, columns):
    encoders = {}
    for col in columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders


class FidelityModel:
    # --- Fonctions de conversion et préparation des données ---
    @staticmethod
    def ensure_dataframe(data):
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    @staticmethod
    def flatten_synthetic_data(synthetic_data):
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

    @staticmethod
    def convert_column_types(df, columns):
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df

    # --- Fonctions d'encodage ---
    @staticmethod
    def encode_categorical(df, columns):
        return encode_categorical(df, columns)

    # --- Calcul du KS Complement ---
    def compute_ksc(self, df_original, df_synthetic, categorical_columns=['actor', 'verb', 'object']):
        ksc_scores = {}
        for col in categorical_columns:
            if col in df_original.columns and col in df_synthetic.columns:
                score = KSComplement.compute(real_data=df_original[col], synthetic_data=df_synthetic[col])
                ksc_scores[col] = score
        return ksc_scores

    # --- Calcul du TV Complement ---
    def compute_tvc(self, df_original, df_synthetic, categorical_columns=['actor', 'verb', 'object']):
        tvc_scores = {}
        for col in categorical_columns:
            if col in df_original.columns and col in df_synthetic.columns:
                score = TVComplement.compute(real_data=df_original[col], synthetic_data=df_synthetic[col])
                tvc_scores[col] = score
        return tvc_scores

    # --- Analyse de séquence de verbes (bigrams) ---
    def compute_verb_sequence_similarity(self, df_real, df_synth):
        # On suppose que df_real et df_synth contiennent les colonnes 'actor', 'verb' et 'timestamp'
        df_real = df_real.dropna(subset=['actor', 'verb', 'timestamp']).copy()
        df_synth = df_synth.dropna(subset=['actor', 'verb', 'timestamp']).copy()

        df_real['timestamp'] = pd.to_datetime(df_real['timestamp'], errors='coerce')
        df_synth['timestamp'] = pd.to_datetime(df_synth['timestamp'], errors='coerce')
        df_real = df_real.dropna(subset=['timestamp'])
        df_synth = df_synth.dropna(subset=['timestamp'])

        def extract_verb_name(v):
            if isinstance(v, dict):
                return v.get('id', '').split('/')[-1]
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

        real_counter = Counter(real_bigrams)
        synth_counter = Counter(synth_bigrams)

        top_real = real_counter.most_common(10)
        top_synth = synth_counter.most_common(10)

        total_real = sum(real_counter.values())
        total_synth = sum(synth_counter.values())

        jaccard = 0.0
        real_set = set(pair for pair, _ in top_real)
        synth_set = set(pair for pair, _ in top_synth)
        if real_set or synth_set:
            intersection = real_set & synth_set
            union = real_set | synth_set
            jaccard = len(intersection) / len(union)
        return top_real, top_synth, jaccard

    # --- Matrice de transition Markov ---
    def compute_markov_transition_matrices(self, df):
        # On suppose que df contient 'actor', 'verb' et 'timestamp'
        df = df.sort_values(by=['actor', 'timestamp'])
        verb_seqs = df.groupby('actor')['verb'].apply(list)
        transitions = []
        for seq in verb_seqs:
            transitions += [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
        trans_df = pd.DataFrame(transitions, columns=['from', 'to'])
        matrix = pd.crosstab(trans_df['from'], trans_df['to'], normalize='index')
        return matrix.fillna(0)

    def compute_l1_divergence(self, matrix1, matrix2):
        return np.abs(matrix1.values - matrix2.values).sum()

    # --- Analyse PCA ---
    def perform_pca(self, real_df, synth_df):
        # Sélectionner les colonnes d'intérêt
        columns = ['verb', 'actor', 'object', 'duration']
        real_df = self.convert_column_types(real_df, columns)
        synth_df = self.convert_column_types(synth_df, columns)

        real_df, _ = self.encode_categorical(real_df, ['verb', 'actor', 'object'])
        synth_df, _ = self.encode_categorical(synth_df, ['verb', 'actor', 'object'])

        real_df['dataset'] = 'original'
        synth_df['dataset'] = 'synthetic'
        combined_df = pd.concat([real_df, synth_df], ignore_index=True).dropna(subset=columns)

        X = combined_df[columns].copy()
        y = combined_df['dataset']

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        np.random.seed(42)
        pca = PCA(n_components=min(10, X_scaled.shape[1]), random_state=42)
        components = pca.fit_transform(X_scaled)
        explained_var = pca.explained_variance_ratio_

        # Projection 2D
        fig = None
        if X_scaled.shape[1] >= 2:
            plt.figure(figsize=(7, 6))
            for label in ['original', 'synthetic']:
                idx = y == label
                plt.scatter(components[idx, 0], components[idx, 1], label=label, alpha=0.6)
            plt.title("Projection 2D PCA: Réel vs Synthétique")
            plt.xlabel("Composante 1")
            plt.ylabel("Composante 2")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            fig = plt.gcf()
            plt.close()  # Pour éviter d'afficher immédiatement
        cumulative_2D = np.sum(explained_var[:2])
        cumulative_5D = np.sum(explained_var[:5])
        var_info = {
            "cumulative_2D": cumulative_2D,
            "cumulative_5D": cumulative_5D,
            "explained_variance": explained_var
        }
        return fig, var_info

    # --- Méthodes utilitaires pour PCA ---
    @staticmethod
    def convert_column_types(df, columns):
        for col in columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df

    @staticmethod
    def encode_categorical(df, columns):
        return encode_categorical(df, columns)
