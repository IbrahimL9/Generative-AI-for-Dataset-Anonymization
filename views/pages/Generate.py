import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QProgressBar
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from views.Styles import BUTTON_STYLE


class Generate(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)  # Réduit l'espacement global

        title = QLabel("Generate")
        title.setFont(QFont("Montserrat", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)

        # Formulaire pour "Number of Data to Generate"
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(5)  # Réduit l'espacement vertical dans le formulaire
        self.records_input = QLineEdit("1000")
        self.records_input.setFixedWidth(300)
        form_layout.addRow("Number of Data to Generate:", self.records_input)
        layout.addLayout(form_layout)

        # Bouton de génération (placé ici, il sera plus proche du formulaire)
        generate_button = QPushButton("Generate Data")
        generate_button.setStyleSheet(BUTTON_STYLE)
        generate_button.setMinimumSize(150, 50)
        generate_button.clicked.connect(self.on_generate)
        layout.addWidget(generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Barre de chargement centrée sous le bouton
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé (animation continue)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

    def on_generate(self):
        records_count = self.records_input.text()
        self.progress_bar.setVisible(True)

