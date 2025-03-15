from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QDialog, QComboBox, QProgressBar
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize
import pickle

from views.Styles import BUTTON_STYLE2, BUTTON_STYLE3


class New(QWidget):
    model_loaded = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.model = None
        self.model_selection_visible = False
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.addSpacing(30)

        # Titre positionné en haut
        title = QLabel("New Model")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addSpacing(5)
        # Layout des boutons
        button_layout = QHBoxLayout()

        # BOUTON "New Model"
        self.new_model_button = QPushButton("New Model")
        self.new_model_button.setStyleSheet(BUTTON_STYLE2)
        self.new_model_button.setFixedSize(200, 150)
        self.new_model_button.setIcon(QIcon("images/plus.png"))
        self.new_model_button.setIconSize(QSize(50, 50))
        self.new_model_button.clicked.connect(self.toggle_model_selection)
        button_layout.addWidget(self.new_model_button)

        # BOUTON "Load Model"
        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.setStyleSheet(BUTTON_STYLE2)
        self.load_model_button.setFixedSize(200, 150)
        self.load_model_button.setIcon(QIcon("images/foldr.png"))
        self.load_model_button.setIconSize(QSize(50, 50))
        self.load_model_button.clicked.connect(self.load_model)
        button_layout.addWidget(self.load_model_button)

        # BOUTON "Delete Model"
        self.delete_model_button = QPushButton("Delete Model")
        self.delete_model_button.setStyleSheet(BUTTON_STYLE2)
        self.delete_model_button.setFixedSize(200, 150)
        self.delete_model_button.setIcon(QIcon("images/delete.png"))
        self.delete_model_button.setIconSize(QSize(45, 45))
        self.delete_model_button.clicked.connect(self.delete_model)
        button_layout.addWidget(self.delete_model_button)

        main_layout.addLayout(button_layout)

        # Sélection du modèle (cachée au départ)
        self.model_selection_layout = QHBoxLayout()
        self.model_selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.model_selection_label = QLabel("Select Model :")
        self.model_selection_label.setFont(QFont("Arial", 12))
        self.model_selection_label.setVisible(False)
        self.model_selection_layout.addWidget(self.model_selection_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["CTGAN", "OTHER"])
        self.model_combo.setCurrentIndex(0)
        self.model_combo.setFixedWidth(150)
        self.model_combo.setVisible(False)
        self.model_selection_layout.addWidget(self.model_combo)

        main_layout.addLayout(self.model_selection_layout)

        # Ajout d'un espacement pour descendre le bouton Continue
        main_layout.addSpacing(60)

        # Bouton Continue
        self.continue_button = QPushButton("Continue")
        self.continue_button.setStyleSheet(BUTTON_STYLE3)
        self.continue_button.setFixedWidth(200)
        main_layout.addWidget(self.continue_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(70)

        self.setLayout(main_layout)

    def toggle_model_selection(self):
        self.model_selection_visible = not self.model_selection_visible
        self.model_combo.setVisible(self.model_selection_visible)
        self.model_selection_label.setVisible(self.model_selection_visible)

    def new_model(self):
        selected_model = self.model_combo.currentText()
        print("Nouveau modèle sélectionné :", selected_model)
        self.show_message(f"Nouveau modèle '{selected_model}' créé.")

    def load_model(self):
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()

        if not open_page.json_data:
            self.show_message("Erreur : Veuillez d'abord charger le fichier JSON dans la page Open.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Load Model", "", "Pickle Files (*.pkl)")

        if file_path:
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(20)

                with open(file_path, 'rb') as f:
                    self.model = pickle.load(f)

                self.progress_bar.setValue(100)
                self.progress_bar.setVisible(False)

                print("Modèle chargé depuis le fichier :", file_path)
                self.show_message(f"Modèle chargé avec succès depuis {file_path}")

                self.model_loaded.emit(self.model)
                print("Signal de modèle chargé émis.")
            except Exception as e:
                self.progress_bar.setVisible(False)
                self.show_message(f"Erreur lors du chargement du modèle.\nDétails : {str(e)}")

    def delete_model(self):
        """Supprime le modèle actuellement chargé."""
        if self.model:
            self.model = None
            self.show_message("Modèle supprimé avec succès.")
            print("Modèle supprimé.")
        else:
            self.show_message("Aucun modèle à supprimer.")

    def show_message(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
