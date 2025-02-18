from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame, QSizePolicy
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal


class Menu(QListWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        # Style de la barre latérale
        self.setStyleSheet("""
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
                    padding-top: 60px;
                }
                QListWidget::item {
                    padding: 8px;
                    text-align: left;
                    padding-top: 20px;
                }
                QListWidget::item:selected {
                    background: none;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                }

                /* Pour les items désactivés (comme vos spacers) :
                   - On rend leur fond transparent
                   - On masque leur texte en leur donnant une couleur transparente */
                QListWidget::item:disabled {
                    background: transparent;
                    color: transparent;
                }

                /* Pour être sûr qu'aucun effet de survol ne s'applique sur les items désactivés */
                QListWidget::item:hover:disabled {
                    background: transparent;
                    border: none;
                }
                """)
        # Définir ici la correspondance entre le sous-item et l'index de la page
        # Attention : les index doivent correspondre à l'ordre dans lequel vous ajoutez vos pages dans le QStackedWidget
        self.page_mapping = {
            "Open file": 0,  # HomePage
            "Display": 1,  # Par exemple, ModelParametersPage
            "Inspect": 2,  # Par exemple, GenerateDataPage
            "New": 3,
            "Build": 4,
            "Tools": 5,
            "Generate": 6,
            "Analysis": 7,
            "Save": 8,
            "About": 9
        }

        # Ici, vous créez vos sections et sous-items comme avant
        self.pages = [
            ("Source", "icons/source.png", ["Open file", "Display", "Inspect"]),
            ("Model", "icons/model.png", ["New", "Build", "Tools"]),
            ("Target", "icons/target.png", ["Generate", "Analysis", "Save"])
        ]

        self.section_items = []
        self.sub_items = {}

        for section, icon_path, sub_items in self.pages:
            section_item = QListWidgetItem(QIcon(icon_path), section)
            section_item.setFont(QFont("Montserrat", 11, QFont.Weight.Bold))
            section_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.section_items.append(section_item)
            self.addItem(section_item)
            self.sub_items[section] = []

            for sub_item in sub_items:
                sub_item_widget = QListWidgetItem("    " + sub_item)
                sub_item_widget.setFont(QFont("Montserrat", 10))
                sub_item_widget.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                sub_item_widget.setHidden(True)
                self.sub_items[section].append(sub_item_widget)
                self.addItem(sub_item_widget)

        # Espaces et About (inchangés)
        self.addSpacingItem()
        self.addSpacingItem()
        self.addSpacingItem()
        self.addSpacingItem()

        about_item = QListWidgetItem("About")
        about_item.setFont(QFont("Montserrat", 12, QFont.Weight.Bold))
        about_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        about_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        about_item.setForeground(Qt.GlobalColor.black)
        self.addItem(about_item)

        # Par défaut, afficher le sous-menu de "Source" et sélectionner "Open file"
        self.show_initial_submenu("Source", "Open file")
        self.currentRowChanged.connect(self.on_page_changed)

        # Émettre le signal pour afficher la page d'accueil dès le lancement
        self.page_changed.emit(self.page_mapping["Open file"])

    def addSpacingItem(self):
        spacing_item = QListWidgetItem("")
        spacing_item.setFlags(Qt.ItemFlag.NoItemFlags)
        spacing_item.setData(Qt.ItemDataRole.UserRole, "spacer")
        self.addItem(spacing_item)

    def on_page_changed(self, index):
        item = self.item(index)
        # Si on clique sur une section, on affiche/masque ses sous-items
        if item in self.section_items:
            section_name = item.text()
            # Masquer les sous-menus des autres sections
            for sec, sub_items in self.sub_items.items():
                if sec != section_name:
                    for sub_item in sub_items:
                        sub_item.setHidden(True)
            # Afficher/masquer les sous-menus de la section cliquée
            for sub_item in self.sub_items[section_name]:
                sub_item.setHidden(not sub_item.isHidden())
        else:
            # Si c'est un sous-item, on récupère son texte (sans espaces) et on émet le signal avec l'index mappé
            text = item.text().strip()
            if text in self.page_mapping:
                self.page_changed.emit(self.page_mapping[text])

    def show_initial_submenu(self, section_name, sub_item_name):
        """
        Affiche les sous-items de la section spécifiée et sélectionne celui qui correspond à sub_item_name.
        """
        # Masquer les sous-menus des autres sections
        for sec, sub_items in self.sub_items.items():
            if sec != section_name:
                for sub_item in sub_items:
                    sub_item.setHidden(True)
        # Afficher les sous-items de la section spécifiée
        for sub_item in self.sub_items.get(section_name, []):
            sub_item.setHidden(False)
            # Si le sous-item correspond à celui souhaité, le sélectionner
            if sub_item.text().strip() == sub_item_name:
                self.setCurrentItem(sub_item)
                break
