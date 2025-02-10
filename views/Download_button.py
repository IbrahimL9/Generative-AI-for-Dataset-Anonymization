import json
from PyQt6.QtWidgets import QPushButton, QFileDialog, QMessageBox
from .Styles import BUTTON_STYLE

class DownloadButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.default_text = text
        self.setAcceptDrops(True)
        self.setStyleSheet(BUTTON_STYLE)
        self.clicked.connect(self.download_file)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setText("Glissez le fichier")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.json'):
                self.setText("Fichier JSON déposé")
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, "Erreur", "Seuls les fichiers JSON sont acceptés.")
                self.setText("Fichier non accepté")
                event.ignore()
        else:
            event.ignore()

    def download_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Télécharger le fichier JSON", "", "JSON Files (*.json)")
        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"
            data = {"message": "Ceci est un fichier JSON téléchargé."}
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Succès", f"Fichier sauvegardé : {file_path}")
                self.setText("Fichier téléchargé")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {e}")
        else:
            self.setText(self.default_text)
