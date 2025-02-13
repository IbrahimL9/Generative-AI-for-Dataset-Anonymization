import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolButton, QDialog, QTextEdit
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer

class HomePage(QWidget):
    def __init__(self, download_button):
        super().__init__()
        self.download_button = download_button
        self.initUI()

        # Créer un timer qui vérifie périodiquement si un fichier a été téléchargé.
        self.checkTimer = QTimer(self)
        self.checkTimer.timeout.connect(self.updateViewButtonState)
        self.checkTimer.start(500)  # Vérifie toutes les 500 ms

    def initUI(self):
        layout = QVBoxLayout()

        # Espacement en haut
        layout.addSpacing(30)

        # Titre de l'application
        title = QLabel("Generative AI for Dataset Anonymization")
        title.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Espace flexible pour positionner les widgets vers le haut
        layout.addStretch(1)

        # Layout horizontal pour les boutons
        button_layout = QHBoxLayout()
        # Ajouter un stretch pour centrer le contenu du layout horizontal
        button_layout.addStretch()

        # Bouton de téléchargement (restant au centre)
        button_layout.addWidget(self.download_button)

        # Espacement entre les boutons
        button_layout.addSpacing(10)

        # Bouton "œil" pour visualiser le fichier généré
        self.view_button = QToolButton()
        # Construction du chemin absolu vers l'icône "eye.png"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        eye_icon_path = os.path.join(current_dir, "..", "eye.png")
        self.view_button.setIcon(QIcon(eye_icon_path))
        self.view_button.setIconSize(QSize(32, 32))
        # Supprimer les bordures du bouton "œil"
        self.view_button.setStyleSheet("QToolButton { border: none; }")
        self.view_button.setToolTip("View generated file")
        self.view_button.clicked.connect(self.view_generated_file)
        button_layout.addWidget(self.view_button)

        # Espacement entre le bouton "œil" et le bouton "stats"
        button_layout.addSpacing(10)

        # Bouton "Stats" pour afficher les statistiques du fichier généré
        self.stats_button = QToolButton()
        # Construction du chemin absolu vers l'icône "statistiques.png"
        stats_icon_path = os.path.join(current_dir, "..", "statistiques.png")
        self.stats_button.setIcon(QIcon(stats_icon_path))
        self.stats_button.setIconSize(QSize(32, 32))
        self.stats_button.setStyleSheet("QToolButton { border: none; }")
        self.stats_button.setToolTip("View file statistics")
        self.stats_button.clicked.connect(self.view_statistics)
        button_layout.addWidget(self.stats_button)

        # Ajouter un stretch pour centrer l'ensemble du layout horizontal
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Réduire l'espace en bas pour éviter que tout descende trop
        layout.addStretch(2)

        self.setLayout(layout)

        # Désactiver par défaut les boutons "œil" et "stats"
        self.view_button.setEnabled(False)
        self.stats_button.setEnabled(False)

    def updateViewButtonState(self):
        """
        Vérifie si un fichier a été téléchargé en regardant l'attribut json_data
        du bouton de téléchargement et active les boutons "œil" et "stats" le cas échéant.
        """
        if self.download_button.json_data is not None:
            self.view_button.setEnabled(True)
            self.stats_button.setEnabled(True)
            self.checkTimer.stop()  # Arrêter le timer une fois le fichier téléchargé
        else:
            self.view_button.setEnabled(False)
            self.stats_button.setEnabled(False)

    def view_generated_file(self):
        """
        Ouvre une fenêtre de dialogue pour afficher le contenu du fichier généré.
        On suppose que le contenu est stocké dans self.download_button.json_data.
        """
        if self.download_button.json_data is not None:
            dialog = QDialog(self)
            dialog.setWindowTitle("View Generated File")
            dialog_layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText(str(self.download_button.json_data))
            text_edit.setReadOnly(True)
            dialog_layout.addWidget(text_edit)
            dialog.exec()
        else:
            dialog = QDialog(self)
            dialog.setWindowTitle("No File Available")
            dialog_layout = QVBoxLayout(dialog)
            message = QLabel("No generated file available. Please download a file first.")
            dialog_layout.addWidget(message)
            dialog.exec()

    def view_statistics(self):
        """
        Ouvre une fenêtre de dialogue pour afficher les statistiques du fichier généré.
        Par exemple, si le fichier est au format JSON, on peut afficher le nombre de clés
        ou d'éléments. Ici, un message simple de placeholder est utilisé.
        """
        if self.download_button.json_data is not None:
            dialog = QDialog(self)
            dialog.setWindowTitle("File Statistics")
            dialog_layout = QVBoxLayout(dialog)
            data = self.download_button.json_data
            # Exemple simple : si data est un dictionnaire, afficher le nombre de clés
            if isinstance(data, dict):
                stats = f"Number of keys: {len(data)}"
            elif isinstance(data, list):
                stats = f"Number of items: {len(data)}"
            else:
                stats = "No statistical data available."
            stats_label = QLabel(stats)
            dialog_layout.addWidget(stats_label)
            dialog.exec()
        else:
            dialog = QDialog(self)
            dialog.setWindowTitle("No File Available")
            dialog_layout = QVBoxLayout(dialog)
            message = QLabel("No generated file available. Please download a file first.")
            dialog_layout.addWidget(message)
            dialog.exec()
