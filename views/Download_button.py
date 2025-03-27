import json
import os
from PyQt6.QtWidgets import QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from .Styles import BUTTON_STYLE


class DownloadButton(QWidget):
    file_loaded = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.default_text = text
        self.json_data = None

        # Création du layout vertical
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Création du bouton
        self.button = QPushButton(text, self)
        self.button.setAcceptDrops(True)
        self.button.setStyleSheet(BUTTON_STYLE)
        self.layout.addWidget(self.button)

        # Création du label pour afficher les messages sous le bouton
        self.message_label = QLabel("", self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.hide()  # Masqué par défaut
        self.layout.addWidget(self.message_label)

        # La taille par défaut sera mise à jour dans showEvent
        self.default_size = None

        # Connexion du clic
        self.button.clicked.connect(self.load_file)

        # Installer un event filter sur le bouton pour intercepter les événements de drag & drop
        self.button.installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        # Mettez à jour la taille par défaut une fois que le widget est affiché
        self.default_size = self.button.size()

    def eventFilter(self, obj, event):
        # Intercepter les événements sur le bouton
        if obj == self.button:
            if event.type() == event.Type.DragEnter:
                self.handleDragEnter(event)
                return True
            elif event.type() == event.Type.DragLeave:
                self.handleDragLeave(event)
                return True
            elif event.type() == event.Type.Drop:
                self.handleDrop(event)
                return True
        return super().eventFilter(obj, event)

    def handleDragEnter(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            # Vérifier si c'est un fichier JSON ou un dossier
            if file_path.lower().endswith('.json') or os.path.isdir(file_path):
                # Modifier le texte du bouton en fonction du type
                if os.path.isdir(file_path):
                    self.button.setText("Drop the Folder")
                else:
                    self.button.setText("Drop the File")
                if self.default_size:
                    new_width = int(self.default_size.width() * 1.5)
                    new_height = int(self.default_size.height() * 1.5)
                    self.button.setFixedSize(new_width, new_height)
                event.acceptProposedAction()
            else:
                event.ignore()

    def handleDragLeave(self, event):
        # Rétablir la taille et le texte par défaut
        if self.default_size:
            self.button.setFixedSize(self.default_size)
        self.button.setText(self.default_text)
        event.accept()

    def handleDrop(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            # Rétablir la taille par défaut du bouton
            if self.default_size:
                self.button.setFixedSize(self.default_size)
            # Traitement d'un fichier JSON individuel
            if file_path.lower().endswith('.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.json_data = json.load(f)
                    self.button.setText("File loaded !")
                    self.showMessage(
                        f"{os.path.basename(file_path)} has been loaded successfully!",
                        success=True
                    )
                    self.file_loaded.emit()
                    event.acceptProposedAction()
                except Exception as e:
                    self.button.setText("Load error")
                    self.showMessage(
                        f"{os.path.basename(file_path)} failed to load: {e}",
                        success=False
                    )
            # Traitement d'un dossier contenant des fichiers JSON
            elif os.path.isdir(file_path):
                concatenated_data = []
                loaded_files = 0
                errors = []
                for entry in os.listdir(file_path):
                    full_path = os.path.join(file_path, entry)
                    if full_path.lower().endswith('.json') and os.path.isfile(full_path):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            # Si les données sont une liste, les étendre; sinon, les ajouter
                            if isinstance(data, list):
                                concatenated_data.extend(data)
                            else:
                                concatenated_data.append(data)
                            loaded_files += 1
                        except Exception as e:
                            errors.append(f"{entry}: {e}")
                if loaded_files > 0:
                    self.json_data = concatenated_data
                    self.button.setText("Folder loaded!")
                    message = f"{loaded_files} JSON file{'s' if loaded_files > 1 else ''} loaded successfully!"
                    if errors:
                        message += " Some files failed: " + ", ".join(errors)
                        self.showMessage(message, success=False)
                    else:
                        self.showMessage(message, success=True)
                    self.file_loaded.emit()
                    event.acceptProposedAction()
                else:
                    self.button.setText("Load error")
                    self.showMessage("No valid JSON files found in the folder.", success=False)
                    event.ignore()
            else:
                self.button.setText("Invalid file")
                self.showMessage("Only JSON files or folders containing JSON files are accepted", success=False)
                event.ignore()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.json_data = json.load(f)
                self.button.setText("File loaded !")
                self.showMessage(
                    f"{os.path.basename(file_path)} has been loaded successfully",
                    success=True
                )
                self.file_loaded.emit()
            except Exception as e:
                self.button.setText("Load error")
                self.showMessage(
                    f"{os.path.basename(file_path)} failed to load: {e}",
                    success=False
                )
        else:
            self.button.setText(self.default_text)

    def showMessage(self, message, success=True):
        self.message_label.setText(message)
        if success:
            self.message_label.setStyleSheet(
                "background-color: green; color: white; padding: 5px; border-radius: 3px;"
            )
        else:
            self.message_label.setStyleSheet(
                "background-color: red; color: white; padding: 5px; border-radius: 3px;"
            )
        self.message_label.show()
        QTimer.singleShot(5000, self.message_label.hide)
