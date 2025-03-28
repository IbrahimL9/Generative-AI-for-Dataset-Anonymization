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
from views.pages.Fidelity import Fidelity
from views.pages.Confidentiality import Confidentiality

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

        # Add the download button
        self.download_button = DownloadButton('Download File')
        self.download_button.file_loaded.connect(self.enableMenu)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.tools = Tools()

        # Define the pages
        self.pages = {
            "open": Open(self.download_button),
            "display": Display(self.download_button, self),
            "inspect": Inspect(self.download_button,self),
            "new": New(self),
            "build": Build(self, self.download_button, self.tools),
            "tools": self.tools,
            "generate": Generate(self),
            "analysis": Analysis(self),
            "save": Save(self),
            "fidelity": Fidelity(self),
            "confidentiality": Confidentiality(self)
        }

        # Add pages to QStackedWidget
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        # Connect signals and slots
        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)
        self.setLayout(main_layout)

        self.connect_signals()

    def connect_signals(self):
        # Connect signals between pages
        self.pages["new"].model_loaded.connect(self.pages["build"].on_model_loaded)
        self.pages["new"].model_loaded.connect(self.pages["generate"].on_model_loaded)
        self.pages["open"].fileLoaded.connect(self.pages["generate"].on_file_loaded)
        self.pages["generate"].data_generated_signal.connect(self.pages["save"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["confidentiality"].on_data_generated)

    def centerWindow(self):
        """Center the main window."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        """Enable the menu when the file is loaded."""
        print("Menu enabled")
        self.menu.setEnabled(True)

    def changePage(self, page_key: str):
        if page_key in ["display", "inspect"] and (
                not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None):
            QMessageBox.warning(self, "File Not Downloaded", "Please download a file before accessing this page.")
            return

        page_index = list(self.pages.keys()).index(page_key)
        self.stacked_widget.setCurrentIndex(page_index)

    def resetMenuSelection(self, index):
        """Reset the menu selection when the page changes."""
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        """Return the Open page."""
        return self.pages["open"]
