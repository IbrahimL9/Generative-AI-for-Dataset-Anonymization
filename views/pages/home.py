from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from views.Download_button import DownloadButton  # Importer le bouton de téléchargement

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Utiliser un espacement précis en pixels pour mieux positionner le titre
        layout.addSpacing(30)

        # Titre de l'application
        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ajuster l'espace flexible pour bien placer le bouton
        layout.addStretch(1)

        # Bouton de téléchargement
        download_button = DownloadButton("Download File")
        layout.addWidget(download_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Réduire l'espace en bas pour éviter que tout descende trop
        layout.addStretch(2)

        self.setLayout(layout)
