from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QStackedWidget, QApplication, QMessageBox
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

class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generative AI for Dataset Anonymization")
        self.centerWindow()
        self.setStyleSheet("background-color: white;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 0)
        main_layout.setSpacing(40)

        self.menu = Menu()
        main_layout.addWidget(self.menu)

        # Ajout du bouton de téléchargement
        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.tools = Tools()

        # Définir les pages
        self.pages = {
            "open": Open(self.download_button),
            "display": Display(self.download_button),
            "inspect": Inspect(self.download_button),
            "new": New(),
            "build": Build(self, self.download_button, self.tools),
            "tools": self.tools,
            "generate": Generate(self),
            "analysis": Analysis(self),
            "save": Save(self)
        }

        # Ajouter les pages au QStackedWidget
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        # Connexion des signaux et des slots
        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)
        self.setLayout(main_layout)

        self.connect_signals()

    def connect_signals(self):
        # Connexion des signaux entre les pages
        self.pages["new"].model_loaded.connect(self.pages["build"].on_model_loaded)
        self.pages["new"].model_loaded.connect(self.pages["generate"].on_model_loaded)
        self.pages["open"].fileLoaded.connect(self.pages["generate"].on_file_loaded)
        self.pages["generate"].data_generated_signal.connect(self.pages["save"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["analysis"].on_data_generated)

    def centerWindow(self):
        """Centre la fenêtre principale."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        """Activer le menu lorsque le fichier est chargé."""
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, index):
        """Changer de page avec vérification du fichier téléchargé."""
        # Vérification pour les pages Open, Display, Inspect reste inchangée
        if index in [1, 2] and (
                not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None):
            QMessageBox.warning(
                self,
                "Fichier non téléchargé",
                "Veuillez télécharger un fichier avant d'accéder à cette page."
            )
            return

        self.stacked_widget.setCurrentIndex(index)

    def resetMenuSelection(self, index):
        """Réinitialiser la sélection du menu lorsque la page change."""
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        """Retourne la page Open."""
        return self.pages["open"]
