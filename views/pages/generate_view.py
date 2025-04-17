# generate_view.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QProgressBar, \
    QHBoxLayout, QFileDialog, QDialog, QVBoxLayout as QVLayout
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize,pyqtSignal
from views.Styles import BUTTON_STYLE2, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE, WARNING_MESSAGE_STYLE, \
    INFO_MESSAGE_STYLE


class GenerateView(QWidget):
    data_generated_signal = pyqtSignal(object)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.initUI()
        self.generated_data = None


    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addSpacing(20)

        self.title = QLabel("Generate")
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title)
        main_layout.addSpacing(100)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.records_input_label = QLabel("Number of Action to Generate:")
        self.records_input_label.setFont(QFont("Montserrat", 14))
        self.records_input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.records_input = QLineEdit("1000")
        self.records_input.setFixedWidth(200)
        self.records_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.records_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
                color: #333;
            }
        """)
        form_layout.addRow(self.records_input_label, self.records_input)

        self.users_input_label = QLabel("Number of Unique Actors (0 = default):")
        self.users_input_label.setFont(QFont("Montserrat", 14))
        self.users_input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.users_input = QLineEdit("0")
        self.users_input.setFixedWidth(200)
        self.users_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.users_input.setStyleSheet(self.records_input.styleSheet())
        form_layout.addRow(self.users_input_label, self.users_input)

        form_container = QHBoxLayout()
        form_container.addStretch(1)
        form_container.addLayout(form_layout)
        form_container.addStretch(1)
        main_layout.addLayout(form_container)
        main_layout.addSpacing(40)

        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(BUTTON_STYLE2)
        self.generate_button.setFixedSize(200, 150)
        self.generate_button.setIcon(QIcon("images/generate.png"))
        self.generate_button.setIconSize(QSize(45, 45))
        main_layout.addWidget(self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(200)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)
        self.setWindowTitle("Generative AI for Dataset Anonymization")

    def show_progress(self, visible):
        self.progress_bar.setVisible(visible)

    def show_message(self, message, message_type="info"):
        dlg = QDialog(self)
        dlg.setWindowTitle("Information")
        layout = QVBoxLayout(dlg)
        lbl = QLabel(message)
        if message_type == "success":
            lbl.setStyleSheet(SUCCESS_MESSAGE_STYLE)
        elif message_type == "error":
            lbl.setStyleSheet(ERROR_MESSAGE_STYLE)
        elif message_type == "warning":
            lbl.setStyleSheet(WARNING_MESSAGE_STYLE)
        else:
            lbl.setStyleSheet(INFO_MESSAGE_STYLE)
        layout.addWidget(lbl)
        dlg.exec()

    def on_model_loaded(self, model):
        self.model = model
        self.model_loaded = True

    def on_file_loaded(self, json_data):
        self.json_data = json_data
        self.check_enable_generate_button()