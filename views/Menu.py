from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from .Styles import SIDEBAR_STYLE

class Menu(QListWidget):
    page_changed = pyqtSignal(int)  # Signal pour indiquer un changement de page

    def __init__(self):
        super().__init__()
        self.setFixedWidth(170)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(SIDEBAR_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # Définition des pages
        self.labels = ["Home Page", "Model Parameters", "Generate Data",
                       "Analysis Parameters", "Analysis", "About"]

        for text in self.labels:
            item = QListWidgetItem(text)
            font = QFont("Montserrat", 10, QFont.Weight.DemiBold)
            item.setFont(font)
            self.addItem(item)

        self.setCurrentRow(0)  # Page d'accueil par défaut

        # Desactiver le menu si aucun fichier telecharger
        self.setEnabled(False)

        # Connecter la sélection au changement de page
        self.currentRowChanged.connect(self.page_changed.emit)

    def setMenuEnabled(self, enabled: bool):
        for index in range(self.count()):
            item = self.item(index)
            if item.text() != "About":
                if enabled:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
