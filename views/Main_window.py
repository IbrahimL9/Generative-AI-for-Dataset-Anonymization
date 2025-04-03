from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
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

        # -- Layout principal horizontal (inchangé) --
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 0)
        main_layout.setSpacing(40)

        # -- Menu à gauche (inchangé) --
        self.menu = Menu()
        main_layout.addWidget(self.menu)

        # -- Bouton Download (inchangé) --
        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        # -- Layout vertical pour la zone de droite --
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # -- StackedWidget (inchangé) --
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        # -- Un stretch pour pousser le bouton refresh en bas --
        right_layout.addStretch(1)

        # -- Bouton Refresh en bas à droite --
        self.refresh_button = QPushButton("")
        # Assurez-vous que le chemin vers l'icône est correct
        self.refresh_button.setIcon(QIcon("images/reset.png"))
        self.refresh_button.setIconSize(QSize(40, 40))
        self.refresh_button.setFixedSize(60, 60)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_application)
        right_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        # -- On ajoute le layout vertical à la droite du main_layout --
        main_layout.addLayout(right_layout)

        # -- Instanciation de la classe Tools (inchangé) --
        self.tools = Tools()

        # -- Définition des pages (inchangé) --
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

        # -- Ajout des pages au StackedWidget (inchangé) --
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)

        # -- On applique le layout principal à la fenêtre --
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
        """Centre la fenêtre principale."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        """Active le menu une fois le fichier chargé."""
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, page_key: str):
        if page_key in ["display", "inspect"] and (
            not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None
        ):
            QMessageBox.warning(self, "File Not Downloaded", "Please download a file before accessing this page.")
            return
        page_index = list(self.pages.keys()).index(page_key)
        self.stacked_widget.setCurrentIndex(page_index)

    def refresh_application(self):
        """Réinitialiser complètement l'application."""
        self.session_data = pd.DataFrame()
        for page in self.pages.values():
            if hasattr(page, 'reset'):
                page.reset()
        self.menu.show_initial_submenu("Source", "Open file")
        self.menu.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)
        self.download_button.reset()
        self.connect_signals()

    def resetMenuSelection(self, index):
        """Réinitialise la sélection du menu lors du changement de page."""
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        """Retourne la page 'Open'."""
        return self.pages["open"]


