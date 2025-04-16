# confidentiality_model.py
import numpy as np
import pandas as pd
from statistics import mean, stdev
from collections import Counter
from scipy.stats import chi2_contingency
from sklearn.metrics import pairwise_distances, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

class ConfidentialityModel:
    # --- Helper Functions ---
    @staticmethod
    def ensure_dataframe(data):
        """Convertit les données en DataFrame si nécessaire."""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    @staticmethod
    def flatten_synthetic_data(synthetic_data):
        """Aplati les données synthétiques pour qu'elles correspondent à la structure des données originales."""
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

    # --- Extraction Utilities ---
    @staticmethod
    def extract_verb(verb_dict):
        if not isinstance(verb_dict, dict):
            return "Unknown"
        vid = verb_dict.get('id', '')
        return vid.split("/")[-1] if vid.startswith("http") else vid

    @staticmethod
    def extract_actor(actor_dict):
        if not isinstance(actor_dict, dict):
            return "Unknown"
        mbox = actor_dict.get('mbox', '')
        if mbox.startswith("mailto:"):
            return mbox.replace("mailto:", "")
        elif mbox.startswith("http"):
            return mbox.split("/")[-1]
        return mbox

    @staticmethod
    def extract_object(object_dict):
        if not isinstance(object_dict, dict):
            return "Unknown"
        oid = object_dict.get('id', '')
        return oid.split("/")[-1] if oid.startswith("http") else oid

    # --- Calcul de Cramer's V ---
    @staticmethod
    def cramers_v(x, y):
        # Convertir les valeurs en chaînes
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

    def compute_cramers_v(self, df_original, df_synthetic, categorical_columns=['actor', 'verb', 'object']):
        results = {}
        for column in categorical_columns:
            if column in df_original.columns and column in df_synthetic.columns:
                v_value = self.cramers_v(df_original[column], df_synthetic[column])
                results[column] = v_value
        return results

    def plot_cramers_v(self, results):
        filtered = {col: v for col, v in results.items() if np.isfinite(v)}
        if not filtered:
            return None
        columns = list(filtered.keys())
        values = list(filtered.values())
        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, values)
        plt.axhline(y=0.1, color='r', linestyle='--', label='Desired Threshold')
        plt.title("Cramer's V Values")
        plt.xlabel("Variables")
        plt.ylabel("Cramer's V Value")
        plt.ylim(0, max(values) + 0.05)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, yval, round(yval, 4), va='bottom')
        plt.legend()
        return plt.gcf()

    # --- Calcul du DCR ---
    def compute_dcr(self, df_original, df_synthetic):
        # Aligner les colonnes
        common_columns = list(set(df_original.columns).intersection(df_synthetic.columns))
        df1 = df_original[common_columns]
        df2 = df_synthetic[common_columns]
        # Séparer train et holdout pour les données réelles
        train_df, holdout_df = train_test_split(df1, test_size=0.5, random_state=42)
        # Convertir en chaînes pour éviter les problèmes de types
        train_df = train_df.apply(lambda x: x.map(str) if x.dtype=='object' else x)
        holdout_df = holdout_df.apply(lambda x: x.map(str) if x.dtype=='object' else x)
        df2 = df2.apply(lambda x: x.map(str) if x.dtype=='object' else x)
        train_encoded = pd.get_dummies(train_df)
        holdout_encoded = pd.get_dummies(holdout_df)
        synthetic_encoded = pd.get_dummies(df2)
        common_cols = set(train_encoded.columns).intersection(holdout_encoded.columns).intersection(synthetic_encoded.columns)
        train_encoded = train_encoded[list(common_cols)]
        holdout_encoded = holdout_encoded[list(common_cols)]
        synthetic_encoded = synthetic_encoded[list(common_cols)]
        # Calcul de la distance minimale moyenne (découpage par Hamming)
        def get_min_distances(synth, ref):
            distances = pairwise_distances(synth, ref, metric='hamming')
            return distances.min(axis=1)
        dcr_train = get_min_distances(synthetic_encoded, train_encoded).mean()
        dcr_holdout = get_min_distances(synthetic_encoded, holdout_encoded).mean()
        return dcr_train, dcr_holdout

    # --- Calcul du pMSE ---
    def compute_pmse(self, df_original, df_synthetic):
        combined = pd.concat([df_original.assign(origin=0), df_synthetic.assign(origin=1)], ignore_index=True)
        # Convertir les colonnes en chaînes si nécessaire
        for col in combined.columns:
            combined[col] = combined[col].apply(lambda x: str(x) if isinstance(x, dict) else x)
        try:
            X = pd.get_dummies(combined.drop('origin', axis=1))
            y = combined['origin']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, stratify=y, random_state=42)
            classifier = RandomForestClassifier(random_state=42)
            classifier.fit(X_train, y_train)
            y_pred_prob = classifier.predict_proba(X_test)[:, 1]
            pmse_value = mean_squared_error(y_test, y_pred_prob)
            return pmse_value
        except Exception as e:
            raise e
