from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget
from .Menu import Menu
from .Download_button import DownloadButton
from views.pages.home import HomePage
from views.pages.model_params import ModelParametersPage
from views.pages.generate_data import GenerateDataPage
from views.pages.analysis_params import AnalysisParametersPage
from views.pages.analysis import AnalysisPage
from views.pages.about import AboutPage

class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generative AI for Dataset Anonymization")
        self.setGeometry(150, 150, 850, 550)
        self.setStyleSheet("background-color: white;")

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 0)
        main_layout.setSpacing(40)

        # Sidebar (Menu)
        self.menu = Menu()
        main_layout.addWidget(self.menu)

        # QStackedWidget pour contenir les pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Ajouter les pages au QStackedWidget
        self.pages = [
            HomePage(),                 # Index 0 - Page d'accueil
            ModelParametersPage(),      # Index 1 - Paramètres du modèle
            GenerateDataPage(),         # Index 2 - Génération de données
            AnalysisParametersPage(),   # Index 3 - Paramètres d'analyse
            AnalysisPage(),             # Index 4 - Analyse
            AboutPage()                 # Index 5 - À propos
        ]

        for page in self.pages:
            self.stacked_widget.addWidget(page)

        # Connecter le menu au QStackedWidget pour changer de page
        self.menu.page_changed.connect(self.stacked_widget.setCurrentIndex)

        self.setLayout(main_layout)
