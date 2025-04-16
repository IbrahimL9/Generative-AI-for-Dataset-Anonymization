from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread
import pandas as pd
from models.display_model import extract_name, UpdateWorker


class DisplayView(QWidget):
    def __init__(self, download_button, main_app):
        super().__init__()
        self.download_button = download_button
        self.main_app = main_app
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("Display Generated Data")
        title.setFont(QFont("Montserrat", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        self.init_filter_section()
        self.init_table()

    def init_filter_section(self):
        self.filter_group = QGroupBox("\U0001F50D Filters")
        self.filter_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #7E88AB;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                margin-top: 10px;
                background: transparent;
            }
        """)
        filter_layout = QHBoxLayout()
        self.filter_group.setLayout(filter_layout)

        self.verb_combobox = QComboBox()
        self.verb_combobox.setFixedWidth(120)
        self.verb_combobox.setVisible(False)
        self.verb_checkbox = QCheckBox("Enable")
        self.verb_checkbox.stateChanged.connect(lambda c: self.verb_combobox.setVisible(c))
        verb_layout = QHBoxLayout()
        verb_layout.addWidget(QLabel("Verb:"))
        verb_layout.addWidget(self.verb_combobox)
        verb_layout.addWidget(self.verb_checkbox)

        self.actor_combobox = QComboBox()
        self.actor_combobox.setFixedWidth(120)
        self.actor_combobox.setVisible(False)
        self.actor_checkbox = QCheckBox("Enable")
        self.actor_checkbox.stateChanged.connect(lambda c: self.actor_combobox.setVisible(c))
        actor_layout = QHBoxLayout()
        actor_layout.addWidget(QLabel("Actor:"))
        actor_layout.addWidget(self.actor_combobox)
        actor_layout.addWidget(self.actor_checkbox)

        self.number_input = QSpinBox()
        self.number_input.setRange(0, 10000)
        self.number_input.setValue(0)
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Max Events:"))
        limit_layout.addWidget(self.number_input)

        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.setStyleSheet("""
            QPushButton {
                background-color: #6B748F;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A627D;
            }
        """)
        filter_layout.addLayout(verb_layout)
        filter_layout.addLayout(actor_layout)
        filter_layout.addLayout(limit_layout)
        filter_layout.addWidget(self.filter_button)

        self.layout.addWidget(self.filter_group)

    def init_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Duration (s)", "Actor", "Verb", "Object"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #F1F3F8;
                border: 2px solid #7E88AB;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                selection-background-color: #D0D7E5;
                alternate-background-color: #E5E9F2;
            }
            QHeaderView::section {
                background-color: #7E88AB;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #5F6889;
            }
            QTableWidget::item:selected {
                background-color: #D0D7E5;
                color: black;
            }
        """)
        self.layout.addWidget(self.table)

    def show_data(self, events, df):
        self.main_app.processed_dataframe = df
        self.populate_comboboxes(events)
        self.populate_table(events)

    def populate_comboboxes(self, events):
        self.verb_combobox.clear()
        self.actor_combobox.clear()
        verbs = sorted(set(extract_name(e.get("verb", {}).get("id", "")) for e in events))
        actors = sorted(set(extract_name(e.get("actor", {}).get("mbox", "")) for e in events))
        self.verb_combobox.addItems(verbs)
        self.actor_combobox.addItems(actors)

    def populate_table(self, events):
        self.table.setRowCount(len(events))
        for row, e in enumerate(events):
            try:
                ts = str(int(pd.to_datetime(e.get("timestamp", "")).timestamp()))
            except Exception:
                ts = "N/A"

            try:
                duration = str(int(float(e.get("Duration", 0))))
            except:
                duration = "0"

            items = [
                QTableWidgetItem(ts),
                QTableWidgetItem(duration),
                QTableWidgetItem(extract_name(e.get("actor", {}).get("mbox", ""))),
                QTableWidgetItem(extract_name(e.get("verb", {}).get("id", ""))),
                QTableWidgetItem(extract_name(e.get("object", {}).get("id", "")))
            ]

            for col, item in enumerate(items):
                self.table.setItem(row, col, item)
                if row % 2 == 0:
                    item.setBackground(QColor("#E5E9F2"))

    def clear_table(self):
        self.table.setRowCount(0)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def updateTable(self):
        data = self.download_button.json_data
        if not data:
            self.table.setRowCount(0)
            return

        # Affichage d'un indicateur de chargement
        self.showLoadingIndicator()

        # Démarrage de la mise à jour en arrière-plan via un worker
        self.thread = QThread()
        self.worker = UpdateWorker(data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_update_finished)
        self.worker.error.connect(self.on_update_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.start()

    def showLoadingIndicator(self):
        if not hasattr(self, "loading_label"):
            self.loading_label = QLabel("⏳ Loading data, please wait...")
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.insertWidget(1, self.loading_label)
        self.loading_label.show()

    def hideLoadingIndicator(self):
        if hasattr(self, "loading_label"):
            self.loading_label.hide()

    def on_update_finished(self, events, df):
        self.show_data(events, df)
        self.hideLoadingIndicator()

    def on_update_error(self, err_msg):
        self.show_error(err_msg)
        self.hideLoadingIndicator()
