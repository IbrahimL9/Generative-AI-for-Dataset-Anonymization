import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel

class Open(QWidget):
    fileDownloaded = pyqtSignal()
    fileLoaded = pyqtSignal()

    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.json_data = None
        self.loading_label = QLabel("")  # 👈 Ajout d'un label d'état
        self.initUI()

        self.download_button.file_loaded.connect(self.handle_file_loaded)

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(20)

        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

        layout.addStretch(2)

        self.setLayout(layout)

    def handle_file_loaded(self):
        if self.json_data is None:
            self.loading_label.setText("Data preprocessing in progress...")
            QTimer.singleShot(500, self.finish_loading)

    def finish_loading(self):
        self.json_data = self.download_button.json_data
        self.loading_label.setText("")
        self.fileDownloaded.emit()
