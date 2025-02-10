from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .Menu import Menu  # Importer la sidebar
from .Download_button import DownloadButton  # Importer le bouton de téléchargement

class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generative AI for Dataset Anonymization")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: white;")

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 0)
        main_layout.setSpacing(20)

        # Sidebar
        sidebar = Menu()
        main_layout.addWidget(sidebar)

        # Zone de contenu principal
        content_layout = QVBoxLayout()
        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        # Bouton de téléchargement
        download_button = DownloadButton("Download Json file")
        content_layout.addWidget(download_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
