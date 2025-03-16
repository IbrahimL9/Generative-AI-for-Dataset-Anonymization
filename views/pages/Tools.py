import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox,
    QDialog, QDialogButtonBox, QInputDialog, QListWidget, QToolButton, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from views.Styles import BUTTON_STYLE, LINEEDIT_STYLE, COMBOBOX_STYLE, HISTORY_DIALOG_STYLE, INFO_MESSAGE_BOX_STYLE, \
    BUTTON_STYLE3

MAX_PARAMS = 100  # Maximum number of saved parameter sets

class Tools(QWidget):
    def __init__(self):
        super().__init__()
        self.saved_params = {}
        self.load_saved_parameters()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(0, 20, 0, 0)

        title_label = QLabel("Model Parameters")
        title_label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        main_layout.addSpacing(20)

        def create_form_row(text, widget, tooltip):
            """Crée un label avec puce et tooltip (ni le label ni le widget ne sont en gras),
            puis renvoie (label, widget)."""
            label = QLabel(f"• {text}")
            # Utilise un poids normal pour la police
            label.setFont(QFont("Montserrat", 10, QFont.Weight.Normal))
            label.setToolTip(tooltip)  # Affiche la bulle d'info au survol du label
            widget.setToolTip(tooltip)  # Affiche la bulle d'info au survol du champ
            return label, widget

        # -------- Layout principal en grille pour les sections --------
        sections_layout = QGridLayout()
        sections_layout.setHorizontalSpacing(50)
        sections_layout.setVerticalSpacing(30)

        # =======================================================================
        # SECTION TRAINING (colonne 0, ligne 0/1)
        # =======================================================================
        training_title = QLabel("Training")
        training_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))

        training_form = QFormLayout()
        training_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        training_form.setHorizontalSpacing(40)
        training_form.setVerticalSpacing(15)

        # Champs "Training"
        self.epochs_edit = QLineEdit("200")
        self.epochs_edit.setStyleSheet(LINEEDIT_STYLE)

        self.batch_size_edit = QLineEdit("500")
        self.batch_size_edit.setStyleSheet(LINEEDIT_STYLE)

        self.verbose_combo = QComboBox()
        self.verbose_combo.addItems(["True", "False"])
        self.verbose_combo.setStyleSheet(COMBOBOX_STYLE)

        # Ajout dans le form layout, avec tooltip pour chaque paramètre en minuscules
        label_epochs, widget_epochs = create_form_row(
            "number of epochs:",
            self.epochs_edit,
            "number of training iterations (epochs) to run during model training."
        )
        training_form.addRow(label_epochs, widget_epochs)

        label_batch, widget_batch = create_form_row(
            "batch size:",
            self.batch_size_edit,
            "number of samples processed in a single training batch."
        )
        training_form.addRow(label_batch, widget_batch)

        label_verbose, widget_verbose = create_form_row(
            "verbose mode:",
            self.verbose_combo,
            "display detailed training logs."
        )
        training_form.addRow(label_verbose, widget_verbose)

        # Placement dans la grille
        sections_layout.addWidget(training_title, 0, 0)  # Titre
        sections_layout.addLayout(training_form, 1, 0)  # Formulaire

        # =======================================================================
        # SECTION GENERATOR PARAMETERS (colonne 1, ligne 0/1)
        # =======================================================================
        generator_title = QLabel("Generator Parameters")
        generator_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))

        generator_form = QFormLayout()
        generator_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        generator_form.setHorizontalSpacing(40)
        generator_form.setVerticalSpacing(15)

        # Champs "Generator"
        self.gen_lr_edit = QLineEdit("0.002")
        self.gen_lr_edit.setStyleSheet(LINEEDIT_STYLE)

        self.generator_dim_edit = QLineEdit("256,256")
        self.generator_dim_edit.setStyleSheet(LINEEDIT_STYLE)

        self.embedding_dim_edit = QLineEdit("128")
        self.embedding_dim_edit.setStyleSheet(LINEEDIT_STYLE)

        # Ajout avec tooltip en minuscules
        label_gen_lr, widget_gen_lr = create_form_row(
            "generator learning rate:",
            self.gen_lr_edit,
            "step size used to update the generator's weights."
        )
        generator_form.addRow(label_gen_lr, widget_gen_lr)

        label_gen_dim, widget_gen_dim = create_form_row(
            "generator dimensions:",
            self.generator_dim_edit,
            "comma-separated list of neurons per hidden layer in the generator."
        )
        generator_form.addRow(label_gen_dim, widget_gen_dim)

        label_embed_dim, widget_embed_dim = create_form_row(
            "embedding dimension:",
            self.embedding_dim_edit,
            "dimension of the embedding vector for categorical features."
        )
        generator_form.addRow(label_embed_dim, widget_embed_dim)

        # Placement dans la grille
        sections_layout.addWidget(generator_title, 0, 1)
        sections_layout.addLayout(generator_form, 1, 1)

        # =======================================================================
        # SECTION DISCRIMINATOR PARAMETERS (colonne 0, ligne 2/3)
        # =======================================================================
        discriminator_title = QLabel("Discriminator Parameters")
        discriminator_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))

        discriminator_form = QFormLayout()
        discriminator_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        discriminator_form.setHorizontalSpacing(40)
        discriminator_form.setVerticalSpacing(15)

        # Champs "Discriminator"
        self.disc_lr_edit = QLineEdit("0.002")
        self.disc_lr_edit.setStyleSheet(LINEEDIT_STYLE)

        self.discriminator_dim_edit = QLineEdit("256,256")
        self.discriminator_dim_edit.setStyleSheet(LINEEDIT_STYLE)

        self.pac_edit = QLineEdit("10")
        self.pac_edit.setStyleSheet(LINEEDIT_STYLE)

        # Ajout avec tooltip en minuscules
        label_disc_lr, widget_disc_lr = create_form_row(
            "discriminator learning rate:",
            self.disc_lr_edit,
            "step size used to update the discriminator's weights."
        )
        discriminator_form.addRow(label_disc_lr, widget_disc_lr)

        label_disc_dim, widget_disc_dim = create_form_row(
            "discriminator dimensions:",
            self.discriminator_dim_edit,
            "comma-separated list of neurons per hidden layer in the discriminator."
        )
        discriminator_form.addRow(label_disc_dim, widget_disc_dim)

        label_pac, widget_pac = create_form_row(
            "pac (grouping factor):",
            self.pac_edit,
            "number of samples grouped together for the discriminator's loss calculation."
        )
        discriminator_form.addRow(label_pac, widget_pac)

        # Placement dans la grille
        sections_layout.addWidget(discriminator_title, 2, 0)
        sections_layout.addLayout(discriminator_form, 3, 0)

        # =======================================================================
        # SECTION ADVANCED OPTIONS (colonne 1, ligne 2/3)
        # =======================================================================
        advanced_title = QLabel("Advanced Options")
        advanced_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))

        advanced_form = QFormLayout()
        advanced_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        advanced_form.setHorizontalSpacing(40)
        advanced_form.setVerticalSpacing(15)

        # Champs "Advanced"
        self.minmax_combo = QComboBox()
        self.minmax_combo.addItems(["True", "False"])
        self.minmax_combo.setStyleSheet(COMBOBOX_STYLE)

        self.data_to_generate_edit = QLineEdit("2000")  # Ajout du champ manquant
        self.data_to_generate_edit.setStyleSheet(LINEEDIT_STYLE)

        # Ajout avec tooltip en minuscules
        label_minmax, widget_minmax = create_form_row(
            "enforce min/max constraints:",
            self.minmax_combo,
            "enforce minimum and maximum value constraints on the generated outputs."
        )
        advanced_form.addRow(label_minmax, widget_minmax)

        label_data_to_generate, widget_data_to_generate = create_form_row(
            "number of data to generate:",
            self.data_to_generate_edit,
            "number of data samples to generate."
        )
        advanced_form.addRow(label_data_to_generate, widget_data_to_generate)

        # Placement dans la grille
        sections_layout.addWidget(advanced_title, 2, 1)
        sections_layout.addLayout(advanced_form, 3, 1)

        # Ajout de la grille au layout principal
        main_layout.addLayout(sections_layout)

        # -------- Espace avant les boutons --------
        main_layout.addSpacing(30)

        # =======================================================================
        # BOUTONS EN BAS (Confirm, Save, Select)
        # =======================================================================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet(BUTTON_STYLE)
        self.confirm_button.setFixedSize(140, 50)
        self.confirm_button.clicked.connect(self.confirm_parameters)
        buttons_layout.addWidget(self.confirm_button)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(140, 50)
        self.save_button.clicked.connect(self.save_parameters)
        buttons_layout.addWidget(self.save_button)

        self.select_button = QPushButton("Select")
        self.select_button.setStyleSheet(BUTTON_STYLE)
        self.select_button.setFixedSize(140, 50)
        self.select_button.clicked.connect(self.select_parameter)
        buttons_layout.addWidget(self.select_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addSpacing(20)

        self.setLayout(main_layout)

    # Method to display the information popup
    def show_info_popup(self, param_name, param_info):
        """ Displays a dialog box with explanations for a parameter. """
        msg = QMessageBox(self)
        msg.setWindowTitle(param_name)
        msg.setText(param_info)
        msg.setStyleSheet(INFO_MESSAGE_BOX_STYLE)  # Apply style to the message box
        msg.setFixedSize(400, 300)
        msg.exec()

    def load_saved_parameters(self):
        if os.path.exists("params.json"):
            with open("params.json", "r") as file:
                try:
                    self.saved_params = json.load(file)
                except json.JSONDecodeError:
                    self.saved_params = {}
        else:
            self.saved_params = {}

    def save_parameters(self):
        if len(self.saved_params) >= MAX_PARAMS:
            QMessageBox.warning(self, "Limit Reached",
                                "You have reached the maximum of 100 saved parameters. Please delete one before saving a new one.")
            return

        name, ok = QInputDialog.getText(self, "Save Parameter", "Enter a name for this parameter set:")
        if ok and name:
            params = {
                "epochs": self.epochs_edit.text(),
                "batch_size": self.batch_size_edit.text(),
                "gen_lr": self.gen_lr_edit.text(),
                "disc_lr": self.disc_lr_edit.text(),
                "embedding_dim": self.embedding_dim_edit.text(),
                "generator_dim": self.generator_dim_edit.text(),
                "discriminator_dim": self.discriminator_dim_edit.text(),
                "pac": self.pac_edit.text(),
                "data_to_generate": self.data_to_generate_edit.text(),
                "verbose": self.verbose_combo.currentText(),
                "minmax": self.minmax_combo.currentText(),
            }

            self.saved_params[name] = params
            self.save_to_file()
            QMessageBox.information(self, "Save", f"Parameters have been saved as '{name}'.")

    def save_to_file(self):
        with open("params.json", "w") as file:
            json.dump(self.saved_params, file, indent=4)

    def select_parameter(self):
        self.load_saved_parameters()

        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("Select or Delete Parameter")
        history_dialog.setStyleSheet(HISTORY_DIALOG_STYLE)

        history_layout = QVBoxLayout()
        history_list_widget = QListWidget()
        history_list_widget.addItems(self.saved_params.keys())
        history_layout.addWidget(history_list_widget)

        # Création d'un layout horizontal pour aligner les 3 boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ok_button = QPushButton("Ok")
        ok_button.setStyleSheet("background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")
        ok_button.setFixedSize(100, 30)
        ok_button.clicked.connect(lambda: self.handle_selection(history_list_widget, history_dialog))
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")

        cancel_button.setFixedSize(100, 30)
        cancel_button.clicked.connect(history_dialog.reject)
        buttons_layout.addWidget(cancel_button)

        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")

        delete_button.setFixedSize(100, 30)
        delete_button.clicked.connect(lambda: self.delete_parameter(history_list_widget))
        buttons_layout.addWidget(delete_button)

        history_layout.addLayout(buttons_layout)

        history_dialog.setLayout(history_layout)
        history_dialog.exec()

    def handle_selection(self, history_list_widget, dialog):
        selected_item = history_list_widget.currentItem()
        if selected_item:
            selected_name = selected_item.text()
            self.load_selected_parameters(self.saved_params[selected_name])
        dialog.accept()

    def delete_parameter(self, history_list_widget):
        selected_item = history_list_widget.currentItem()
        if selected_item:
            selected_name = selected_item.text()
            del self.saved_params[selected_name]
            self.save_to_file()
            history_list_widget.takeItem(history_list_widget.row(selected_item))
            QMessageBox.information(self, "Deleted", f"Parameter '{selected_name}' has been deleted.")

    def load_selected_parameters(self, params):
        # Load parameters into the corresponding fields
        self.epochs_edit.setText(params["epochs"])
        self.batch_size_edit.setText(params["batch_size"])
        self.gen_lr_edit.setText(params["gen_lr"])
        self.disc_lr_edit.setText(params["disc_lr"])
        self.embedding_dim_edit.setText(params["embedding_dim"])
        self.generator_dim_edit.setText(params["generator_dim"])
        self.discriminator_dim_edit.setText(params["discriminator_dim"])
        self.pac_edit.setText(params["pac"])
        self.data_to_generate_edit.setText(params["data_to_generate"])
        self.verbose_combo.setCurrentText(params["verbose"])
        self.minmax_combo.setCurrentText(params["minmax"])

    def confirm_parameters(self):
        QMessageBox.information(self, "Confirm", "Parameters have been confirmed.")
