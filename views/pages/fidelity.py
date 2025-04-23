import pandas as pd
import seaborn as sns
import numpy as np
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QPlainTextEdit, QToolTip
)
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sdmetrics.single_column import KSComplement, TVComplement
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

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
        layout.addSpacing(30)

        title = QLabel("Fidelity Analysis")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(50)

        # KS Complement
        h1 = QHBoxLayout()
        self.ksc_button = QPushButton("Compute the KS Complement")
        self.ksc_button.clicked.connect(self.calculate_ksc)
        h1.addWidget(self.ksc_button)
        info1 = QPushButton("?"); info1.setFixedSize(24, 24)
        info1.clicked.connect(lambda: self._show_info_tooltip(
            "KS Complement Info",
            "KS Complement measures the maximum distance between the real and synthetic CDFs.\n"
            "Values close to 0 indicate better fidelity."
        ))
        h1.addWidget(info1)
        layout.addLayout(h1)

        # TV Complement
        h2 = QHBoxLayout()
        self.tvc_button = QPushButton("Compute the TV Complement")
        self.tvc_button.clicked.connect(self.calculate_tvc)
        h2.addWidget(self.tvc_button)
        info2 = QPushButton("?"); info2.setFixedSize(24, 24)
        info2.clicked.connect(lambda: self._show_info_tooltip(
            "TV Complement Info",
            "TV Complement (Total Variation) quantifies the total distance between distributions.\n"
            "Values close to 0 indicate better fidelity."
        ))
        h2.addWidget(info2)
        layout.addLayout(h2)

        # Verb sequence logic
        h3 = QHBoxLayout()
        self.sequence_button = QPushButton("Check verb sequence logic")
        self.sequence_button.clicked.connect(self.calculate_verb_sequence_similarity)
        h3.addWidget(self.sequence_button)
        info3 = QPushButton("?"); info3.setFixedSize(24, 24)
        info3.clicked.connect(lambda: self._show_info_tooltip(
            "Sequence Logic Info",
            "Compares the order of verbs per user, real vs synthetic.\n"
            "A high Jaccard index indicates good logic preservation."
        ))
        h3.addWidget(info3)
        layout.addLayout(h3)

        # Markov transition matrices
        h4 = QHBoxLayout()
        self.markov_button = QPushButton("Display Markov transition matrices")
        self.markov_button.clicked.connect(self.plot_markov_transition_matrices)
        h4.addWidget(self.markov_button)
        info4 = QPushButton("?"); info4.setFixedSize(24, 24)
        info4.clicked.connect(lambda: self._show_info_tooltip(
            "Markov Matrix Info",
            "Displays the transition probabilities from one verb to another.\n"
            "The L1 divergence indicates the overall difference."
        ))
        h4.addWidget(info4)
        layout.addLayout(h4)

        # PCA Analysis
        self.pca_button = QPushButton("Analyse de la variance (PCA)")
        self.pca_button.setToolTip(
            "Affiche la variance expliquée par composante principale.\n"
            "Projette les données en 2D pour visualisation.\n"
            "Utilise PCA pour détecter la structure latente."
        )
        self.pca_button.clicked.connect(self.perform_pca_analysis)
        layout.addWidget(self.pca_button)

        layout.addSpacing(20)
        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def _show_info_tooltip(self, title: str, message: str):
        btn = self.sender()
        pos = btn.mapToGlobal(btn.rect().bottomLeft()) if btn else self.mapToGlobal(self.rect().center())
        html = f"<b>{title}</b><br>{message.replace(chr(10), '<br>')}"
        QToolTip.showText(pos, html, btn)

    def on_data_generated(self):
        self.synthetic_data = self._ensure_df(self.main_app.pages["generate"].generated_data)
        self.original_data = self._ensure_df(self.main_app.pages["open"].json_data)
        if 'actions' in self.synthetic_data.columns:
            self.synthetic_data = self._flatten(self.synthetic_data)
        if 'actions' in self.original_data.columns:
            self.original_data = self._flatten(self.original_data)

    def _ensure_df(self, data):
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def _flatten(self, df):
        rows = []
        for sess in df['actions']:
            for action in sess:
                rows.append({
                    'id': action.get('id'),
                    'timestamp': action.get('timestamp'),
                    'verb': action.get('verb', {}).get('id'),
                    'actor': action.get('actor', {}).get('mbox'),
                    'object': action.get('object', {}).get('id'),
                    'duration': action.get('duration', 0.0)
                })
        return pd.DataFrame(rows)

    def _categorize(self, value, thresholds, labels):
        for thr, lab in zip(thresholds, labels):
            if value < thr:
                return lab
        return labels[-1]

    def calculate_ksc(self):
        self.results_text.clear()
        df = self.original_data
        synth = self.synthetic_data
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        cols = ['actor', 'verb', 'object']
        df, _ = encode_categorical(df, cols)
        synth, _ = encode_categorical(synth, cols)

        thresholds = [0.01, 0.05, 0.1, 0.2]
        labels = ["Excellent", "Very Good", "Good", "Ok", "Bad"]

        for col in cols:
            try:
                score = KSComplement.compute(real_data=df[col], synthetic_data=synth[col])
                status = self._categorize(score, thresholds, labels)
                self.results_text.appendPlainText(f"KS Complement for {col}: {score:.4f} [{status}]")
            except Exception as e:
                self.results_text.appendPlainText(f"Error KS {col}: {e}")

    def calculate_tvc(self):
        self.results_text.clear()
        df = self.original_data
        synth = self.synthetic_data
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        cols = ['actor', 'verb', 'object']
        df, _ = encode_categorical(df, cols)
        synth, _ = encode_categorical(synth, cols)

        thresholds = [0.01, 0.05, 0.1, 0.2]
        labels = ["Excellent", "Very Good", "Good", "Ok", "Bad"]

        for col in cols:
            try:
                score = TVComplement.compute(real_data=df[col], synthetic_data=synth[col])
                status = self._categorize(score, thresholds, labels)
                self.results_text.appendPlainText(f"TV Complement for {col}: {score:.4f} [{status}]")
            except Exception as e:
                self.results_text.appendPlainText(f"Error TV {col}: {e}")

    def calculate_verb_sequence_similarity(self):
        self.results_text.clear()
        df_r = self.original_data.copy()
        df_s = self.synthetic_data.copy()
        if df_r.empty or df_s.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        for col in ('actor', 'verb', 'timestamp'):
            if col not in df_r or col not in df_s:
                self.results_text.appendPlainText(f"Missing column: {col}")
                return

        df_r['timestamp'] = pd.to_datetime(df_r['timestamp'], errors='coerce')
        df_s['timestamp'] = pd.to_datetime(df_s['timestamp'], errors='coerce')
        df_r.dropna(subset=['timestamp'], inplace=True)
        df_s.dropna(subset=['timestamp'], inplace=True)
        df_r.sort_values(['actor', 'timestamp'], inplace=True)
        df_s.sort_values(['actor', 'timestamp'], inplace=True)

        def bigrams(seqs):
            return [(seq[i], seq[i + 1]) for seq in seqs for i in range(len(seq) - 1)]

        br = bigrams(df_r.groupby('actor')['verb'].apply(list))
        bs = bigrams(df_s.groupby('actor')['verb'].apply(list))
        cr = pd.Series(br).value_counts(normalize=True).head(10)
        cs = pd.Series(bs).value_counts(normalize=True).head(10)

        self.results_text.appendPlainText("Top 10 real bigrams (%):")
        for pair, pct in cr.items():
            self.results_text.appendPlainText(f"  {pair}: {pct * 100:.2f}%")

        self.results_text.appendPlainText("\nTop 10 synth bigrams (%):")
        for pair, pct in cs.items():
            self.results_text.appendPlainText(f"  {pair}: {pct * 100:.2f}%")

        jacc = len(set(cr.index) & set(cs.index)) / len(set(cr.index) | set(cs.index) or [1])
        thresholds = [0.2, 0.5, 0.8, 0.95]
        labels = ["Bad", "Ok", "Good", "Very Good", "Excellent"]
        status = self._categorize(jacc, thresholds, labels)
        self.results_text.appendPlainText(f"\nJaccard index (top10): {jacc:.2f} [{status}]")

    def plot_markov_transition_matrices(self):
        self.results_text.clear()
        df_r = self.original_data.copy()
        df_s = self.synthetic_data.copy()
        if df_r.empty or df_s.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        for col in ('actor', 'verb', 'timestamp'):
            if col not in df_r or col not in df_s:
                self.results_text.appendPlainText(f"Missing column: {col}")
                return

        df_r['timestamp'] = pd.to_datetime(df_r['timestamp'], errors='coerce')
        df_s['timestamp'] = pd.to_datetime(df_s['timestamp'], errors='coerce')
        df_r.dropna(subset=['timestamp'], inplace=True)
        df_s.dropna(subset=['timestamp'], inplace=True)

        def transition_matrix(df):
            df = df.sort_values(['actor', 'timestamp'])
            seqs = df.groupby('actor')['verb'].apply(list)
            pairs = [(seq[i], seq[i + 1]) for seq in seqs for i in range(len(seq) - 1)]
            tdf = pd.DataFrame(pairs, columns=['from', 'to'])
            return pd.crosstab(tdf['from'], tdf['to'], normalize='index').fillna(0)

        M_r = transition_matrix(df_r)
        M_s = transition_matrix(df_s)
        verbs = sorted(set(M_r.index) | set(M_r.columns) | set(M_s.index) | set(M_s.columns))
        M_r = M_r.reindex(index=verbs, columns=verbs, fill_value=0)
        M_s = M_s.reindex(index=verbs, columns=verbs, fill_value=0)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        sns.heatmap(M_r, ax=axes[0], cmap="Blues", cbar=False)
        axes[0].set_title("Real transition")
        sns.heatmap(M_s, ax=axes[1], cmap="Oranges", cbar=False)
        axes[1].set_title("Synthetic transition")
        plt.tight_layout()
        plt.show()

        dist = np.abs(M_r.values - M_s.values).sum()
        status = self._categorize(dist, [5, 10, 20, 40], ["Excellent", "Good", "Ok", "Bad"])
        self.results_text.appendPlainText(f"\nL1 divergence between matrices: {dist:.4f} [{status}]")

    def perform_pca_analysis(self):
        real_df = self.original_data.copy()
        synth_df = self.synthetic_data.copy()

        # Log the initial state of the data
        self.results_text.appendPlainText("\nInitial state of original data:")
        self.results_text.appendPlainText(real_df.head().to_string(index=False))
        self.results_text.appendPlainText("\nInitial state of synthetic data:")
        self.results_text.appendPlainText(synth_df.head().to_string(index=False))

        if real_df.empty or synth_df.empty:
            self.results_text.appendPlainText("Error: Data not available for PCA.")
            return

        columns = ['verb', 'actor', 'object', 'duration']
        real_df = self.convert_column_types(real_df, columns)
        synth_df = self.convert_column_types(synth_df, columns)

        # Ensure both DataFrames have the same columns
        for col in columns:
            if col not in real_df.columns:
                real_df[col] = np.nan
            if col not in synth_df.columns:
                synth_df[col] = np.nan

        # Log after type conversion
        self.results_text.appendPlainText("\nAfter column type conversion (original):")
        self.results_text.appendPlainText(real_df.head().to_string(index=False))
        self.results_text.appendPlainText("\nAfter column type conversion (synthetic):")
        self.results_text.appendPlainText(synth_df.head().to_string(index=False))

        real_df, _ = encode_categorical(real_df, ['verb', 'actor', 'object'])
        synth_df, _ = encode_categorical(synth_df, ['verb', 'actor', 'object'])

        # Log after encoding
        self.results_text.appendPlainText("\nAfter categorical encoding (original):")
        self.results_text.appendPlainText(real_df.head().to_string(index=False))
        self.results_text.appendPlainText("\nAfter categorical encoding (synthetic):")
        self.results_text.appendPlainText(synth_df.head().to_string(index=False))

        real_df['dataset'] = 'original'
        synth_df['dataset'] = 'synthetic'
        combined_df = pd.concat([real_df, synth_df], ignore_index=True).dropna(subset=columns)

        # Log after concatenation
        self.results_text.appendPlainText("\nAfter concatenating datasets:")
        self.results_text.appendPlainText(combined_df.head().to_string(index=False))

        X = combined_df[columns].copy()
        y = combined_df['dataset']

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        np.random.seed(42)
        pca = PCA(n_components=min(10, X_scaled.shape[1]), random_state=42)
        components = pca.fit_transform(X_scaled)
        explained_var = pca.explained_variance_ratio_

        # Normalize components for visualization
        components = (components - components.mean(axis=0)) / components.std(axis=0)

        # 2D scatter projection (smaller figure)
        if X_scaled.shape[1] >= 2:
            plt.figure(figsize=(8, 6))  # reduced size
            for label, marker, size in zip(['original', 'synthetic'], ['o', 's'], [40, 80]):
                idx = y == label
                plt.scatter(components[idx, 0], components[idx, 1], label=label,
                            alpha=0.6, s=size, edgecolors='w', linewidth=0.5)
            plt.title("2D PCA Projection: Original vs Synthetic")
            plt.xlabel("PC1")
            plt.ylabel("PC2")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()

        # Explained variance summary
        cum2 = explained_var[:2].sum()
        cum5 = explained_var[:5].sum()
        self.results_text.appendPlainText(
            f"\nVariance explained:\n"
            f"→ 2 components: {cum2:.2%}\n"
            f"→ 5 components: {cum5:.2%}"
        )

        if cum2 >= 0.45:
            self.results_text.appendPlainText(
                "✔️ 2D projection captures sufficient structure."
            )
        else:
            self.results_text.appendPlainText(
                "⚠️ 2D projection loses too much information; consider more dimensions."
            )

    def convert_column_types(self, df, columns):
        for column in columns:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df