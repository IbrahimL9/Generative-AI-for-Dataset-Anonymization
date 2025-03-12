from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QDialog, QComboBox, \
    QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
import pickle
# Définir les styles
from views.Styles import BUTTON_STYLE


class New(QWidget):
    model_loaded = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.model = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Titre de la page
        label = QLabel("New Model")
        label.setFont(QFont("Montserrat", 16, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addWidget(label)
        main_layout.addItem(QSpacerItem(20, 200, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))


        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        row_layout.setContentsMargins(0, 20, 0, 0)

        self.new_model_button = QPushButton("New")
        self.new_model_button.setStyleSheet(BUTTON_STYLE)
        self.new_model_button.setFixedWidth(200)
        self.new_model_button.clicked.connect(self.new_model)
        row_layout.addWidget(self.new_model_button)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["CTGAN", "OTHER"])
        self.model_combo.setCurrentIndex(0)  # CTGAN par défaut
        self.model_combo.setFixedWidth(150)
        row_layout.addWidget(self.model_combo)

        # Bouton "Load Model"
        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.setStyleSheet(BUTTON_STYLE)
        self.load_model_button.setFixedWidth(200)
        self.load_model_button.clicked.connect(self.load_model)
        row_layout.addWidget(self.load_model_button)

        main_layout.addLayout(row_layout)

        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def new_model(self):
        selected_model = self.model_combo.currentText()
        print("Nouveau modèle sélectionné :", selected_model)
        self.show_message(f"Nouveau modèle '{selected_model}' créé.")

    def load_model(self):
        anonymization_app = self.parent().parent()
        open_page = anonymization_app.get_open_page()

        if not open_page.json_data:
            self.show_message("Veuillez d'abord charger le fichier JSON dans la page Open.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Load Model", "", "Pickle Files (*.pkl)")
        if file_path:
            with open(file_path, 'rb') as f:
                self.model = pickle.load(f)
            print("Modèle chargé depuis le fichier :", file_path)
            self.show_message(f"Modèle chargé avec succès depuis {file_path}")

            self.model_loaded.emit(self.model)
            print("Signal de modèle chargé émis.")

    def show_message(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
