# analysis_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QWidgetItem
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

class AnalysisView(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.web_view = None
        self.initUI()


    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.addSpacing(20)

        self.title = QLabel("COMPARATIVE ANALYSIS")
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.setWindowTitle("Analysis - Real vs. Generated")
        self.resize(1600, 2000)
        self.setLayout(self.layout)

    def show_loading_screen(self):
        if self.web_view is None:
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)
        loading_html = """
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; text-align: center;">
            <h2>Loading, please wait...</h2>
        </body>
        </html>
        """
        self.web_view.setHtml(loading_html)

    def load_report(self, html_file_path):
        if self.web_view is None:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self.web_view = QWebEngineView()
            self.scroll_layout.addWidget(self.web_view)
        from PyQt6.QtCore import QUrl
        self.web_view.setUrl(QUrl.fromLocalFile(html_file_path))
