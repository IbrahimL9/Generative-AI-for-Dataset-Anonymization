# tools_view.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QDialog, QMessageBox, QListWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from views.Styles import BUTTON_STYLE, LINEEDIT_STYLE, COMBOBOX_STYLE, HISTORY_DIALOG_STYLE, INFO_MESSAGE_BOX_STYLE, BUTTON_STYLE3

class ToolsView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 20, 0, 0)

        title_label = QLabel("Model Parameters")
        title_label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        main_layout.addSpacing(20)

        # Fonction utilitaire pour créer une ligne de formulaire
        def create_form_row(text, widget, tooltip):
            label = QLabel(f"• {text}")
            label.setFont(QFont("Montserrat", 10, QFont.Weight.Normal))
            label.setToolTip(tooltip)
            widget.setToolTip(tooltip)
            return label, widget

        # Layout en grille pour les sections
        self.sections_layout = QGridLayout()
        self.sections_layout.setHorizontalSpacing(50)
        self.sections_layout.setVerticalSpacing(30)

        # SECTION TRAINING (colonne 0, ligne 0/1)
        training_title = QLabel("Training")
        training_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        training_form = self._create_form_layout([
            ("number of epochs:", LINEEDIT_STYLE, "200", "number of training iterations (epochs) to run during model training."),
            ("batch size:", LINEEDIT_STYLE, "500", "number of samples processed in a single training batch."),
            ("verbose mode:", COMBOBOX_STYLE, None, "display detailed training logs.", "combo", ["True", "False"])
        ])
        self.epochs_edit = training_form['number of epochs:']
        self.batch_size_edit = training_form['batch size:']
        self.verbose_combo = training_form['verbose mode:']
        self.sections_layout.addWidget(training_title, 0, 0)
        self.sections_layout.addLayout(training_form['layout'], 1, 0)

        # SECTION GENERATOR PARAMETERS (colonne 1, ligne 0/1)
        generator_title = QLabel("Generator Parameters")
        generator_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        generator_form = self._create_form_layout([
            ("generator learning rate:", LINEEDIT_STYLE, "0.002", "step size used to update the generator's weights."),
            ("generator dimensions:", LINEEDIT_STYLE, "256,256", "comma-separated list of neurons per hidden layer in the generator."),
            ("embedding dimension:", LINEEDIT_STYLE, "128", "dimension of the embedding vector for categorical features.")
        ])
        self.gen_lr_edit = generator_form['generator learning rate:']
        self.generator_dim_edit = generator_form['generator dimensions:']
        self.embedding_dim_edit = generator_form['embedding dimension:']
        self.sections_layout.addWidget(generator_title, 0, 1)
        self.sections_layout.addLayout(generator_form['layout'], 1, 1)

        # SECTION DISCRIMINATOR PARAMETERS (colonne 0, ligne 2/3)
        discriminator_title = QLabel("Discriminator Parameters")
        discriminator_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        discriminator_form = self._create_form_layout([
            ("discriminator learning rate:", LINEEDIT_STYLE, "0.002", "step size used to update the discriminator's weights."),
            ("discriminator dimensions:", LINEEDIT_STYLE, "256,256", "comma-separated list of neurons per hidden layer in the discriminator."),
            ("pac (grouping factor):", LINEEDIT_STYLE, "10", "number of samples grouped together for the discriminator's loss calculation.")
        ])
        self.disc_lr_edit = discriminator_form['discriminator learning rate:']
        self.discriminator_dim_edit = discriminator_form['discriminator dimensions:']
        self.pac_edit = discriminator_form['pac (grouping factor):']
        self.sections_layout.addWidget(discriminator_title, 2, 0)
        self.sections_layout.addLayout(discriminator_form['layout'], 3, 0)

        # SECTION ADVANCED OPTIONS (colonne 1, ligne 2/3)
        advanced_title = QLabel("Advanced Options")
        advanced_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        advanced_form = self._create_form_layout([
            ("enforce min/max constraints:", COMBOBOX_STYLE, None,
             "enforce minimum and maximum value constraints on the generated outputs.", "combo", ["True", "False"]),
            ("number of data to generate:", LINEEDIT_STYLE, "2000", "number of data samples to generate.")
        ])

        self.minmax_combo = advanced_form['enforce min/max constraints:']
        self.data_to_generate_edit = advanced_form['number of data to generate:']
        self.sections_layout.addWidget(advanced_title, 2, 1)
        self.sections_layout.addLayout(advanced_form['layout'], 3, 1)

        main_layout.addLayout(self.sections_layout)
        main_layout.addSpacing(30)

        # Boutons en bas (Confirm, Save, Select)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet(BUTTON_STYLE)
        self.confirm_button.setFixedSize(140, 50)
        buttons_layout.addWidget(self.confirm_button)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(140, 50)
        buttons_layout.addWidget(self.save_button)

        self.select_button = QPushButton("Select")
        self.select_button.setStyleSheet(BUTTON_STYLE)
        self.select_button.setFixedSize(140, 50)
        buttons_layout.addWidget(self.select_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addSpacing(20)

        self.setLayout(main_layout)

    def _create_form_layout(self, items):
        """
        Crée un QFormLayout à partir d'une liste de tuples définissant :
         (label_text, style, default_value, tooltip[, type, extras])
        Le type par défaut est 'lineedit',
         pour une combobox, fournir type='combo' et une liste d'extras.
        Retourne un dictionnaire contenant le layout et chaque widget sous leur label.
        """
        from PyQt6.QtWidgets import QFormLayout, QLineEdit, QComboBox
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setHorizontalSpacing(40)
        form_layout.setVerticalSpacing(15)
        widgets = {}
        for item in items:
            label_text, style, default, tooltip = item[:4]
            w_type = item[4] if len(item) > 4 else "lineedit"
            extras = item[5] if len(item) > 5 else None
            label = QLabel(f"• {label_text}")
            label.setFont(QFont("Montserrat", 10))
            label.setToolTip(tooltip)
            if w_type == "lineedit":
                widget = QLineEdit(default)
                widget.setStyleSheet(style)
            elif w_type == "combo":
                widget = QComboBox()
                widget.setStyleSheet(style)
                if extras:
                    widget.addItems(extras)
            else:
                widget = QLineEdit(default)
                widget.setStyleSheet(style)
            widget.setToolTip(tooltip)
            form_layout.addRow(label, widget)
            widgets[label_text] = widget
        widgets['layout'] = form_layout
        return widgets

    def show_info_popup(self, param_name, param_info):
        msg = QMessageBox(self)
        msg.setWindowTitle(param_name)
        msg.setText(param_info)
        msg.setStyleSheet(INFO_MESSAGE_BOX_STYLE)
        msg.setFixedSize(400, 300)
        msg.exec()
