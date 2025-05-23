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
        background-color: #4B66BE;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 20px;
        border: none;
    }
    QPushButton:hover {
        background-color: #3B5998;
    }
"""


COMBOBOX_STYLE = """
QComboBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
    font-family: "Montserrat", sans-serif;
    background-color: #f9f9f9;
    color: #333;
}

QComboBox:drop-down {
    border: 0px;
}

QComboBox QAbstractItemView {
    border: 1px solid #ccc;
    selection-background-color: #007BFF;
    selection-color: white;
    font-size: 14px;
    font-family: "Montserrat", sans-serif;
    background-color: #f9f9f9;
}
"""

LINEEDIT_STYLE = """
QLineEdit {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
    font-family: "Montserrat", sans-serif;
    background-color: #f9f9f9;
    color: #333;
}

QLineEdit:focus {
    border-color: #007BFF;
}
"""


# styles.py

# Simplified styles for messages
SUCCESS_MESSAGE_STYLE = """
    QLabel {
        color: green;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
"""

ERROR_MESSAGE_STYLE = """
    QLabel {
        color: red;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
"""

WARNING_MESSAGE_STYLE = """
    QLabel {
        color: black;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
"""

INFO_MESSAGE_STYLE = """
    QLabel {
        color: black;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
"""

##################


HISTORY_DIALOG_STYLE = """
    QDialog {
        background-color: #2E2E2E; /* Fond sombre */
        border-radius: 10px; /* Coins arrondis */
        padding: 20px;
    }
    QLabel {
        color: white;
        font-family: 'Montserrat', sans-serif;
        font-size: 14px;
    }
    QListWidget {
        background-color: #444444; /* Fond gris foncé */
        color: white;
        border-radius: 5px;
        padding: 10px;
        font-family: 'Montserrat', sans-serif;
    }
    QListWidget::item {
        padding: 10px;
        border-bottom: 1px solid #333333; /* Séparation des éléments */
    }
    QListWidget::item:hover {
        background-color: #5F5F5F; /* Survol des éléments */
    }
    QPushButton {
        background-color: #6C6C6C; /* Bouton gris */
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-family: 'Montserrat', sans-serif;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    QPushButton:hover {
        background-color: #8A8A8A; /* Effet de survol */
    }
    QPushButton:pressed {
        background-color: #555555; /* Effet au clic */
    }
    QDialogButtonBox {
        background-color: #2E2E2E;
    }
    QDialogButtonBox::button {
        background-color: #4A4A4A;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-family: 'Montserrat', sans-serif;
    }
    QDialogButtonBox::button:hover {
        background-color: #6C6C6C;
    }
"""
# Définir les styles pour les boutons
BUTTON_STYLE2 = """
QPushButton {
    background-color: #736EA7;
    color: black;
    border: none;
    padding: 20px;
    width: 200px;
    height: 150px;
    text-align: center;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.3s;
    font-size: 16px;
}
QPushButton:hover {
    background-color: #7377C4;
}
"""

BUTTON_STYLE3 = """
QPushButton {
    background-color: #4B66BE;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 15px 30px;
    font-size: 18px;
}
QPushButton:hover {
    background-color: #3B5998;
}
QPushButton:disabled {
    background-color: #cccccc; 
    color: #666666;
    border: 2px solid #cccccc;
}
"""

############

INFO_MESSAGE_BOX_STYLE = """
QMessageBox {
    background-color: #2c3e50;
    color: white;
    font-size: 14px;
    border-radius: 10px;
    padding: 20px;   /* Ajout de padding pour mieux espacer le texte */
    min-width: 400px;  /* Largeur minimale pour éviter les coupures de texte */
    min-height: 200px;  /* Hauteur minimale */
}

QMessageBox QLabel {
    background-color: #2c3e50;
    color: white;
    font-size: 14px;
    word-wrap: break-word;  /* Permet au texte de se couper proprement si trop long */
}

QMessageBox QPushButton {
    background-color: #2980b9;
    color: white;
    border-radius: 5px;
    padding: 5px 10px;
}

QMessageBox QPushButton:hover {
    background-color: #3498db;
}
"""
