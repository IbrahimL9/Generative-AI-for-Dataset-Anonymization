# Menu.py
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame, QSizePolicy
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal


class Menu(QListWidget):
    page_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
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
                    padding-top: 100px;
                }
                QListWidget::item {
                    padding: 10px;
                    text-align: left;
                    padding-top: 15px;
                    font: 50px;
                }
                QListWidget::item:selected {
                    background: none;
                    border: none;
                }
                QListWidget::item:focus {
                    outline: none;
                }
                QListWidget::item:disabled {
                    background: transparent;
                    color: transparent;
                }
                QListWidget::item:hover:disabled {
                    background: transparent;
                    border: none;
                }
                """)
        # Mise à jour du mapping avec les nouvelles pages
        self.page_mapping = {
            "Open file": "open",
            "Display": "display",
            "Inspect": "inspect",
            "New": "new",
            "Build": "build",
            "Tools": "tools",
            "Generate": "generate",
            "Analysis": "analysis",
            "Confidentiality": "confidentiality",
            "Fidelity": "fidelity",
            "Save": "save",
            "About": "about"
        }

        self.pages = [
            ("Source", "icons/source.png", ["Open file", "Display", "Inspect"]),
            ("Model", "icons/model.png", ["New", "Build", "Tools"]),
            ("Target", "icons/target.png", ["Generate", "Analysis", "Save"])
        ]
        self.section_items = []
        self.sub_items = {}

        # Liste qui contiendra les sous-sous-menus pour "Analysis"
        self.analysis_submenu = []

        # Ajout des sections et sous-éléments
        for section, icon_path, sub_items in self.pages:
            section_item = QListWidgetItem(QIcon(icon_path), section)
            section_item.setFont(QFont("Montserrat", 13, QFont.Weight.Bold))
            section_item.setFlags(section_item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.section_items.append(section_item)
            self.addItem(section_item)
            self.sub_items[section] = []

            for sub_item in sub_items:
                sub_item_widget = QListWidgetItem(f"    • {sub_item}")
                sub_item_widget.setFont(QFont("Montserrat", 10))

                if sub_item == "Build":
                    # L'élément s'affiche mais ne peut pas être sélectionné et ne déclenche pas d'action
                    sub_item_widget.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    sub_item_widget.setFlags(sub_item_widget.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    # Désactiver les signaux pour cet élément
                    sub_item_widget.setFlags(sub_item_widget.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                else:
                    sub_item_widget.setFlags(
                        sub_item_widget.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                    )

                sub_item_widget.setHidden(False)
                self.sub_items[section].append(sub_item_widget)
                self.addItem(sub_item_widget)


        self.addSpacingItem()
        about_item = QListWidgetItem("About")
        about_item.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
        about_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        about_item.setFlags(about_item.flags() | Qt.ItemFlag.ItemIsEnabled)
        about_item.setForeground(Qt.GlobalColor.black)
        self.addItem(about_item)

        self.show_initial_submenu("Source", "Open file")
        self.currentRowChanged.connect(self.on_page_changed)
        self.page_changed.emit(self.page_mapping["Open file"])

    def addSpacingItem(self, count=4):
        for _ in range(count):
            spacing_item = QListWidgetItem("")
            spacing_item.setFlags(Qt.ItemFlag.NoItemFlags)
            spacing_item.setData(Qt.ItemDataRole.UserRole, "spacer")
            self.addItem(spacing_item)

    def on_page_changed(self, index):
        item = self.item(index)
        # Récupérer le texte sans indentation ni puce
        item_text = item.text().strip().replace("• ", "")

        # Si l'élément est "Build", ne rien faire
        if item_text == "Build":
            return

        # Si un élément de sous-menu "Analysis" est déjà présent et que l'utilisateur sélectionne un autre item qui n'est pas ces sous-menus, on les retire.
        if item_text not in ["Analysis", "Confidentiality", "Fidelity"]:
            if self.analysis_submenu:
                for sub in self.analysis_submenu:
                    row = self.row(sub)
                    self.takeItem(row)
                self.analysis_submenu = []

        # Si l'utilisateur sélectionne "Analysis", on insère les sous-sous-menus si non déjà présents.
        if item_text == "Analysis":
            if not self.analysis_submenu:
                current_index = self.currentRow()
                candidate_item = QListWidgetItem("              • Confidentiality")
                candidate_item.setFont(QFont("Montserrat", 9))
                candidate_item.setFlags(
                    candidate_item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                fidelity_item = QListWidgetItem("              • Fidelity")
                fidelity_item.setFont(QFont("Montserrat", 9))
                fidelity_item.setFlags(fidelity_item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                # Insérer ces items juste après "Analysis"
                self.insertItem(current_index + 1, candidate_item)
                self.insertItem(current_index + 2, fidelity_item)
                self.analysis_submenu.extend([candidate_item, fidelity_item])

        # Si l'élément sélectionné fait partie du mapping, on émet le signal correspondant.
        if item_text in self.page_mapping:
            self.page_changed.emit(self.page_mapping[item_text])

        # Gérer l'affichage des sous-menus de section (premier niveau)
        if item in self.section_items:
            section_name = item.text()
            for sec, sub_items in self.sub_items.items():
                for sub_item in sub_items:
                    sub_item.setHidden(sec != section_name)

    def show_initial_submenu(self, section_name, sub_item_name):
        for sec, sub_items in self.sub_items.items():
            for sub_item in sub_items:
                sub_item.setHidden(sec != section_name)
        for sub_item in self.sub_items.get(section_name, []):
            if sub_item.text().strip().replace("• ", "") == sub_item_name:
                self.setCurrentItem(sub_item)
                break
