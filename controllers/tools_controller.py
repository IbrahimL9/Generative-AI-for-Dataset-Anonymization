# tools_controller.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QListWidget
from models.tools_model import ToolsModel


class ToolsController:
    def __init__(self, view: 'ToolsView'):
        self.view = view
        self.model = ToolsModel()
        self.connect_signals()

    def connect_signals(self):
        self.view.confirm_button.clicked.connect(self.confirm_parameters)
        self.view.save_button.clicked.connect(self.save_parameters)
        self.view.select_button.clicked.connect(self.select_parameter)

    def confirm_parameters(self):
        QMessageBox.information(self.view, "Confirm", "Parameters have been confirmed.")

    def save_parameters(self):
        if len(self.model.saved_params) >= self.model.MAX_PARAMS:
            QMessageBox.warning(self.view, "Limit Reached",
                                "You have reached the maximum of 100 saved parameters. Please delete one before saving a new one.")
            return

        name, ok = QInputDialog.getText(self.view, "Save Parameter", "Enter a name for this parameter set:")
        if ok and name:
            params = {
                "epochs": self.view.epochs_edit.text(),
                "batch_size": self.view.batch_size_edit.text(),
                "gen_lr": self.view.gen_lr_edit.text(),
                "disc_lr": self.view.disc_lr_edit.text(),
                "embedding_dim": self.view.embedding_dim_edit.text(),
                "generator_dim": self.view.generator_dim_edit.text(),
                "discriminator_dim": self.view.discriminator_dim_edit.text(),
                "pac": self.view.pac_edit.text(),
                "data_to_generate": self.view.data_to_generate_edit.text(),
                "verbose": self.view.verbose_combo.currentText(),
                "minmax": self.view.minmax_combo.currentText(),
            }
            try:
                self.model.add_parameter_set(name, params)
                QMessageBox.information(self.view, "Save", f"Parameters have been saved as '{name}'.")
            except Exception as e:
                QMessageBox.warning(self.view, "Error", str(e))

    def select_parameter(self):
        self.model.load_saved_parameters()
        history_dialog = QDialog(self.view)
        history_dialog.setWindowTitle("Select or Delete Parameter")
        history_dialog.setStyleSheet(self.view.styleSheet())  # Vous pouvez utiliser HISTORY_DIALOG_STYLE ici

        history_layout = QVBoxLayout()
        history_list_widget = QListWidget()
        history_list_widget.addItems(list(self.model.get_all_parameter_sets().keys()))
        history_layout.addWidget(history_list_widget)

        # Layout pour les boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ok_button = QPushButton("Ok")
        ok_button.setStyleSheet(
            "background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")
        ok_button.setFixedSize(100, 30)
        ok_button.clicked.connect(lambda: self.handle_selection(history_list_widget, history_dialog))
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(
            "background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")
        cancel_button.setFixedSize(100, 30)
        cancel_button.clicked.connect(history_dialog.reject)
        buttons_layout.addWidget(cancel_button)

        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet(
            "background-color: #4B66BE; color: white; border: none; border-radius: 10px; font-size: 13px;")
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
            params = self.model.get_parameter_set(selected_name)
            if params:
                self.load_selected_parameters(params)
        dialog.accept()

    def delete_parameter(self, history_list_widget):
        selected_item = history_list_widget.currentItem()
        if selected_item:
            selected_name = selected_item.text()
            self.model.delete_parameter_set(selected_name)
            history_list_widget.takeItem(history_list_widget.row(selected_item))
            QMessageBox.information(self.view, "Deleted", f"Parameter '{selected_name}' has been deleted.")

    def load_selected_parameters(self, params):
        self.view.epochs_edit.setText(params["epochs"])
        self.view.batch_size_edit.setText(params["batch_size"])
        self.view.gen_lr_edit.setText(params["gen_lr"])
        self.view.disc_lr_edit.setText(params["disc_lr"])
        self.view.embedding_dim_edit.setText(params["embedding_dim"])
        self.view.generator_dim_edit.setText(params["generator_dim"])
        self.view.discriminator_dim_edit.setText(params["discriminator_dim"])
        self.view.pac_edit.setText(params["pac"])
        self.view.data_to_generate_edit.setText(params["data_to_generate"])
        self.view.verbose_combo.setCurrentText(params["verbose"])
        self.view.minmax_combo.setCurrentText(params["minmax"])
