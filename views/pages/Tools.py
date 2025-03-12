from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox
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
        title_label = QLabel("Model Parameters")
        title_label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Spacer après le titre
        main_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Titre pour la section des paramètres
        param_title = QLabel("CTGAN MODEL :")
        param_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        main_layout.addWidget(param_title)

        main_layout.addItem(QSpacerItem(10, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Layout pour les paramètres (Grille)
        param_layout = QGridLayout()
        param_layout.setHorizontalSpacing(40)
        param_layout.setVerticalSpacing(20)

        # Fonction pour créer un label et un champ de saisie
        def create_label_input_field(label_text, input_widget):
            layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(label)
            layout.addWidget(input_widget)
            return layout

        # Champs avec valeurs par défaut
        self.epochs_edit = QLineEdit("200")
        self.batch_size_edit = QLineEdit("500")
        self.gen_lr_edit = QLineEdit("0.002")
        self.disc_lr_edit = QLineEdit("0.002")
        self.embedding_dim_edit = QLineEdit("128")
        self.generator_dim_edit = QLineEdit("256,256")  # Liste sous forme de string
        self.discriminator_dim_edit = QLineEdit("256,256")  # Liste sous forme de string
        self.pac_edit = QLineEdit("10")
        self.data_to_generate_edit = QLineEdit("2000")

        self.verbose_combo = QComboBox()
        self.verbose_combo.addItems(["True", "False"])
        self.verbose_combo.setCurrentIndex(0)  # "True" par défaut

        self.minmax_combo = QComboBox()
        self.minmax_combo.addItems(["True", "False"])
        self.minmax_combo.setCurrentIndex(0)  # "True" par défaut

        # Ajout des paramètres à la grille (2 par ligne)
        param_layout.addLayout(create_label_input_field("Number of Epochs", self.epochs_edit), 0, 0)
        param_layout.addLayout(create_label_input_field("Batch Size", self.batch_size_edit), 0, 1)
        param_layout.addLayout(create_label_input_field("Generator Learning Rate", self.gen_lr_edit), 1, 0)
        param_layout.addLayout(create_label_input_field("Discriminator Learning Rate", self.disc_lr_edit), 1, 1)
        param_layout.addLayout(create_label_input_field("Embedding Dimension", self.embedding_dim_edit), 2, 0)
        param_layout.addLayout(create_label_input_field("Generator Dimensions", self.generator_dim_edit), 2, 1)
        param_layout.addLayout(create_label_input_field("Discriminator Dimensions", self.discriminator_dim_edit), 3, 0)
        param_layout.addLayout(create_label_input_field("PAC (Grouping Factor)", self.pac_edit), 3, 1)
        param_layout.addLayout(create_label_input_field("Verbose Mode", self.verbose_combo), 4, 0)
        param_layout.addLayout(create_label_input_field("Enforce Min/Max Constraints", self.minmax_combo), 4, 1)
        param_layout.addLayout(create_label_input_field("Number of Data to Generate", self.data_to_generate_edit), 5, 0)

        main_layout.addLayout(param_layout)

        # Spacer pour ne pas coller le bouton
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bouton SAVE
        save_button_layout = QHBoxLayout()
        self.save_button = QPushButton("SAVE")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(140, 50)
        save_button_layout.addStretch()
        save_button_layout.addWidget(self.save_button)
        save_button_layout.addStretch()
        main_layout.addLayout(save_button_layout)

        self.save_button.clicked.connect(self.show_save_message)

        # Spacer en bas pour équilibrer
        main_layout.addItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Appliquer le layout principal
        self.setLayout(main_layout)

    def show_save_message(self):
        QMessageBox.information(self, "Save", "Changes have been saved.")
