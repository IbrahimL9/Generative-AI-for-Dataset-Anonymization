from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit,
    QComboBox, QDialog, QFileDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from views.Styles import (
    BUTTON_STYLE2, SUCCESS_MESSAGE_STYLE, ERROR_MESSAGE_STYLE,
    WARNING_MESSAGE_STYLE, INFO_MESSAGE_STYLE
)


class BuildView(QWidget):
    train_clicked = pyqtSignal()
    save_clicked = pyqtSignal(str)

    def __init__(self, main_app, download_button, tools):
        super().__init__()
        self.main_app = main_app
        self.download_button = download_button
        self.tools = tools
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addSpacing(30)

        self.title = QLabel("Build Model", self)
        self.title.setFont(QFont("Montserrat", 21, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(32)

        # -- Mode de données
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label = QLabel("Data Mode :")
        self.mode_label.setFont(QFont("Arial", 12))
        self.data_mode_combo = QComboBox()
        self.data_mode_combo.addItems(["Actions", "Sessions"])
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.data_mode_combo)
        layout.addLayout(mode_layout)
        layout.addSpacing(20)

        # -- Boutons
        button_layout = QHBoxLayout()

        self.train_model_button = QPushButton("Train Model", self)
        self.train_model_button.setStyleSheet(BUTTON_STYLE2)
        self.train_model_button.setFixedSize(200, 150)
        self.train_model_button.setIcon(QIcon("images/train.png"))
        self.train_model_button.setIconSize(QSize(45, 45))
        self.train_model_button.clicked.connect(lambda: self.train_clicked.emit())
        button_layout.addWidget(self.train_model_button)

        self.save_model_button = QPushButton("Save Model", self)
        self.save_model_button.setStyleSheet(BUTTON_STYLE2)
        self.save_model_button.setFixedSize(200, 150)
        self.save_model_button.setIcon(QIcon("images/save.png"))
        self.save_model_button.setIconSize(QSize(40, 40))
        self.save_model_button.setEnabled(False)
        self.save_model_button.clicked.connect(self.emit_save_model)
        button_layout.addWidget(self.save_model_button)

        layout.addLayout(button_layout)
        layout.addSpacing(100)

        # -- Zone de texte pour messages
        self.output_edit = QPlainTextEdit(self)
        self.output_edit.setReadOnly(True)
        self.output_edit.setFrameStyle(0)
        font = QFont("Montserrat", 10, QFont.Weight.Medium)
        self.output_edit.setFont(font)
        self.output_edit.setStyleSheet("color: red;")
        layout.addWidget(self.output_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(22)

        self.setLayout(layout)

    def emit_save_model(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Model", "", "Pickle Files (*.pkl)")
        if file_path:
            self.save_clicked.emit(file_path)

    def update_output(self, text):
        self.output_edit.setPlainText(text)
        self.output_edit.verticalScrollBar().setValue(
            self.output_edit.verticalScrollBar().maximum()
        )

    def show_message(self, message, message_type="info"):
        dialog = QDialog(self)
        dialog.setWindowTitle("Information")
        dialog_layout = QVBoxLayout(dialog)
        message_label = QLabel(message)

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

    def enable_save(self):
        self.save_model_button.setEnabled(True)

    def on_model_loaded(self, model):
        self.model = model
        self.enable_save()
        self.update_output("✅ Model loaded successfully!")
