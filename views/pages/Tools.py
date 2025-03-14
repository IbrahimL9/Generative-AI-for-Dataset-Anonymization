import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox, 
    QDialog, QDialogButtonBox, QInputDialog, QListWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from views.Styles import BUTTON_STYLE, LINEEDIT_STYLE, COMBOBOX_STYLE , HISTORY_DIALOG_STYLE

MAX_PARAMS = 100  # Limite de paramètres sauvegardés

class Tools(QWidget):
    def __init__(self):
        super().__init__()
        self.saved_params = {}  
        self.load_saved_parameters()  
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        title_label = QLabel("Model Parameters")
        title_label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        main_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        param_title = QLabel("CTGAN MODEL :")
        param_title.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        main_layout.addWidget(param_title)

        main_layout.addItem(QSpacerItem(10, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        param_layout = QGridLayout()
        param_layout.setHorizontalSpacing(40)
        param_layout.setVerticalSpacing(20)

        def create_label_input_field(label_text, input_widget):
            layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(label)
            layout.addWidget(input_widget)
            return layout

        self.epochs_edit = QLineEdit("200")
        self.batch_size_edit = QLineEdit("500")
        self.gen_lr_edit = QLineEdit("0.002")
        self.disc_lr_edit = QLineEdit("0.002")
        self.embedding_dim_edit = QLineEdit("128")
        self.generator_dim_edit = QLineEdit("256,256")
        self.discriminator_dim_edit = QLineEdit("256,256")
        self.pac_edit = QLineEdit("10")
        self.data_to_generate_edit = QLineEdit("2000")

        for field in [self.epochs_edit, self.batch_size_edit, self.gen_lr_edit, self.disc_lr_edit,
                      self.embedding_dim_edit, self.generator_dim_edit, self.discriminator_dim_edit,
                      self.pac_edit, self.data_to_generate_edit]:
            field.setStyleSheet(LINEEDIT_STYLE)

        self.verbose_combo = QComboBox()
        self.verbose_combo.addItems(["True", "False"])
        self.verbose_combo.setStyleSheet(COMBOBOX_STYLE)

        self.minmax_combo = QComboBox()
        self.minmax_combo.addItems(["True", "False"])
        self.minmax_combo.setStyleSheet(COMBOBOX_STYLE)

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
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        button_layout = QHBoxLayout()

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet(BUTTON_STYLE)
        self.confirm_button.setFixedSize(140, 50)
        self.confirm_button.clicked.connect(self.confirm_parameters)
        button_layout.addWidget(self.confirm_button)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedSize(140, 50)
        self.save_button.clicked.connect(self.save_parameters)
        button_layout.addWidget(self.save_button)

        self.select_button = QPushButton("Select")
        self.select_button.setStyleSheet(BUTTON_STYLE)
        self.select_button.setFixedSize(140, 50)
        self.select_button.clicked.connect(self.select_parameter)
        button_layout.addWidget(self.select_button)

        main_layout.addLayout(button_layout)
        main_layout.addItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(main_layout)

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
            QMessageBox.warning(self, "Limit Reached", "You have reached the maximum of 100 saved parameters. Please delete one before saving a new one.")
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

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.handle_selection(history_list_widget, history_dialog))
        button_box.rejected.connect(history_dialog.reject)
        history_layout.addWidget(button_box)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_parameter(history_list_widget))
        history_layout.addWidget(delete_button)

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
        # Charge les paramètres dans les champs correspondants
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
