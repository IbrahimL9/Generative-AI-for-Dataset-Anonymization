from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QStackedWidget, QApplication, QMessageBox, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from .Menu import Menu
from views.pages.Open import Open
from views.pages.Display import Display
from views.pages.Inspect import Inspect
from views.pages.New import New
from views.pages.Build import Build
from views.pages.Tools import Tools
from views.pages.Analysis import Analysis
from views.pages.Save import Save
from views.pages.Generate import Generate
from views.Download_button import DownloadButton
from views.pages.Fidelity import Fidelity
from views.pages.Confidentiality import Confidentiality
import pandas as pd


class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.session_data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generative AI for Dataset Anonymization")
        self.centerWindow()
        self.setStyleSheet("background-color: white;")

        # Le layout principal
        main_layout = QVBoxLayout()

        # Crée une barre de titre vide juste pour la hauteur de la fenêtre
        title_layout = QHBoxLayout()

        # Le bouton Refresh
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumWidth(100)  # Définit une largeur minimale pour le bouton
        self.refresh_button.setMaximumWidth(100)  # Définit une largeur maximale pour le bouton
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4059A8;
                color: white;
                border: 2px solid red;
                padding: 5px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #35499B;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_application)

        # Ajouter le bouton Refresh au layout de la barre de titre (aligné à droite)
        title_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Ajouter la barre de titre à la fenêtre
        self.title_bar_widget = QWidget(self)
        self.title_bar_widget.setLayout(title_layout)
        self.title_bar_widget.setFixedHeight(40)  # Hauteur de la barre de titre

        # Ajouter la barre de titre en haut du layout principal
        main_layout.addWidget(self.title_bar_widget)

        # Layout pour le contenu (le menu et les pages)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 10, 0)
        content_layout.setSpacing(40)

        self.menu = Menu()
        content_layout.addWidget(self.menu)

        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        self.tools = Tools()

        # Définition des pages
        self.pages = {
            "open": Open(self.download_button),
            "display": Display(self.download_button, self),
            "inspect": Inspect(self.download_button, self),
            "new": New(self),
            "build": Build(self, self.download_button, self.tools),
            "tools": self.tools,
            "generate": Generate(self),
            "analysis": Analysis(self),
            "save": Save(self),
            "fidelity": Fidelity(self),
            "confidentiality": Confidentiality(self)
        }

        # Ajouter les pages au QStackedWidget
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)

        # Ajouter le layout du contenu dans le layout principal
        main_layout.addLayout(content_layout)

        # Appliquer le layout principal à la fenêtre
        self.setLayout(main_layout)

        self.connect_signals()

    def connect_signals(self):
        self.pages["new"].model_loaded.connect(self.pages["build"].on_model_loaded)
        self.pages["new"].model_loaded.connect(self.pages["generate"].on_model_loaded)
        self.pages["open"].fileLoaded.connect(self.pages["generate"].on_file_loaded)
        self.pages["generate"].data_generated_signal.connect(self.pages["save"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["confidentiality"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["fidelity"].on_data_generated)

    def centerWindow(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, page_key: str):
        if page_key == "refresh":
            self.refresh_application()
            return

        if page_key in ["display", "inspect"] and (
                not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None):
            QMessageBox.warning(self, "File Not Downloaded", "Please download a file before accessing this page.")
            return

        page_index = list(self.pages.keys()).index(page_key)
        self.stacked_widget.setCurrentIndex(page_index)

    def refresh_application(self):
        """Réinitialiser complètement l'application."""
        self.session_data = pd.DataFrame()

        # Réinitialiser les pages
        for page in self.pages.values():
            if hasattr(page, 'reset'):
                page.reset()  # Appelle la méthode reset de chaque page

        # Réinitialiser le menu
        self.menu.show_initial_submenu("Source", "Open file")
        self.menu.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)

        # Réinitialiser les données du bouton de téléchargement
        self.download_button.reset()

        # Réinitialiser les signaux
        self.connect_signals()

    def resetMenuSelection(self, index):
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        return self.pages["open"]
