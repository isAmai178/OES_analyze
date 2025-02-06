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
    QGroupBox, QGridLayout, QMenu, QDialog, QDialogButtonBox
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
        enabled = bool(text) and text not in self.selected_attributes
        self.add_btn.setEnabled(enabled)

    def get_selected_attributes(self) -> List[str]:
        """Get the list of selected attributes."""
        return self.selected_attributes

class SectionInputDialog(QDialog):
    """對話框用於輸入區段數"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定區段數")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # 區段數輸入
        input_layout = QHBoxLayout()
        self.section_spin = QSpinBox()
        self.section_spin.setRange(2, 10)  # 最少2個區段，最多10個
        self.section_spin.setValue(3)
        input_layout.addWidget(QLabel("請輸入要分析的區段數:"))
        input_layout.addWidget(self.section_spin)

        # 確認和取消按鈕
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(input_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

class SectionResultDialog(QDialog):
    """對話框用於顯示區段分析結果"""
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.setWindowTitle("區段分析結果")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # 創建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['區段', '平均值', '標準差', '穩定度'])

        # 填充數據
        self.table.setRowCount(len(self.results))
        for i, (section, values) in enumerate(self.results.items()):
            self.table.setItem(i, 0, QTableWidgetItem(f"區段 {section}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{values['平均值']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{values['標準差']:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{values['穩定度']:.2f}"))

        # 調整表格大小
        self.table.resizeColumnsToContents()
        
        # 添加關閉按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)

        layout.addWidget(self.table)
        layout.addWidget(button_box)
        self.setLayout(layout)

class PlasmaAnalyzerGUI(QMainWindow):
    """Main window class for the Plasma Analyzer GUI application."""
    
    WINDOW_TITLE = 'Plasma Analyzer'
    WINDOW_GEOMETRY = (100, 100, 1400, 800)
    DEFAULT_PARAMS = AnalysisParameters()
    FILE_TYPES = ['RF.csv', 'BgCgTemp.csv', 'MFC.csv']
    
    def __init__(self):
        """初始化主畫面和UI設定元件"""
        super().__init__()
        self.analyzer = PlasmaAnalyzer()
        self.file_selectors: Dict[str, FileAttributeSelector] = {}
        self._init_ui()
        logger.info("Plasma Analyzer GUI initialized")

    def _init_ui(self) -> None:
        """初始化所有元件."""
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
        """主介面創建."""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def _setup_file_section(self) -> None:
        """設定資料夾路徑區"""
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
        """設定參數輸入區"""
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
        """設定分析和結果儲存按鈕區."""
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
        """設定結果表格區"""
        self.results_layout = QHBoxLayout()
        
        # Create a table for each file type
        self.result_tables = {}
        for file_type in self.FILE_TYPES:
            group = QGroupBox(f"{file_type} 分析結果")
            layout = QVBoxLayout()
            
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['屬性', '平均值', '標準差', '穩定度'])
            
            # 設定每個欄位的寬度
            table.setColumnWidth(0, 150)
            table.setColumnWidth(1, 100)
            table.setColumnWidth(2, 100)
            table.setColumnWidth(3, 100)
            
            # 啟用右鍵選單
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(
                lambda pos, table=table: self._show_context_menu(pos, table)
            )
            
            layout.addWidget(table)
            group.setLayout(layout)
            self.results_layout.addWidget(group)
            self.result_tables[file_type] = table
            
        self.main_layout.addLayout(self.results_layout)

    def _show_context_menu(self, pos, table):
        """顯示右鍵選單"""
        # 獲取點擊位置的項目
        item = table.itemAt(pos)
        
        if item is not None:
            menu = QMenu()
            
            # 添加選單項目
            copy_action = menu.addAction("複製選中儲存格")
            copy_row_action = menu.addAction("複製整行")
            copy_all_action = menu.addAction("複製全部")
            menu.addSeparator()
            custom_analyze_action = menu.addAction("自訂義分析")
            
            # 顯示選單
            action = menu.exec(table.viewport().mapToGlobal(pos))
            
            # 處理選單動作
            if action == copy_action:
                self._copy_cell(table)
            elif action == copy_row_action:
                self._copy_row(table)
            elif action == copy_all_action:
                self._copy_all(table)
            elif action == custom_analyze_action:
                self._custom_analyze(table)

    def _copy_cell(self, table):
        """複製選中儲存格"""
        if table.currentItem() is not None:
            clipboard = QApplication.clipboard()
            clipboard.setText(table.currentItem().text())
            self._show_info("複製成功", "已複製選中儲存格內容")

    def _copy_row(self, table):
        """複製整行"""
        current_row = table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(current_row, col)
                if item is not None:
                    row_data.append(item.text())
            
            clipboard = QApplication.clipboard()
            clipboard.setText('\t'.join(row_data))
            self._show_info("複製成功", "已複製整行內容")

    def _copy_all(self, table):
        """複製全部內容"""
        all_data = []
        # 添加表頭
        headers = []
        for col in range(table.columnCount()):
            headers.append(table.horizontalHeaderItem(col).text())
        all_data.append('\t'.join(headers))
        
        # 添加數據
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
            all_data.append('\t'.join(row_data))
        
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(all_data))
        self._show_info("複製成功", "已複製全部內容")

    def _custom_analyze(self, table):
        """自定義區段分析"""
        try:
            # 獲取要分析的數據
            current_row = table.currentRow()
            if current_row < 0:
                self._show_warning("警告", "請先選擇要分析的屬性")
                return

            # 獲取屬性名稱
            attr_name = table.item(current_row, 0).text()
            
            # 顯示區段數輸入對話框
            dialog = SectionInputDialog(self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # 獲取區段數
            section_count = dialog.section_spin.value()

            # 從原始數據中獲取該屬性的時間序列
            folder_path = self.path_edit.text()
            for file_type, file_table in self.result_tables.items():
                if table == file_table:
                    file_path = os.path.join(folder_path, file_type)
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                        if attr_name in df.columns:
                            # 獲取激發時間範圍內的數據
                            df_activated = df[
                                (df['Time'] >= self.analyzer.activate_time) & 
                                (df['Time'] <= self.analyzer.end_time)
                            ]
                            
                            # 計算每個區段的長度
                            section_length = len(df_activated) // section_count
                            
                            # 分析每個區段
                            section_results = {}
                            for i in range(section_count):
                                start_idx = i * section_length
                                end_idx = start_idx + section_length if i < section_count - 1 else len(df_activated)
                                section_data = df_activated[attr_name].iloc[start_idx:end_idx]
                                
                                mean_val = section_data.mean()
                                std_val = section_data.std()
                                stability = (std_val / mean_val) * 100 if mean_val != 0 else 0
                                
                                section_results[i + 1] = {
                                    '平均值': mean_val,
                                    '標準差': std_val,
                                    '穩定度': stability
                                }
                            
                            # 顯示結果對話框
                            result_dialog = SectionResultDialog(section_results, self)
                            result_dialog.exec()
                            return

            self._show_warning("警告", "找不到對應的數據")
            
        except Exception as e:
            logger.error(f"自定義分析時發生錯誤: {e}")
            self._show_error("分析錯誤", str(e))

    def _browse_folder(self) -> None:
        """Handle folder browsing action."""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
            if folder_path:
                self.path_edit.setText(folder_path)
                # 清理舊的選擇和結果
                self._clear_all_data()
                # 載入新的屬性
                self._load_file_attributes(folder_path)
                
        except Exception as e:
            logger.error(f"Error during folder browsing: {e}")
            self._show_error("資料夾瀏覽錯誤", str(e))

    def _clear_all_data(self) -> None:
        """清理所有數據和選擇"""
        # 清理所有選擇器的數據
        for selector in self.file_selectors.values():
            selector.combo_box.clear()
            selector.selected_attributes.clear()
            selector._update_selected_list()

        # 清理所有結果表格
        for table in self.result_tables.values():
            table.setRowCount(0)

        # 禁用儲存按鈕
        self.save_btn.setEnabled(False)

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
                else:
                    logger.warning(f"File not found: {file_path}")
                    self.file_selectors[file_type].set_available_attributes([])
            except Exception as e:
                logger.error(f"Error loading attributes for {file_type}: {e}")
                self.file_selectors[file_type].set_available_attributes([])

    def _analyze_data(self) -> None:
        """資料分析區段"""
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
        """更新結果表格"""
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