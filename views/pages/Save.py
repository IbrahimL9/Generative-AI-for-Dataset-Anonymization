from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import json
from views.Styles import BUTTON_STYLE

class Save(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.data_generated = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addStretch(5)

        label = QLabel("Save")
        label.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.setFixedWidth(200)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(2)
        self.setLayout(layout)
        self.save_button.setEnabled(False)  # Désactivé par défaut

    def on_data_generated(self):
        self.data_generated = True
        self.save_button.setEnabled(True)

    def save_data(self):
        if not self.data_generated:
            QMessageBox.warning(self, "Erreur", "Aucune donnée à sauvegarder.")
            return

        file_dialog = QFileDialog()
        file_name, _ = file_dialog.getSaveFileName(self, "Enregistrer les données", "", "JSON Files (*.json)")

        if file_name:
            generated_data = self.main_app.pages["generate"].generated_data

            if generated_data:
                with open(file_name, "w", encoding="utf-8") as file:
                    json.dump(generated_data, file, ensure_ascii=False, indent=4)  # ✅ Ajoute des retours à la ligne
                self.show_message("Données sauvegardées avec succès !")

    def show_message(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)
        dialog_layout.addWidget(message_label)
        dialog.exec()
