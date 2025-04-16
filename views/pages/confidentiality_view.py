# confidentiality_view.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QPlainTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ConfidentialityView(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.initUI()


    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.addSpacing(30)

        self.title = QLabel("Confidentiality Analysis")
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)

        self.cramers_v_button = QPushButton("Calculate Cramer's V")
        self.layout.addWidget(self.cramers_v_button)

        self.dcr_button = QPushButton("Calculate DCR")
        self.layout.addWidget(self.dcr_button)

        self.pmse_button = QPushButton("Calculate pMSE")
        self.layout.addWidget(self.pmse_button)

        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        self.layout.addWidget(self.results_text)

        self.setLayout(self.layout)

    def append_result(self, text):
        self.results_text.appendPlainText(text)

    def clear_results(self):
        self.results_text.clear()

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