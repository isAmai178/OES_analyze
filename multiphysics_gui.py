#!/usr/bin/env python3
"""
Plasma Analyzer GUI Application
This module provides a graphical user interface for the Plasma Analyzer tool.

Author: [Your Name]
Date: [Current Date]
Version: 1.0.0
"""

import sys
import os
import pandas as pd
from typing import Optional, Dict, List
import logging
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from Multiphysics import PlasmaAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisParameters:
    """Data class for storing analysis parameters."""
    threshold: int = 200

class FileAttributeSelector(QGroupBox):
    """Custom widget for file attribute selection."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.attributes: List[str] = []
        self.selected_attributes: List[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.currentTextChanged.connect(self._on_selection_changed)
        
        self.selected_label = QLabel("已選擇的屬性：")
        self.selected_list = QTableWidget()
        self.selected_list.setColumnCount(1)
        self.selected_list.setHorizontalHeaderLabels(["屬性名稱"])
        
        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加")
        self.remove_btn = QPushButton("移除")
        self.add_btn.clicked.connect(self._add_attribute)
        self.remove_btn.clicked.connect(self._remove_attribute)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)

        layout.addWidget(QLabel("可用屬性："))
        layout.addWidget(self.combo_box)
        layout.addLayout(btn_layout)
        layout.addWidget(self.selected_label)
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
            self.selected_attributes.append(current_attr)
            self._update_selected_list()

    def _remove_attribute(self) -> None:
        """Remove selected attribute from the list."""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            removed_attr = self.selected_attributes.pop(current_row)
            self._update_selected_list()

    def _update_selected_list(self) -> None:
        """Update the selected attributes list display."""
        self.selected_list.setRowCount(len(self.selected_attributes))
        for i, attr in enumerate(self.selected_attributes):
            self.selected_list.setItem(i, 0, QTableWidgetItem(attr))

    def _on_selection_changed(self, text: str) -> None:
        """Handle combo box selection changes."""
        self.add_btn.setEnabled(text and text not in self.selected_attributes)

    def get_selected_attributes(self) -> List[str]:
        """Get the list of selected attributes."""
        return self.selected_attributes

class PlasmaAnalyzerGUI(QMainWindow):
    """Main window class for the Plasma Analyzer GUI application."""
    
    WINDOW_TITLE = 'Plasma Analyzer'
    WINDOW_GEOMETRY = (100, 100, 1400, 800)
    DEFAULT_PARAMS = AnalysisParameters()
    FILE_TYPES = ['RF.csv', 'BgCgTemp.csv', 'MFC.csv']
    
    def __init__(self):
        """Initialize the main window and setup UI components."""
        super().__init__()
        self.analyzer = PlasmaAnalyzer()
        self.file_selectors: Dict[str, FileAttributeSelector] = {}
        self._init_ui()
        logger.info("Plasma Analyzer GUI initialized")

    def _init_ui(self) -> None:
        """Initialize all UI components."""
        self._setup_window()
        self._create_main_layout()
        self._setup_file_section()
        self._setup_parameters_section()
        self._setup_file_attributes_section()
        self._setup_analysis_section()
        self._setup_results_section()

    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setGeometry(*self.WINDOW_GEOMETRY)

    def _create_main_layout(self) -> None:
        """Create and set the main layout."""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def _setup_file_section(self) -> None:
        """Setup the file selection section."""
        file_group = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText('選擇資料夾路徑...')
        
        browse_btn = QPushButton('瀏覽')
        browse_btn.clicked.connect(self._browse_folder)
        browse_btn.setFixedWidth(80)
        
        file_group.addWidget(QLabel('資料夾路徑:'))
        file_group.addWidget(self.path_edit)
        file_group.addWidget(browse_btn)
        
        self.main_layout.addLayout(file_group)

    def _setup_parameters_section(self) -> None:
        """Setup the parameters input section."""
        params_layout = QVBoxLayout()
        
        params_title = QLabel('參數設定')
        params_title.setStyleSheet('font-weight: bold; font-size: 14px;')
        params_layout.addWidget(params_title)

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel('power臨界值(範圍:0~1000):')
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 1000)
        self.threshold_spin.setValue(self.DEFAULT_PARAMS.threshold)
        self.threshold_spin.setFixedWidth(100)
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        
        params_layout.addLayout(threshold_layout)
        self.main_layout.addLayout(params_layout)

    def _setup_file_attributes_section(self) -> None:
        """Setup the file attributes selection section."""
        attributes_layout = QHBoxLayout()
        
        for file_type in self.FILE_TYPES:
            selector = FileAttributeSelector(file_type)
            self.file_selectors[file_type] = selector
            attributes_layout.addWidget(selector)
        
        self.main_layout.addLayout(attributes_layout)

    def _setup_analysis_section(self) -> None:
        """Setup the analysis and save buttons section."""
        button_layout = QHBoxLayout()
        
        # 分析按鈕
        analyze_btn = QPushButton('開始分析')
        analyze_btn.clicked.connect(self._analyze_data)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 儲存按鈕
        self.save_btn = QPushButton('儲存結果')
        self.save_btn.clicked.connect(self._save_results)
        self.save_btn.setEnabled(False)  # 初始時禁用
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #007B9A;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        button_layout.addWidget(analyze_btn)
        button_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(button_layout)

    def _setup_results_section(self) -> None:
        """Setup the results table section."""
        self.results_layout = QHBoxLayout()
        
        # Create a table for each file type
        self.result_tables = {}
        for file_type in self.FILE_TYPES:
            group = QGroupBox(f"{file_type} 分析結果")
            layout = QVBoxLayout()
            
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['屬性', '平均值', '標準差', '穩定度'])
            
            layout.addWidget(table)
            group.setLayout(layout)
            self.results_layout.addWidget(group)
            self.result_tables[file_type] = table
            
        self.main_layout.addLayout(self.results_layout)

    def _browse_folder(self) -> None:
        """Handle folder browsing action."""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
            if folder_path:
                self.path_edit.setText(folder_path)
                self._load_file_attributes(folder_path)
                
        except Exception as e:
            logger.error(f"Error during folder browsing: {e}")
            self._show_error("資料夾瀏覽錯誤", str(e))

    def _load_file_attributes(self, folder_path: str) -> None:
        """Load available attributes for each file type."""
        for file_type in self.FILE_TYPES:
            try:
                file_path = os.path.join(folder_path, file_type)
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    columns = df.columns.tolist()
                    if 'Time' in columns:
                        columns.remove('Time')
                    self.file_selectors[file_type].set_available_attributes(columns)
            except Exception as e:
                logger.error(f"Error loading attributes for {file_type}: {e}")

    def _analyze_data(self) -> None:
        """Handle data analysis action."""
        try:
            folder_path = self.path_edit.text()
            if not folder_path:
                self._show_warning("警告", "請先選擇資料夾路徑")
                return

            # 更新分析器的設定
            self.analyzer.set_folder_path(folder_path)
            self.analyzer.set_threshold(self.threshold_spin.value())
            
            # 更新檔案配置
            new_config = {}
            for file_type, selector in self.file_selectors.items():
                selected_attrs = selector.get_selected_attributes()
                if selected_attrs:
                    new_config[file_type] = selected_attrs
            
            if not new_config:
                self._show_warning("警告", "請至少選擇一個檔案的分析屬性")
                return
                
            self.analyzer.files_config = new_config
            logger.info(f"分析配置: {new_config}")

            # 執行分析
            self.results = self.analyzer.analyze_data()
            
            if not self.results:
                self._show_warning("警告", "分析未產生任何結果")
                return
                
            logger.info(f"分析結果: {self.results}")
            self._update_results_tables(self.results)
            self.save_btn.setEnabled(True)
            self._show_info("成功", "分析完成！")
            
        except Exception as e:
            logger.error(f"Error during data analysis: {e}")
            self._show_error("分析錯誤", str(e))

    def _update_results_tables(self, results: dict) -> None:
        """Update all results tables."""
        try:
            for file_type, table in self.result_tables.items():
                table.setRowCount(0)  # 清空表格
                if file_type in results:
                    data = results[file_type]
                    for attr, values in data.items():
                        row_position = table.rowCount()
                        table.insertRow(row_position)
                        
                        # Set attribute name
                        table.setItem(row_position, 0, QTableWidgetItem(str(attr)))
                        
                        # Set values
                        table.setItem(row_position, 1, QTableWidgetItem(f"{values['平均值']:.2f}"))
                        table.setItem(row_position, 2, QTableWidgetItem(f"{values['標準差']:.2f}"))
                        table.setItem(row_position, 3, QTableWidgetItem(f"{values['穩定度']:.2f}"))
                        
            logger.info("Results tables updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating results tables: {e}")
            raise

    def _save_results(self) -> None:
        """Handle results saving action."""
        try:
            if not hasattr(self, 'results'):
                self._show_warning("警告", "請先執行分析")
                return

            # 選擇儲存目錄
            save_dir = QFileDialog.getExistingDirectory(self, '選擇儲存位置')
            if not save_dir:
                return

            # 設定輸出路徑並儲存結果
            self.analyzer.output_path = save_dir
            self.analyzer.save_results(self.results)
            self._show_info("成功", "結果已成功儲存！")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            self._show_error("儲存錯誤", str(e))

    def _show_error(self, title: str, message: str) -> None:
        """Show error message box."""
        QMessageBox.critical(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show warning message box."""
        QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        """Show information message box."""
        QMessageBox.information(self, title, message)

def main():
    """
    GUI 應用程式主入口點
    """
    try:
        # 初始化 QApplication
        app = QApplication(sys.argv)
        
        # 建立並顯示主視窗
        logger.info("初始化 GUI 介面...")
        window = PlasmaAnalyzerGUI()
        window.show()
        
        # 執行應用程式
        logger.info("啟動 GUI 應用程式...")
        return app.exec()
        
    except Exception as e:
        logger.error(f"GUI 應用程式執行錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 