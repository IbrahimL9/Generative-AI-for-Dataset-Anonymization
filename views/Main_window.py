# anonymization_app.py

import os
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# --- Controllers ---
from controllers.analysis_controller import AnalysisController
from controllers.generate_controller import GenerateController
from controllers.tools_controller import ToolsController
from controllers.display_controller import DisplayController
from controllers.inspect_controller import InspectController
from controllers.build_controller import BuildController
from controllers.save_controller import SaveController

# --- Views ---
from views.Menu import Menu
from views.pages.Open import Open
from views.pages.New import New
from views.pages.display_view import DisplayView
from views.pages.tools_view import ToolsView
from views.pages.analysis_view import AnalysisView
from views.pages.save_view import SaveView
from views.pages.generate_view import GenerateView
from views.pages.confidentiality import Confidentiality
from views.Download_button import DownloadButton
from views.pages.fidelity import Fidelity


class AnonymizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.session_data = pd.DataFrame()
        self.json_data = None
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

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        self.refresh_button = QPushButton("")
        self.refresh_button.setIcon(QIcon("images/reset.png"))
        self.refresh_button.setIconSize(QSize(40, 40))
        self.refresh_button.setFixedSize(60, 60)
        self.refresh_button.setVisible(False)
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

        main_layout.addLayout(right_layout)

        # --- Initialisation des vues et contrôleurs ---
        self.tools = ToolsView()
        self.tools_controller = ToolsController(self.tools)
        self.display_controller = DisplayController(self.download_button, self)
        self.inspect_controller = InspectController(self.download_button, self)
        self.build_controller = BuildController(self, self.download_button, self.tools)
        self.generate_view = GenerateView(self)
        self.generate_controller = GenerateController(self, self.generate_view)

        # ✅ Instanciation directe des vues monolithiques
        self.confidentiality_view = Confidentiality(self)
        self.fidelity_view = Fidelity(self)

        # --- Pages ---
        self.pages = {
            "open": Open(self.download_button),
            "display": DisplayView(self.download_button, self),
            "inspect": self.inspect_controller.view,
            "new": New(self),
            "build": self.build_controller.view,
            "tools": self.tools,
            "generate": self.generate_view,
            "analysis": AnalysisView(self),
            "save": SaveView(self),
            "fidelity": self.fidelity_view,
            "confidentiality": self.confidentiality_view
        }

        self.analysis_controller = AnalysisController(self, self.pages["analysis"])
        self.save_controller = SaveController(self, self.pages["save"])

        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        self.menu.page_changed.connect(self.changePage)
        self.stacked_widget.setCurrentIndex(0)
        self.setLayout(main_layout)
        self.connect_signals()

    def connect_signals(self):
        self.pages["new"].model_loaded.connect(self.pages["build"].on_model_loaded)
        self.pages["new"].model_loaded.connect(self.generate_controller.on_model_loaded)
        self.pages["open"].fileLoaded.connect(self.pages["generate"].on_file_loaded)
        self.pages["generate"].data_generated_signal.connect(self.pages["save"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["confidentiality"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.pages["fidelity"].on_data_generated)
        self.download_button.file_loaded.connect(self.pages["display"].updateTable)
        self.pages["generate"].data_generated_signal.connect(self.pages["save"].on_data_generated)
        self.pages["generate"].data_generated_signal.connect(self.save_controller.on_data_generated)

    def centerWindow(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width, window_height = 1000, 700
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

    def enableMenu(self):
        print("✅ File loaded. Menu enabled.")
        self.menu.setEnabled(True)
        self.json_data = self.download_button.json_data
        self.inspect_controller.schedule_update()

    def changePage(self, page_key: str):
        if page_key in ["display", "inspect"] and (
                not hasattr(self.download_button, 'json_data') or self.download_button.json_data is None
        ):
            QMessageBox.warning(self, "File Not Downloaded", "Please download a file before accessing this page.")
            return
        if page_key == "inspect":
            self.inspect_controller.schedule_update()
        self.stacked_widget.setCurrentIndex(list(self.pages.keys()).index(page_key))

    def refresh_application(self):
        print("🔄 Application reset.")
        self.session_data = pd.DataFrame()

        for page in self.pages.values():
            if hasattr(page, 'reset'):
                page.reset()

        self.menu.show_initial_submenu("Source", "Open file")
        self.menu.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)
        self.download_button.reset()
        self.connect_signals()
        self.display_controller.load_data()
        self.inspect_controller.schedule_update()

    def resetMenuSelection(self, index):
        self.menu.blockSignals(True)
        self.menu.setCurrentRow(index)
        self.menu.blockSignals(False)
        self.stacked_widget.setCurrentIndex(index)

    def get_open_page(self):
        return self.pages["open"]
