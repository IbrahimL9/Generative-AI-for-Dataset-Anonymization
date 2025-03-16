import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal

class Open(QWidget):
    fileDownloaded = pyqtSignal()
    fileLoaded = pyqtSignal()

    def __init__(self, download_button):
        super().__init__()
        # Utiliser l'instance partagée passée en paramètre
        self.download_button = download_button
        self.json_data = None

        self.initUI()

        # Créer un timer qui vérifie périodiquement si un fichier a été téléchargé.
        self.checkTimer = QTimer(self)
        self.checkTimer.timeout.connect(self.updateViewButtonState)
        self.checkTimer.start(500)

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

        # Utiliser directement l'instance de DownloadButton passée au constructeur
        button_layout.addWidget(self.download_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch(2)

        # (Ici, on n'affiche plus la zone des statistiques dans Open)
        self.setLayout(layout)

    def updateViewButtonState(self):
        if hasattr(self.download_button, 'json_data') and self.download_button.json_data is not None:
            # Une fois le fichier téléchargé, on arrête le timer et on signale l'événement
            self.json_data = self.download_button.json_data  # Assurez-vous que json_data est défini
            self.checkTimer.stop()
            self.checkTimer.stop()
            self.fileDownloaded.emit()  # Signaler que le fichier est téléchargé
        # Sinon, rien n'est fait

