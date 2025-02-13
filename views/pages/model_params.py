from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolButton, QDialog, QTextEdit, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont 

class ModelParametersPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Model Parameters Page")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
