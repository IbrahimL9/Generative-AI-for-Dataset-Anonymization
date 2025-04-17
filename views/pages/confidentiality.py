import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QApplication, QToolTip
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from scipy.stats import chi2_contingency
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

        title = QLabel("Confidentiality Analysis")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(50)

        # Cramer's V button + info
        h1 = QHBoxLayout()
        self.cramers_v_button = QPushButton("Calculate Cramer's V")
        self.cramers_v_button.clicked.connect(self.calculate_cramers_v)
        h1.addWidget(self.cramers_v_button)
        info1 = QPushButton("?")
        info1.setFixedSize(24,24)
        info1.setToolTip("What is Cramer's V?")
        info1.clicked.connect(self.show_cramers_info)
        h1.addWidget(info1)
        layout.addLayout(h1)

        # DCR button + info
        h2 = QHBoxLayout()
        self.dcr_button = QPushButton("Calculate DCR")
        self.dcr_button.clicked.connect(self.calculate_dcr)
        h2.addWidget(self.dcr_button)
        info2 = QPushButton("?")
        info2.setFixedSize(24,24)
        info2.setToolTip("What is DCR?")
        info2.clicked.connect(self.show_dcr_info)
        h2.addWidget(info2)
        layout.addLayout(h2)

        # pMSE button + info
        h3 = QHBoxLayout()
        self.pmse_button = QPushButton("Calculate pMSE")
        self.pmse_button.clicked.connect(self.calculate_pmse)
        h3.addWidget(self.pmse_button)
        info3 = QPushButton("?")
        info3.setFixedSize(24,24)
        info3.setToolTip("What is pMSE?")
        info3.clicked.connect(self.show_pmse_info)
        h3.addWidget(info3)
        layout.addLayout(h3)

        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def _show_info_dialog(self, title: str, message: str):
        text = f"<b>{title}</b><br>{message.replace(chr(10), '<br>')}"
        btn = self.sender()
        pos = btn.mapToGlobal(btn.rect().bottomLeft()) if btn else self.mapToGlobal(self.rect().center())
        QToolTip.showText(pos, text, btn)

    def show_cramers_info(self):
        title = "Cramer's V Info"
        message = (
            "Cramer's V measures association between two categorical variables.\n"
            "Values closer to 1 indicate strong association.\n"
            "Helps detect privacy risks if synthetic data too similar to original."
        )
        self._show_info_dialog(title, message)

    def show_dcr_info(self):
        title = "DCR Info"
        message = (
            "DCR (Distortion of Categorical Representation) quantifies how much the distribution "
            "of categories in synthetic data deviates from the original.\n"
            "Lower values mean less distortion (better utility)."
        )
        self._show_info_dialog(title, message)

    def show_pmse_info(self):
        title = "pMSE Info"
        message = (
            "pMSE (probabilistic Mean Squared Error) evaluates how well a classifier can distinguish "
            "synthetic from real records.\n"
            "Lower pMSE indicates high similarity, but too low may risk disclosure."
        )
        self._show_info_dialog(title, message)

    def _categorize(self, value, thresholds, labels):
        for thr, lab in zip(thresholds, labels):
            if value < thr:
                return lab
        return labels[-1]

    def on_data_generated(self, synthetic_data):
        self.synthetic_data = self._ensure_dataframe(synthetic_data)
        self.original_data = self._ensure_dataframe(self.main_app.json_data)
        self.synthetic_data = self._flatten(self.synthetic_data)
        self.original_data = self._flatten(self.original_data)

    def _ensure_dataframe(self, data):
        if isinstance(data, pd.DataFrame):
            return data.copy()
        elif isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()

    def _flatten(self, df):
        if 'actions' in df.columns:
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
        return df

    def calculate_cramers_v(self):
        self.results_text.clear()
        df, synth = self.original_data, self.synthetic_data
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        thresholds = [0.05, 0.1, 0.2]
        labels = ["Very Good", "Good", "Ok", "Bad"]

        def cramers_v(x, y):
            cm = pd.crosstab(x.astype(str), y.astype(str))
            chi2 = chi2_contingency(cm)[0]
            n = cm.sum().sum()
            phi2 = chi2 / n
            r, k = cm.shape
            phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
            rcorr = r - ((r-1)**2)/(n-1)
            kcorr = k - ((k-1)**2)/(n-1)
            return np.sqrt(phi2corr / min(kcorr-1, rcorr-1))

        for col in ('actor', 'verb', 'object'):
            if col in df and col in synth:
                v = cramers_v(df[col], synth[col])
                status = self._categorize(v, thresholds, labels)
                self.results_text.appendPlainText(f"Cramer's V for {col}: {v:.4f} [{status}]")
            else:
                self.results_text.appendPlainText(f"Column '{col}' missing.")

    def calculate_dcr(self):
        df, synth = self.original_data, self.synthetic_data
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        thresholds = [0.05, 0.1, 0.2]
        labels = ["Very Good", "Good", "Ok", "Bad"]

        common = list(set(df.columns) & set(synth.columns))
        df2 = df[common].applymap(str)
        synth2 = synth[common].applymap(str)
        train, hold = train_test_split(df2, test_size=0.5, random_state=42)
        one_hot = lambda d: pd.get_dummies(d)
        t_enc, _ = one_hot(train).align(one_hot(hold), join='inner', axis=1)
        h_enc, _ = one_hot(hold).align(t_enc, join='inner', axis=1)
        s_enc, _ = one_hot(synth2).align(t_enc, join='inner', axis=1)

        def min_hamming(a, b):
            d = pairwise_distances(a, b, metric='hamming')
            return d.min(axis=1).mean()

        d_train = min_hamming(s_enc, t_enc)
        d_hold  = min_hamming(s_enc, h_enc)
        st_train = self._categorize(d_train, thresholds, labels)
        st_hold  = self._categorize(d_hold, thresholds, labels)

        self.results_text.appendPlainText(f"DCR Train:   {d_train:.4f} [{st_train}]")
        self.results_text.appendPlainText(f"DCR Holdout: {d_hold:.4f} [{st_hold}]")

    def calculate_pmse(self):
        df, synth = self.original_data, self.synthetic_data
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        thresholds = [0.1, 0.25, 0.5]
        labels = ["Very Good", "Good", "Ok", "Bad"]

        orig = df.assign(origin=0)
        fake = synth.assign(origin=1)
        comb = pd.concat([orig, fake], ignore_index=True)
        comb = comb.applymap(lambda x: x if not isinstance(x, dict) else str(x))
        y = comb.pop('origin')
        X = pd.get_dummies(comb)

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.5, stratify=y, random_state=42
            )
            clf = RandomForestClassifier(random_state=42).fit(X_train, y_train)
            probs = clf.predict_proba(X_test)[:, 1]
            pmse = mean_squared_error(y_test, probs)
            status = self._categorize(pmse, thresholds, labels)
            self.results_text.appendPlainText(f"pMSE: {pmse:.4f} [{status}]")
        except Exception as e:
            self.results_text.appendPlainText(f"Error calculating pMSE: {e}")
