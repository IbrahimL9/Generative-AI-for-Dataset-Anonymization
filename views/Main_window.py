from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QStackedWidget, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
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

        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.pages = {
            "open": Open(self.download_button),
            "display": Display(self.download_button),
            "inspect": Inspect(self.download_button),
            "new": New(),
            "build": Build(self, self.download_button),
            "tools": Tools(),
            "generate": Generate(self),
            "analysis": Analysis(),
            "save": Save(self)
        }

        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)
        self.setLayout(main_layout)

        self.connect_signals()

    def connect_signals(self):
        self.pages["new"].model_loaded.connect(self.pages["build"].on_model_loaded)
        self.pages["new"].model_loaded.connect(self.pages["generate"].on_model_loaded)
        self.pages["open"].fileLoaded.connect(self.pages["generate"].on_file_loaded)

    def centerWindow(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, index):
        """Change la page affichée en vérifiant les conditions d'accès."""
        print(f"🔄 Changement de page vers l'index: {index}")

        # Vérification si on tente d'accéder à Display ou Inspect sans fichier chargé
        if index in [1, 2] and (
                not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None):
            QMessageBox.warning(
                self,
                "Fichier non téléchargé",
                "Veuillez télécharger un fichier avant d'accéder à cette page."
            )
            return

        # ✅ Vérification si on clique sur Save (index 8)
        if index == 8 and not self.pages["save"].data_generated:
            QMessageBox.warning(
                self,
                "Données non générées",
                "Veuillez d'abord générer des données avant de les sauvegarder."
            )
            return

        # ✅ Changement de page normal
        self.stacked_widget.setCurrentIndex(index)

    def resetMenuSelection(self, index):
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        return self.pages["open"]


