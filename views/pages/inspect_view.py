from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import os


class InspectView(QWidget):
    def __init__(self):
        super().__init__()
        self.web_view = None
        self.scroll_layout = None
        self.report_loaded = False  # 🔹 Empêche les rechargements multiples
        self.report_path = None     # 🔹 Sauvegarde le chemin du rapport
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(20)

        title = QLabel("STATISTICS")
        title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

    def clear_report(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.web_view = None
        self.report_loaded = False
        self.report_path = None

    def show_loading_message(self):
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)

        html = """
        <html><body style="font-family: Arial; text-align: center; padding: 20px;">
        <h2>Loading statistics, please wait...</h2></body></html>
        """
        self.web_view.setHtml(html)
        self.report_loaded = False

    def display_report(self, html_file_path: str):
        if self.report_loaded and self.report_path == html_file_path:
            return

        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)

        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(html_file_path)))
        self.report_loaded = True
        self.report_path = html_file_path
