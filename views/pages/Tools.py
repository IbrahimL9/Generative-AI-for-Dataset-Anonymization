from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from views.Styles import BUTTON_STYLE


class Tools(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Layout principal
        main_layout = QVBoxLayout()

        # Titre de la page
        title_label = QLabel("Tools")
        title_label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Titre pour la section des paramètres
        param_title = QLabel("Model Parameters :")
        param_title.setFont(QFont("Montserrat", 12, QFont.Weight.Bold))
        main_layout.addWidget(param_title)

        # Layout en formulaire pour les champs de saisie
        form_layout = QFormLayout()

        # Champ : Number of Epochs (valeur par défaut : 200)
        self.epochs_edit = QLineEdit("200")
        form_layout.addRow(QLabel("Number of Epochs"), self.epochs_edit)

        # Champ : Generator Learning Rate (valeur par défaut : 0.002)
        self.gen_lr_edit = QLineEdit("0.002")
        form_layout.addRow(QLabel("Generator Learning Rate"), self.gen_lr_edit)

        # Champ : Batch size (valeur par défaut : 500)
        self.batch_size_edit = QLineEdit("500")
        form_layout.addRow(QLabel("Batch size"), self.batch_size_edit)

        # Champ : Discriminator Learning Rate (valeur par défaut : 0.002)
        self.disc_lr_edit = QLineEdit("0.002")
        form_layout.addRow(QLabel("Discriminator Learning Rate"), self.disc_lr_edit)

        # Champ : Number of data to generate (valeur par défaut : 2000)
        self.data_to_generate_edit = QLineEdit("2000")
        form_layout.addRow(QLabel("Number of data to generate"), self.data_to_generate_edit)

        # Champ : Enforce Min/Max Constraints (valeur par défaut : True)
        self.minmax_combo = QComboBox()
        self.minmax_combo.addItems(["True", "False"])
        # Sélectionne "True" par défaut
        self.minmax_combo.setCurrentIndex(0)
        form_layout.addRow(QLabel("Enforce Min/Max Constraints"), self.minmax_combo)

        # Ajouter le formulaire au layout principal
        main_layout.addLayout(form_layout)

        # Bouton SAVE, centré horizontalement
        save_button_layout = QHBoxLayout()
        self.save_button = QPushButton("SAVE")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        # Ajuster la taille du bouton si nécessaire
        self.save_button.setFixedSize(140, 50)
        save_button_layout.addStretch()
        save_button_layout.addWidget(self.save_button)
        save_button_layout.addStretch()
        main_layout.addLayout(save_button_layout)

        # Appliquer le layout principal
        self.setLayout(main_layout)
