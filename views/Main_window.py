# AnonymizationApp.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from .Menu import Menu
from views.pages.Open import Open
from views.pages.Display import Display
from views.pages.Inspect import Inspect
from views.pages.New import New
from views.pages.Build import Build
from views.pages.Tools import Tools
from views.pages.Generate import Generate
from views.pages.Analysis import Analysis
from views.pages.Save import Save   # Ajout de l'import pour la page Save
from views.Download_button import DownloadButton

class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generative AI for Dataset Anonymization")
        self.centerWindow()
        self.setStyleSheet("background-color: white;")

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 0)
        main_layout.setSpacing(40)

        # Barre latérale (Menu)
        self.menu = Menu()
        main_layout.addWidget(self.menu)

        # Bouton de téléchargement
        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        # QStackedWidget pour gérer les pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Ajout des pages dans le QStackedWidget
        self.pages = [
            Open(self.download_button),         # Index 0 – Open
            Display(self.download_button),        # Index 1 – Display
            Inspect(self.download_button),        # Index 2 – Inspect
            New(),                                # Index 3 – New
            Build(),                              # Index 4 – Build
            Tools(),                              # Index 5 – Tools
            Generate(self),                       # Index 6 – Generate (passage de self)
            Analysis(),                           # Index 7 – Analysis
            Save(self)                            # Index 8 – Save (passage de self)
        ]
        for page in self.pages:
            self.stacked_widget.addWidget(page)

        # Connexion du signal du menu aux changements de pages
        self.menu.page_changed.connect(self.changePage)

        # Affichage de la page d'accueil par défaut
        self.stacked_widget.setCurrentIndex(0)
        self.setLayout(main_layout)

        # Récupération des pages spécifiques
        self.new_page = self.pages[3]    # Index 3 – New
        self.build_page = self.pages[4]  # Index 4 – Build
        self.generate_page = self.pages[6]  # Index 6 – Generate
        self.save_page = self.pages[8]   # Index 8 – Save

        # Connexion du signal du modèle chargé (New → Build et Generate)
        self.new_page.model_loaded.connect(self.build_page.on_model_loaded)
        self.new_page.model_loaded.connect(self.generate_page.on_model_loaded)

        # Connexion du signal de fichier chargé (Open → Generate et Save)
        self.pages[0].fileLoaded.connect(self.generate_page.on_file_loaded)
        self.pages[0].fileLoaded.connect(self.save_page.on_file_loaded)

    def centerWindow(self):
        """Centre la fenêtre sur l'écran."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width = 1000
        window_height = 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        """Active le menu une fois qu'un fichier est chargé."""
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, index):
        """Change la page affichée en vérifiant les conditions d'accès."""
        print(f"Changing page to index: {index}")
        currentIndex = self.stacked_widget.currentIndex()

        # Vérification avant d'accéder aux pages Display et Inspect
        if index in [1, 2]:
            if not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None:
                print("File not loaded, showing warning.")
                QMessageBox.warning(
                    self,
                    "Fichier non téléchargé",
                    "Veuillez télécharger un fichier avant d'accéder à cette page."
                )
                QTimer.singleShot(0, lambda: self.resetMenuSelection(currentIndex))
                return

        self.stacked_widget.setCurrentIndex(index)

    def resetMenuSelection(self, index):
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        """Retourne la page Open (index 0)."""
        return self.pages[0]
