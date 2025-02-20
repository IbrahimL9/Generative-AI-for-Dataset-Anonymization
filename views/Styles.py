SIDEBAR_STYLE = """
QListWidget {
    border-top-right-radius: 15px;
    border-bottom-right-radius: 15px;
    border: none;
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(189,158,215,255), 
                                stop:1 rgba(64,89,168,255));
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding-left: 10px;
}

QListWidget::item {
    padding: 8px;
    text-align: left;
}

QListWidget::item:selected {
    background: rgba(255, 255, 255, 50);
    border-radius: 5px;
}
"""



BUTTON_STYLE = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 20px;
        border: none;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:pressed {
        background-color: #388E3C;
    }
"""


