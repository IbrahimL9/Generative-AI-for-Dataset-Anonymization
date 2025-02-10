from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .Styles import SIDEBAR_STYLE

class Menu(QListWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(170)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(SIDEBAR_STYLE)

        labels = ["Label xxx", "Label xxx", "label yyy", "Label xxx", "Label xxx"]
        for text in labels:
            item = QListWidgetItem(text)
            font = QFont("Arial", 13, QFont.Weight.DemiBold)
            item.setFont(font)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)
        self.setCurrentRow(2)
