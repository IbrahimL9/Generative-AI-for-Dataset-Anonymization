from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QPushButton
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QRect, Qt, QSize
from .Menu import Menu
from views.pages.home import HomePage
from views.pages.model_params import ModelParametersPage
from views.pages.generate_data import GenerateDataPage
from views.pages.analysis_params import AnalysisParametersPage
from views.pages.analysis import AnalysisPage
from views.pages.about import AboutPage
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

        # Sidebar (Menu)
        self.menu = Menu()
        main_layout.addWidget(self.menu)
        self.download_button = DownloadButton('Download File')

        # Passer la même instance du bouton à HomePage et GenerateDataPage
        self.home_page = HomePage(self.download_button)
        self.generate_data_page = GenerateDataPage(self.download_button)

        # Bouton "prev" placé juste après le menu
        self.prev_button = QPushButton()
        self.prev_button.setIcon(QIcon("prev.png"))
        self.prev_button.setIconSize(QSize(80, 80))
        self.prev_button.setStyleSheet("border: none;")
        self.prev_button.setFixedSize(QSize(70, 70))
        self.prev_button.clicked.connect(self.prev_page)
        main_layout.addWidget(self.prev_button, alignment=Qt.AlignmentFlag.AlignBottom)

        # QStackedWidget pour les pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Ajout des pages
        self.pages = [
            self.home_page,
            ModelParametersPage(),
            self.generate_data_page,
            AnalysisParametersPage(),
            AnalysisPage(),
            AboutPage()
        ]
        for page in self.pages:
            self.stacked_widget.addWidget(page)

        # Connexion des signaux pour synchroniser menu et stacked widget
        self.menu.page_changed.connect(self.stacked_widget.setCurrentIndex)
        self.stacked_widget.currentChanged.connect(self.menu.setCurrentRow)

        # Ajouter un stretch pour pousser le prochain bouton à droite
        main_layout.addStretch()

        # Bouton "next" en extrémité droite
        self.next_button = QPushButton()
        self.next_button.setIcon(QIcon("next.png"))
        self.next_button.setIconSize(QSize(80, 80))
        self.next_button.setStyleSheet("border: none;")
        self.next_button.setFixedSize(QSize(70, 70))
        self.next_button.clicked.connect(self.next_page)
        main_layout.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.setLayout(main_layout)

    def centerWindow(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width = 1000
        window_height = 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def next_page(self):
        current_index = self.stacked_widget.currentIndex()
        next_index = (current_index + 1) % len(self.pages)
        self.stacked_widget.setCurrentIndex(next_index)

    def prev_page(self):
        current_index = self.stacked_widget.currentIndex()
        prev_index = (current_index - 1) % len(self.pages)
        self.stacked_widget.setCurrentIndex(prev_index)
