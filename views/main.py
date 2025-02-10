import sys
from PyQt6.QtWidgets import QApplication
from views.Main_window import AnonymizationApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnonymizationApp()
    window.show()
    sys.exit(app.exec())
