#!/usr/bin/env python3
"""
OES Analyzer GUI Application
This module provides a graphical user interface for the OES Analyzer tool.

Author: Benson
Date: 01/16/25
Version: 1.0.0
"""

import sys
import os
from typing import Tuple, Optional, List
import logging
from dataclasses import dataclass
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt
from oes_analyzer import OESAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisParameters:
    """Data class for storing analysis parameters."""
    detect_wave: int = 657
    threshold: float = 1000.0
    section_count: int = 3

class OESAnalyzerGUI(QMainWindow):
    """Main window class for the OES Analyzer GUI application."""
    
    # Class constants
    WINDOW_TITLE = 'OES Analyzer'
    WINDOW_GEOMETRY = (100, 100, 800, 600)
    DEFAULT_PARAMS = AnalysisParameters()
    
    def __init__(self):
        """Initialize the main window and setup UI components."""
        super().__init__()
        self.analyzer = OESAnalyzer()
        self._init_ui()
        logger.info("OES Analyzer GUI initialized")

    def _init_ui(self) -> None:
        """Initialize all UI components."""
        self._setup_window()
        self._create_main_layout()
        self._setup_file_section()
        self._setup_parameters_section()
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
        
        self.file_info_label = QLabel()
        self.main_layout.addWidget(self.file_info_label)

    def _setup_parameters_section(self) -> None:
        """Setup the parameters input section."""
        params_layout = QVBoxLayout()
        
        # Title
        params_title = QLabel('參數設定')
        params_title.setStyleSheet('font-weight: bold; font-size: 14px;')
        params_layout.addWidget(params_title)

        # Parameters grid
        params_grid = QHBoxLayout()
        params_grid.setSpacing(20)

        # Wave detection
        wave_layout = QVBoxLayout()
        wave_label = QLabel('檢測波長(nm):')
        self.detect_wave_spin = QDoubleSpinBox()
        self.detect_wave_spin.setRange(0.0, 1000.0)
        self.detect_wave_spin.setValue(self.DEFAULT_PARAMS.detect_wave)
        self.detect_wave_spin.setFixedWidth(100)
        wave_layout.addWidget(wave_label)
        wave_layout.addWidget(self.detect_wave_spin)
        params_grid.addLayout(wave_layout)

        # Threshold
        threshold_layout = QVBoxLayout()
        threshold_label = QLabel('光譜強度(a.u.):')
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setValue(self.DEFAULT_PARAMS.threshold)
        self.threshold_spin.setFixedWidth(100)
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        params_grid.addLayout(threshold_layout)

        # Section count
        section_layout = QVBoxLayout()
        section_label = QLabel('解離區段數:')
        self.section_spin = QSpinBox()
        self.section_spin.setRange(2, 10)
        self.section_spin.setValue(self.DEFAULT_PARAMS.section_count)
        self.section_spin.setFixedWidth(100)
        section_layout.addWidget(section_label)
        section_layout.addWidget(self.section_spin)
        params_grid.addLayout(section_layout)

        params_layout.addLayout(params_grid)
        self.main_layout.addLayout(params_layout)

    def _setup_analysis_section(self) -> None:
        """Setup the analysis button section."""
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
        self.main_layout.addWidget(analyze_btn)

    def _setup_results_section(self) -> None:
        """Setup the results table and save button section."""
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(['區段', '平均值', '標準差', '穩定度'])
        self.main_layout.addWidget(self.result_table)

        # 啟用右鍵選單
        self.result_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self._show_context_menu)

        save_btn = QPushButton('儲存結果')
        save_btn.clicked.connect(self._save_results)
        self.main_layout.addWidget(save_btn)

    def _browse_folder(self) -> None:
        """Handle folder browsing action."""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
            if not folder_path:
                return

            self.path_edit.setText(folder_path)
            self._update_file_info(folder_path)
            
        except Exception as e:
            logger.error(f"Error during folder browsing: {e}")
            self._show_error("資料夾瀏覽錯誤", str(e))

    def _update_file_info(self, folder_path: str) -> None:
        """Update file information display."""
        base_name, start_index, end_index = self._find_spectrum_files(folder_path)
        if base_name:
            self.base_name = base_name
            self.start_index = start_index
            self.end_index = end_index
            self.file_info_label.setText(
                f'找到檔案：\n'
                f'基本檔名：{base_name}\n'
                f'起始索引：{start_index}\n'
                f'結束索引：{end_index}'
            )
        else:
            self.file_info_label.setText('未找到符合格式的檔案')
            self._show_warning("警告", "在選擇的資料夾中未找到符合格式的檔案")

    @staticmethod
    def _find_spectrum_files(folder_path: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """Find spectrum files and return file information."""
        try:
            files = os.listdir(folder_path)
            spectrum_files = [f for f in files if f.endswith('.txt') and '_S' in f]
            
            if not spectrum_files:
                return None, None, None
            
            base_name = spectrum_files[0].split('_S')[0]            
            indices = []
            for file in spectrum_files:
                if file.startswith(base_name):
                    try:
                        index = int(file.split('_S')[-1].replace('.txt', ''))
                        indices.append(index)
                    except ValueError:
                        continue
            
            if not indices:
                return None, None, None
                
            return base_name, min(indices), max(indices)
            
        except Exception as e:
            logger.error(f"Error finding spectrum files: {e}")
            return None, None, None

    def _analyze_data(self) -> None:
        """Handle data analysis action."""
        try:
            if not self._validate_analysis_parameters():
                return

            base_path = self.path_edit.text()
            
            # Generate file names and read data
            file_names = self.analyzer.generate_file_names(
                self.base_name,
                self.start_index,
                self.end_index
            )
            self.analyzer.read_file_to_data(file_names, base_path)

            # Analyze data
            results_df = self.analyzer.analyze_data(
                base_path,
                self.base_name,
                detect_wave=self.detect_wave_spin.value(),
                threshold=self.threshold_spin.value(),
                section=self.section_spin.value(),
                start_index=self.start_index
            )

            self._update_results_table(results_df)
            self._show_info("成功", "分析完成！")
            
        except Exception as e:
            logger.error(f"Error during data analysis: {e}")
            self._show_error("分析錯誤", str(e))

    def _validate_analysis_parameters(self) -> bool:
        """Validate analysis parameters."""
        if not hasattr(self, 'base_name'):
            self._show_warning("警告", "請先選擇包含光譜檔案的資料夾")
            return False
        return True

    def _update_results_table(self, df: pd.DataFrame) -> None:
        """Update results table with analyzed data."""
        self.result_table.setRowCount(len(df))
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.result_table.setItem(i, j, item)

    def _save_results(self) -> None:
        """Handle results saving action."""
        try:
            base_path = self.path_edit.text()
            if not base_path:
                self._show_warning("警告", "請先選擇資料夾路徑")
                return

            data = self._get_table_data()
            df = pd.DataFrame(data, columns=['區段', '平均值', '標準差', '穩定度'])
            
            self.analyzer.save_to_excel(df, base_path, self.threshold_spin.value())
            self._show_info("成功", "結果已成功儲存！")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            self._show_error("儲存錯誤", str(e))

    def _get_table_data(self) -> List[List[str]]:
        """Get data from results table."""
        data = []
        for row in range(self.result_table.rowCount()):
            row_data = []
            for col in range(self.result_table.columnCount()):
                item = self.result_table.item(row, col)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        return data

    def _show_error(self, title: str, message: str) -> None:
        """Show error message box."""
        QMessageBox.critical(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show warning message box."""
        QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        """Show information message box."""
        QMessageBox.information(self, title, message)

    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        menu = QMenu()
        copy_cell_action = menu.addAction("複製當前儲存格")
        copy_row_action = menu.addAction("複製當前行")
        copy_all_action = menu.addAction("複製全部")
        
        action = menu.exec(self.result_table.mapToGlobal(pos))
        
        if action == copy_cell_action:
            self._copy_cell()
        elif action == copy_row_action:
            self._copy_row()
        elif action == copy_all_action:
            self._copy_all()

    def _copy_cell(self):
        """複製選中儲存格"""
        if self.result_table.currentItem() is not None:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.result_table.currentItem().text())
            self._show_info("複製成功", "已複製選中儲存格內容")

    def _copy_row(self):
        """複製整行"""
        current_row = self.result_table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(self.result_table.columnCount()):
                item = self.result_table.item(current_row, col)
                if item is not None:
                    row_data.append(item.text())
            
            clipboard = QApplication.clipboard()
            clipboard.setText('\t'.join(row_data))
            self._show_info("複製成功", "已複製整行內容")

    def _copy_all(self):
        """複製全部內容"""
        all_data = []
        # 添加表頭
        headers = []
        for col in range(self.result_table.columnCount()):
            headers.append(self.result_table.horizontalHeaderItem(col).text())
        all_data.append('\t'.join(headers))
        
        # 添加數據
        for row in range(self.result_table.rowCount()):
            row_data = []
            for col in range(self.result_table.columnCount()):
                item = self.result_table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
            all_data.append('\t'.join(row_data))
        
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(all_data))
        self._show_info("複製成功", "已複製全部內容")

def main():
    app = QApplication(sys.argv)
    gui = OESAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 