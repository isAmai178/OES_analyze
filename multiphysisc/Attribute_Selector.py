import logging

logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QSpinBox, QLabel
from typing import List, Dict

class FileAttributeSelector(QGroupBox):
    """Custom widget for file attribute selection."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.attributes: List[str] = []
        self.selected_attributes: Dict[str, int] = {}  # 改為字典，儲存屬性和對應的區段數
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # 屬性選擇區
        attr_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.currentTextChanged.connect(self._on_selection_changed)
        
        # 區段數設定 - 修改最小值為2
        self.section_spin = QSpinBox()
        self.section_spin.setRange(2, 10)  # 最少2個區段
        self.section_spin.setValue(2)
        
        attr_layout.addWidget(QLabel("可用屬性："))
        attr_layout.addWidget(self.combo_box)
        attr_layout.addWidget(QLabel("區段數："))
        attr_layout.addWidget(self.section_spin)

        # 添加/移除按鈕
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加")
        self.remove_btn = QPushButton("移除")
        self.add_btn.clicked.connect(self._add_attribute)
        self.remove_btn.clicked.connect(self._remove_attribute)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)

        # 已選擇的屬性列表
        self.selected_list = QTableWidget()
        self.selected_list.setColumnCount(2)
        self.selected_list.setHorizontalHeaderLabels(["屬性名稱", "區段數"])

        layout.addLayout(attr_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("已選擇的屬性："))
        layout.addWidget(self.selected_list)
        self.setLayout(layout)

    def set_available_attributes(self, attributes: List[str]) -> None:
        """Set available attributes in the combo box."""
        self.attributes = attributes
        self.combo_box.clear()
        self.combo_box.addItems(attributes)

    def _add_attribute(self) -> None:
        """Add selected attribute to the list."""
        current_attr = self.combo_box.currentText()
        if current_attr and current_attr not in self.selected_attributes:
            sections = self.section_spin.value()
            self.selected_attributes[current_attr] = sections
            self._update_selected_list()

    def _remove_attribute(self) -> None:
        """Remove selected attribute from the list."""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            attr = self.selected_list.item(current_row, 0).text()
            del self.selected_attributes[attr]
            self._update_selected_list()

    def _update_selected_list(self) -> None:
        """Update the selected attributes list display."""
        self.selected_list.setRowCount(len(self.selected_attributes))
        for i, (attr, sections) in enumerate(self.selected_attributes.items()):
            self.selected_list.setItem(i, 0, QTableWidgetItem(attr))
            self.selected_list.setItem(i, 1, QTableWidgetItem(str(sections)))

    def _on_selection_changed(self, text: str) -> None:
        """Handle combo box selection changes."""
        enabled = bool(text) and text not in self.selected_attributes
        self.add_btn.setEnabled(enabled)

    def get_selected_attributes(self) -> Dict[str, int]:
        """Get the dictionary of selected attributes and their section counts."""
        return self.selected_attributes

