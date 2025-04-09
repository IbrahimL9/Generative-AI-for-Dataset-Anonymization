import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal


class Open(QWidget):
    fileDownloaded = pyqtSignal()
    fileLoaded = pyqtSignal()

    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.json_data = None

        self.initUI()

        # Connexion directe au signal (plus propre qu'un QTimer)
        self.download_button.file_loaded.connect(self.handle_file_loaded)

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(20)

        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch(2)

        self.setLayout(layout)

    def reset(self):
        """Réinitialiser l'état de la page."""
        self.download_button.json_data = None
        self.json_data = None

    def handle_file_loaded(self):
        """Méthode appelée lorsqu'un fichier est chargé."""
        # Si on n'a pas déjà stocké de données
        if self.json_data is None:
            self.json_data = self.download_button.json_data
            self.fileDownloaded.emit()
