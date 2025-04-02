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

class Confidentiality(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.synthetic_data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(30)

        title = QLabel("Analysis")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(50)

        self.cramers_v_button = QPushButton("Calculate Cramer's V")
        self.cramers_v_button.clicked.connect(self.calculate_cramers_v)
        layout.addWidget(self.cramers_v_button)

        self.dcr_button = QPushButton("Calculate DCR")
        self.dcr_button.clicked.connect(self.calculate_dcr)
        layout.addWidget(self.dcr_button)

        self.pmse_button = QPushButton("Calculate pMSE")
        self.pmse_button.clicked.connect(self.calculate_pmse)
        layout.addWidget(self.pmse_button)

        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def on_data_generated(self):
        """Called when the 'generate' page has finished generating
        or loading synthetic data."""
        self.synthetic_data = self.main_app.pages["generate"].generated_data
        self.original_data = self.main_app.pages["open"].json_data

        self.original_data = self.ensure_dataframe(self.original_data)
        self.synthetic_data = self.ensure_dataframe(self.synthetic_data)

        # Set column names to lowercase to match data
        self.original_data.columns = self.original_data.columns.str.lower()
        self.synthetic_data.columns = self.synthetic_data.columns.str.lower()

        print("Columns in original_data:", self.original_data.columns)
        print("Columns in synthetic_data:", self.synthetic_data.columns)

        if self.original_data.empty or self.synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available or incorrect.")
            return

        # Check if the data is in session mode
        self.is_session_mode = 'session_id' in self.original_data.columns

    def ensure_dataframe(self, data):
        """Converts your data to DataFrame if necessary."""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def flatten_synthetic_data(self, synthetic_data):
        """Aplatir les données synthétiques pour correspondre à la structure de original_data."""
        if 'actions' in synthetic_data.columns:
            # Extraire les informations pertinentes de 'actions'
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

    def calculate_cramers_v(self):
        """Calculates and displays Cramer's V for categorical columns."""
        def cramers_v(x, y):
            # Convert values to strings to avoid errors
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
        synthetic_data = self.flatten_synthetic_data(self.synthetic_data)

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available.")
            return

        categorical_columns = ['actor', 'verb', 'object']
        results = {}
        for column in categorical_columns:
            if column in df.columns and column in synthetic_data.columns:
                v_cramer_value = cramers_v(df[column], synthetic_data[column])
                results[column] = v_cramer_value
                self.results_text.appendPlainText(f"Cramer's V for {column}: {v_cramer_value:.4f}")
            else:
                self.results_text.appendPlainText(f"Column '{column}' missing in data.")

        # Display the plot only if there are results
        if results:
            self.plot_cramers_v(results)

    def plot_cramers_v(self, results):
        # Filter out columns and values with NaN together
        filtered_results = {col: v for col, v in results.items() if np.isfinite(v)}

        if not filtered_results:  # Check if there are still values after filtering
            self.results_text.appendPlainText("No valid Cramer's V values to plot.")
            return

        columns = list(filtered_results.keys())
        cramer_values = list(filtered_results.values())  # Now, lengths are aligned

        plt.figure(figsize=(10, 6))
        bars = plt.bar(columns, cramer_values)
        plt.axhline(y=0.1, color='r', linestyle='--', label='Desired Threshold')
        plt.title("Cramer's V Values")
        plt.xlabel("Variables")
        plt.ylabel("Cramer's V Value")
        plt.ylim(0, max(cramer_values) + 0.05)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, yval, round(yval, 4), va='bottom')

        plt.legend()
        plt.show()

    def calculate_dcr(self):
        df = self.original_data
        synthetic_data = self.flatten_synthetic_data(self.synthetic_data)

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available.")
            return

        # 1) Align columns between original and synthetic data
        common_columns = list(set(df.columns).intersection(synthetic_data.columns))
        df = df[common_columns]
        synthetic_data = synthetic_data[common_columns]

        # 2) Split real data into train/holdout (e.g., 50/50)
        train_df, holdout_df = train_test_split(df, test_size=0.5, random_state=42)

        # 3) Convert to string if some columns are of type dict or object
        train_df = train_df.apply(lambda x: x.map(str) if x.dtype == 'object' else x)
        holdout_df = holdout_df.apply(lambda x: x.map(str) if x.dtype == 'object' else x)
        synthetic_data = synthetic_data.apply(lambda x: x.map(str) if x.dtype == 'object' else x)

        # 4) One-hot encode
        train_encoded = pd.get_dummies(train_df)
        holdout_encoded = pd.get_dummies(holdout_df)
        synthetic_encoded = pd.get_dummies(synthetic_data)

        # 5) Align columns after one-hot encoding
        common_encoded_cols = list(
            set(train_encoded.columns)
            .intersection(holdout_encoded.columns)
            .intersection(synthetic_encoded.columns)
        )

        train_encoded = train_encoded[common_encoded_cols]
        holdout_encoded = holdout_encoded[common_encoded_cols]
        synthetic_encoded = synthetic_encoded[common_encoded_cols]

        # 6) Utility function to calculate distances
        def get_min_hamming_distances(synth, reference):
            distances = pairwise_distances(synth, reference, metric='hamming')
            min_distances = distances.min(axis=1)
            return min_distances

        # 7) Calculate DCR with respect to train and holdout
        dcr_train = get_min_hamming_distances(synthetic_encoded, train_encoded).mean()
        dcr_holdout = get_min_hamming_distances(synthetic_encoded, holdout_encoded).mean()

        self.results_text.appendPlainText(f"DCR Train: {dcr_train:.4f}")
        self.results_text.appendPlainText(f"DCR Holdout: {dcr_holdout:.4f}")

    def calculate_pmse(self):
        df = self.original_data
        synthetic_data = self.flatten_synthetic_data(self.synthetic_data)

        if df.empty or synthetic_data.empty:
            self.results_text.appendPlainText("Error: Data not available.")
            return

        # 1) Combine original (origin=0) and synthetic (origin=1) data
        combined_df = pd.concat([df.assign(origin=0), synthetic_data.assign(origin=1)], ignore_index=True)

        # 2) Convert all potentially 'dict' or 'object' columns to string
        for column in combined_df.columns:
            combined_df[column] = combined_df[column].apply(lambda x: str(x) if isinstance(x, dict) else x)

        # 3) One-hot encoding
        try:
            X = pd.get_dummies(combined_df.drop('origin', axis=1))
            y = combined_df['origin']

            # 4) Split train/test (50/50), stratified on y
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, stratify=y, random_state=42)

            # 5) Train RandomForest to distinguish origin=0 vs origin=1
            classifier = RandomForestClassifier(random_state=42)
            classifier.fit(X_train, y_train)

            # 6) Predict probabilities on X_test
            y_pred_prob = classifier.predict_proba(X_test)[:, 1]

            # 7) Calculate pMSE
            pmse_value = mean_squared_error(y_test, y_pred_prob)
            self.results_text.appendPlainText(f"pMSE: {pmse_value:.4f}")

        except Exception as e:
            self.results_text.appendPlainText(f"Error calculating pMSE: {str(e)}")

