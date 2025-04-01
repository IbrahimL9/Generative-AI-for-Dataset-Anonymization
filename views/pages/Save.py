import json
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QDialog,
    QMessageBox, QHBoxLayout, QScrollArea, QFrame
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
from views.Styles import SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE, BUTTON_STYLE2

class Save(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.data_generated = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Aligne tout vers le haut
        layout.addSpacing(20)

        # Titre
        label = QLabel("Save")
        label.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        layout.addSpacing(150)

        # Layout horizontal pour les boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(40)

        self.save_button = QPushButton("Save Data")
        self.save_button.setStyleSheet(BUTTON_STYLE2)
        self.save_button.setFixedSize(200, 150)
        self.save_button.setIcon(QIcon("images/save.png"))
        self.save_button.setIconSize(QSize(45, 45))
        self.save_button.clicked.connect(self.save_data)
        buttons_layout.addWidget(self.save_button)

        self.display_button = QPushButton("Display Data")
        self.display_button.setStyleSheet(BUTTON_STYLE2)
        self.display_button.setFixedSize(200, 150)
        self.display_button.setIcon(QIcon("images/view.png"))
        self.display_button.setIconSize(QSize(45, 45))
        self.display_button.clicked.connect(self.display_data)
        buttons_layout.addWidget(self.display_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # Désactivés par défaut (activés via on_data_generated)
        self.display_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def on_data_generated(self):
        """Méthode pour activer les boutons lorsque les données sont générées."""
        self.data_generated = True
        self.save_button.setEnabled(True)
        self.display_button.setEnabled(True)

    def display_data(self):
        """Affiche les données générées dans une QDialog avec barre de défilement."""
        if not self.data_generated:
            QMessageBox.warning(self, "Error", "No data available to display.")
            return

        # Récupère la structure depuis la page "generate"
        generated_data = self.main_app.pages["generate"].generated_data
        if generated_data is None:
            QMessageBox.warning(self, "Error", "No data found.")
            return

        # Conversion si DataFrame
        data_to_display = self._prepare_data_for_display_or_save(generated_data)

        # On tente de faire un dumps JSON (avec indentation)
        try:
            data_str = json.dumps(data_to_display, indent=4, ensure_ascii=False)
        except Exception as e:
            data_str = f"Erreur lors de la conversion JSON: {e}"

        # (Optionnel) On peut tronquer si c’est trop long pour éviter un crash d’affichage
        MAX_LEN = 200000  # 200k caractères par ex.
        if len(data_str) > MAX_LEN:
            data_str = data_str[:MAX_LEN] + "\n[... TRONQUÉ ...]"

        # Création de la QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated Data")
        dialog.setMinimumSize(600, 400)
        dialog_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QFrame()
        content_layout = QVBoxLayout(content_widget)

        # Affichage du JSON formaté dans un QLabel
        data_label = QLabel(data_str)
        data_label.setFont(QFont("Courier", 10))
        data_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        content_layout.addWidget(data_label)
        scroll_area.setWidget(content_widget)
        dialog_layout.addWidget(scroll_area)

        dialog.exec()

    def save_data(self):
        """Sauvegarde les données générées dans un fichier JSON."""
        if not self.data_generated:
            QMessageBox.warning(self, "Error", "No data to save.")
            return

        file_dialog = QFileDialog()
        file_name, _ = file_dialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")

        if not file_name:
            return  # Annulation par l'utilisateur

        # Récupère la structure depuis la page "generate"
        generated_data = self.main_app.pages["generate"].generated_data
        if generated_data is None:
            QMessageBox.warning(self, "Error", "No data found.")
            return

        # Conversion si DataFrame
        data_to_save = self._prepare_data_for_display_or_save(generated_data)

        # Écriture au format JSON
        try:
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(data_to_save, file, ensure_ascii=False, indent=4)
            self.show_message("Data successfully saved!", message_type="success")
        except Exception as e:
            self.show_message(f"Error saving data: {e}", message_type="error")

    def _prepare_data_for_display_or_save(self, generated_data):
        """
        Convertit la structure DataFrame (Sessions) ou liste (Actions)
        en un objet Python compatible JSON.
        """
        if isinstance(generated_data, pd.DataFrame):
            # Mode "Sessions": la DataFrame a probablement une colonne 'actions'
            if "actions" in generated_data.columns:
                # Chaque ligne => liste de dicts
                return generated_data["actions"].tolist()
            else:
                # Sinon, on convertit tout le DF
                return generated_data.to_dict(orient="records")
        elif isinstance(generated_data, list):
            # Mode "Actions": on a déjà une liste de dicts
            return generated_data
        else:
            # Structure inconnue, on renvoie quand même quelque chose
            return str(generated_data)

    def show_message(self, message, message_type="info"):
        """Affiche un message dans une QDialog avec un style spécifique."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)

        # Appliquer le style en fonction du type de message
        if message_type == "success":
            message_label.setStyleSheet(SUCCESS_MESSAGE_STYLE)
        elif message_type == "error":
            message_label.setStyleSheet(ERROR_MESSAGE_STYLE)
        elif message_type == "warning":
            message_label.setStyleSheet(WARNING_MESSAGE_STYLE)
        else:
            message_label.setStyleSheet(INFO_MESSAGE_STYLE)

        dialog_layout.addWidget(message_label)
        dialog.exec()
