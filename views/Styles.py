SIDEBAR_STYLE = """
    QListWidget {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(189,158,215,255), stop:1 rgba(64,89,168,255));
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    color: white;
    font-size: 16px;
    padding-left: 15px;
    padding-top: 0px;  /* Modifier ici */
    padding-right: 0px; /* Modifier ici */
    padding-bottom: 0px; /* Modifier ici */
    outline: 0;
}

    QListWidget::item {
        margin-top: 10px;
        margin-bottom: 10px;
        padding-top: 7px;
        padding-bottom: 7px;
        outline: 0;
    }
    QListWidget::item:selected {
        background: white;
        color: black;
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #677DB7;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 20px;
        border: none;
    }
    QPushButton:hover {
        background-color: #5A6FA5;
    }
    QPushButton:focus {
        outline: none;
        border: none;
    }
"""

