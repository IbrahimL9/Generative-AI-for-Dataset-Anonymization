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
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestClassifier


class Confidentiality(QWidget):
    """Widget providing confidentiality/utility checks for synthetic data."""

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.synthetic_data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.initUI()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.addSpacing(30)

        title = QLabel("Confidentiality Analysis", self)
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(50)

        # Cramer's V -------------------------------------------------------
        h1 = QHBoxLayout()
        self.cramers_v_button = QPushButton("Calculate Cramer's V", self)
        self.cramers_v_button.clicked.connect(self.calculate_cramers_v)
        h1.addWidget(self.cramers_v_button)
        info1 = QPushButton("?", self)
        info1.setFixedSize(24, 24)
        info1.clicked.connect(self.show_cramers_info)
        h1.addWidget(info1)
        layout.addLayout(h1)

        # DCR --------------------------------------------------------------
        h2 = QHBoxLayout()
        self.dcr_button = QPushButton("Calculate DCR", self)
        self.dcr_button.clicked.connect(self.calculate_dcr)
        h2.addWidget(self.dcr_button)
        info2 = QPushButton("?", self)
        info2.setFixedSize(24, 24)
        info2.clicked.connect(self.show_dcr_info)
        h2.addWidget(info2)
        layout.addLayout(h2)

        # pMSE -------------------------------------------------------------
        h3 = QHBoxLayout()
        self.pmse_button = QPushButton("Calculate pMSE", self)
        self.pmse_button.clicked.connect(self.calculate_pmse)
        h3.addWidget(self.pmse_button)
        info3 = QPushButton("?", self)
        info3.setFixedSize(24, 24)
        info3.clicked.connect(self.show_pmse_info)
        h3.addWidget(info3)
        layout.addLayout(h3)

        self.results_text = QPlainTextEdit(self)
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

    # ------------------------------------------------------------------
    # Tool‑tips helpers
    # ------------------------------------------------------------------
    def _show_info_dialog(self, title: str, message: str):
        html = f"<b>{title}</b><br>{message.replace(chr(10), '<br>')}"
        btn = self.sender()
        pos = (
            btn.mapToGlobal(btn.rect().bottomLeft()) if btn else self.mapToGlobal(self.rect().center())
        )
        QToolTip.showText(pos, html, btn)

    def show_cramers_info(self):
        self._show_info_dialog(
            "Cramer's V Info",
            "Cramer's V measures association between two categorical variables.\n"
            "Values closer to 1 indicate strong association.\n"
            "Helps detect privacy risks if synthetic data is too similar to original."
        )

    def show_dcr_info(self):
        self._show_info_dialog(
            "DCR Info",
            "DCR (Distortion of Categorical Representation) quantifies how much the distribution\n"
            "of categories in synthetic data deviates from the original.\n"
            "Lower values mean less distortion (better utility)."
        )

    def show_pmse_info(self):
        self._show_info_dialog(
            "pMSE Info",
            "pMSE (propensity Mean Squared Error) compares the predicted membership probability\n"
            "for each record with the ideal value of 0.5 (random guessing).\n"
            "Lower values (closer to 0) indicate that the classifier struggles to distinguish\n"
            "synthetic from real data, suggesting higher similarity but, if *too* low, potential disclosure risk."
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _categorize(value, thresholds, labels):
        """Return the first label whose threshold is strictly greater than *value*."""
        for thr, lab in zip(thresholds, labels):
            if value < thr:
                return lab
        return labels[-1]

    # ------------------------------------------------------------------
    # Data preparation hooks (called externally)
    # ------------------------------------------------------------------
    def on_data_generated(self, synthetic_data):
        self.synthetic_data = self._ensure_dataframe(synthetic_data)
        self.original_data = self._ensure_dataframe(self.main_app.json_data)
        self.synthetic_data = self._flatten(self.synthetic_data)
        self.original_data = self._flatten(self.original_data)

    @staticmethod
    def _ensure_dataframe(data):
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if isinstance(data, (dict, list)):
            return pd.DataFrame(data)
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Flatten helpers for nested xAPI‑like structures
    # ------------------------------------------------------------------
    @staticmethod
    def _flatten(df: pd.DataFrame) -> pd.DataFrame:
        """Turn nested sessions/actions representations into a flat table."""
        # Case 1: DataFrame of sessions each containing a list of actions ------------
        if "actions" in df.columns:
            rows = []
            for sess in df["actions"]:
                for action in sess:
                    rows.append(
                        {
                            "id": action.get("id"),
                            "timestamp": action.get("timestamp"),
                            "verb": action.get("verb", {}).get("id"),
                            "actor": action.get("actor", {}).get("mbox"),
                            "object": action.get("object", {}).get("id"),
                            "duration": action.get("duration", 0.0),
                        }
                    )
            return pd.DataFrame(rows)

        # Case 2: DataFrame of actions with nested dicts -----------------------------
        if "actor" in df.columns and df["actor"].apply(lambda x: isinstance(x, dict)).any():
            rows = []
            for _, action in df.iterrows():
                rows.append(
                    {
                        "id": action.get("id"),
                        "timestamp": action.get("timestamp"),
                        "verb": (
                            action["verb"].get("id") if isinstance(action.get("verb"), dict) else action.get("verb")
                        ),
                        "actor": (
                            action["actor"].get("mbox") if isinstance(action.get("actor"), dict) else action.get("actor")
                        ),
                        "object": (
                            action["object"].get("id") if isinstance(action.get("object"), dict) else action.get("object")
                        ),
                        "duration": action.get("duration", 0.0),
                    }
                )
            return pd.DataFrame(rows)

        # Otherwise: return as‑is ----------------------------------------------------
        return df.copy()

    # ------------------------------------------------------------------
    # CONFIDENTIALITY / UTILITY METRICS
    # ------------------------------------------------------------------
    def calculate_cramers_v(self):
        self.results_text.clear()
        df, synth = self.original_data.copy(), self.synthetic_data.copy()
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        for col in ("actor", "verb", "object"):
            if col in df:
                df[col] = df[col].fillna("").astype(str)
            if col in synth:
                synth[col] = synth[col].fillna("").astype(str)

        thresholds = [0.01, 0.05, 0.1, 0.2]
        labels = ["Excellent", "Very Good", "Good", "Ok", "Bad"]

        def cramers_v(x, y):
            cm = pd.crosstab(x, y)
            chi2 = chi2_contingency(cm)[0]
            n = cm.values.sum()
            phi2 = chi2 / n
            r, k = cm.shape
            phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
            rcorr = r - ((r - 1) ** 2) / (n - 1)
            kcorr = k - ((k - 1) ** 2) / (n - 1)
            return np.sqrt(phi2corr / max(1, min(kcorr - 1, rcorr - 1)))

        for col in ("actor", "verb", "object"):
            if col in df and col in synth:
                v = cramers_v(df[col], synth[col])
                status = self._categorize(v, thresholds, labels)
                self.results_text.appendPlainText(f"Cramer's V for {col}: {v:.4f} [{status}]")
            else:
                self.results_text.appendPlainText(f"Column '{col}' missing.")

    def calculate_dcr(self):
        self.results_text.clear()
        df, synth = self.original_data.copy(), self.synthetic_data.copy()
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        for col in ("actor", "verb", "object"):
            if col in df:
                df[col] = df[col].fillna("").astype(str)
            if col in synth:
                synth[col] = synth[col].fillna("").astype(str)

        thresholds = [0.01, 0.05, 0.1, 0.2]
        labels = ["Excellent", "Very Good", "Good", "Ok", "Bad"]

        for col in ("actor", "verb", "object"):
            if col not in df or col not in synth:
                self.results_text.appendPlainText(f"Column '{col}' missing.")
                continue

            orig_p = df[col].value_counts(normalize=True)
            synth_p = synth[col].value_counts(normalize=True)
            all_cats = orig_p.index.union(synth_p.index)

            l1 = (orig_p.reindex(all_cats, fill_value=0.0) - synth_p.reindex(all_cats, fill_value=0.0)).abs().sum()
            tv = 0.5 * l1
            status = self._categorize(tv, thresholds, labels)
            self.results_text.appendPlainText(f"\nDCR for {col}: {tv:.4f} [{status}]\n")

    def calculate_pmse(self):
        self.results_text.clear()
        df, synth = self.original_data.copy(), self.synthetic_data.copy()
        if df.empty or synth.empty:
            self.results_text.appendPlainText("Error: data not available.")
            return

        orig = df.assign(origin=0)
        fake = synth.assign(origin=1)
        comb = pd.concat([orig, fake], ignore_index=True)

        comb = comb.applymap(lambda x: "" if pd.isna(x) else str(x))

        y = comb.pop("origin")
        X = pd.get_dummies(comb, drop_first=False)

        thresholds = [0.005, 0.01, 0.025, 0.05]  # Adapted to new 0‑0.25 range
        labels = ["Excellent", "Very Good", "Good", "Ok", "Bad"]

        try:
            X_train, X_test, y_train, _ = train_test_split(
                X, y, test_size=0.5, stratify=y, random_state=42
            )
            clf = RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                n_jobs=-1,
                random_state=42,
            ).fit(X_train, y_train)

            probs = clf.predict_proba(X_test)[:, 1]  # P(origin=1 | X)
            pmse = np.mean((probs - 0.5) ** 2)

            status = self._categorize(pmse, thresholds, labels)
            self.results_text.appendPlainText(f"pMSE: {pmse:.4f} [{status}]")
        except Exception as e:
            self.results_text.appendPlainText(f"Error calculating pMSE: {e}")

