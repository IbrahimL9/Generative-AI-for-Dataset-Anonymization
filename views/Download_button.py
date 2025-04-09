import os
import json
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QObject, pyqtSlot
)
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout
)

from .Styles import BUTTON_STYLE


class JSONLoaderWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    @pyqtSlot()
    def run(self):
        try:
            if os.path.isfile(self.file_path) and self.file_path.lower().endswith('.json'):
                data = self._load_single_json(self.file_path)
                self.finished.emit(data)

            elif os.path.isdir(self.file_path):
                all_data = []
                loaded_files = 0
                errors = []

                for entry in os.listdir(self.file_path):
                    full_path = os.path.join(self.file_path, entry)
                    if full_path.lower().endswith('.json') and os.path.isfile(full_path):
                        try:
                            sub_data = self._load_single_json(full_path)
                            all_data.extend(sub_data)
                            loaded_files += 1
                        except Exception as e:
                            errors.append(f"{entry}: {e}")

                if loaded_files == 0:
                    raise ValueError("No valid JSON files found in the folder.")
                if errors:
                    # On prévient qu'il y a des erreurs, mais on renvoie quand même le data
                    err_msg = "Some files failed: " + ", ".join(errors)
                    self.error.emit(err_msg)

                self.finished.emit(all_data)
            else:
                raise ValueError("Invalid file or folder (must be .json or folder containing .json).")
        except Exception as e:
            self.error.emit(str(e))

    def _load_single_json(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # On normalize en liste
        if isinstance(data, list):
            return data
        else:
            return [data]


class DownloadButton(QWidget):
    file_loaded = pyqtSignal()  # Émis quand les données sont chargées (facultatif)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.default_text = text
        self.json_data = None

        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Bouton
        self.button = QPushButton(text, self)
        self.button.setAcceptDrops(True)
        self.button.setStyleSheet(BUTTON_STYLE)
        self.layout.addWidget(self.button)

        # Label de message sous le bouton
        self.message_label = QLabel("", self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.hide()  # Masqué par défaut
        self.layout.addWidget(self.message_label)

        self.default_size = None

        # Clic sur le bouton => Dialogue pour charger un JSON
        self.button.clicked.connect(self.load_file)

        # Permet d'intercepter les drag & drop
        self.button.installEventFilter(self)

        # Thread et worker (on en créera un au besoin)
        self.thread = None
        self.loader = None

    def reset(self):
        """Réinitialiser l'état du bouton de téléchargement."""
        self.json_data = None
        self.button.setText(self.default_text)
        self.message_label.hide()

    def showEvent(self, event):
        super().showEvent(event)
        # Mémoriser la taille par défaut une fois que le widget est affiché
        self.default_size = self.button.size()

    def eventFilter(self, obj, event):
        # Intercepter les événements de drag & drop
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
            # On n'accepte que les .json ou les dossiers
            if file_path.lower().endswith('.json') or os.path.isdir(file_path):
                # Modifier le texte du bouton en fonction du type
                if os.path.isdir(file_path):
                    self.button.setText("Drop the Folder")
                else:
                    self.button.setText("Drop the File")
                # (Facultatif) Agrandir un peu le bouton pour le feedback
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

            # On lance le chargement asynchrone
            self.load_json_async(file_path)
            event.acceptProposedAction()

    def load_file(self):
        """Ouvre un QFileDialog pour sélectionner un fichier JSON."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_path:
            self.load_json_async(file_path)
        else:
            self.button.setText(self.default_text)

    def load_json_async(self, file_path):
        """Crée un worker + QThread pour charger le JSON sans bloquer l'UI."""
        self.button.setText("Loading...")
        self.showMessage("Loading file in background...", success=True)

        # On vide l'ancienne data
        self.json_data = None

        # Crée le thread et le worker
        self.thread = QThread()
        self.loader = JSONLoaderWorker(file_path)
        self.loader.moveToThread(self.thread)

        # Connecte les signaux
        self.thread.started.connect(self.loader.run)
        self.loader.finished.connect(self.on_json_loaded)
        self.loader.error.connect(self.on_json_error)

        # A la fin, on arrête le thread
        self.loader.finished.connect(self.thread.quit)
        self.loader.error.connect(self.thread.quit)

        # Lancement
        self.thread.start()

    def on_json_loaded(self, data):
        """Slot appelé quand le worker a fini de charger."""
        self.json_data = data
        # Mise à jour du bouton et du label
        self.button.setText("File loaded !")
        self.showMessage(f"Loaded {len(data)} items successfully!", success=True)
        # On émet le signal si d'autres composants veulent réagir
        self.file_loaded.emit()

    def on_json_error(self, err_msg):
        """Slot appelé si le worker rencontre un souci."""
        self.button.setText("Load error")
        self.showMessage(err_msg, success=False)

    def showMessage(self, message, success=True):
        """Affiche un message sous le bouton, puis le masque après 5 s."""
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
