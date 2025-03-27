from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class Fidelity(QWidget):
    def __init__(self, main_app):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Fidelity"))
        self.setLayout(layout)
