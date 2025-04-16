# fidelity_view.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QPlainTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class FidelityView(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.initUI()


    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(30)

        self.title = QLabel("Fidelity Analysis")
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)

        layout.addSpacing(50)
        # Boutons d'analyse
        self.ksc_button = QPushButton("Compute the KS Complement")
        layout.addWidget(self.ksc_button)

        self.tvc_button = QPushButton("Compute the TV Complement")
        layout.addWidget(self.tvc_button)

        self.sequence_button = QPushButton("Check the logic of verb sequences")
        layout.addWidget(self.sequence_button)

        self.markov_button = QPushButton("Display the Markov transition matrix")
        layout.addWidget(self.markov_button)

        self.pca_button = QPushButton("Analyse de la variance (PCA)")
        layout.addWidget(self.pca_button)

        # Zone pour afficher les résultats
        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        self.setLayout(layout)

    def append_result(self, text):
        self.results_text.appendPlainText(text)

    def clear_results(self):
        self.results_text.clear()

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