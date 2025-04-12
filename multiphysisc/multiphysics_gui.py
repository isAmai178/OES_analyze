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
    QGroupBox, QGridLayout, QMenu, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QListView, QTreeView
)
from PyQt6.QtCore import Qt
from Multiphysics import PlasmaAnalyzer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from matplotlib.font_manager import FontProperties
import matplotlib as mpl

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

class AnalysisPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            mpl.rcParams['font.family'] = ['Microsoft JhengHei', 'sans-serif']
            mpl.rcParams['axes.unicode_minus'] = False
        except Exception as e:
            logger.error(f"Error setting font: {e}")
            
        self.figure = Figure(figsize=(12, 5))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(right=0.85)

    def plot_data(self, data, results, activate_time, end_time):
        """繪製數據和區段分析圖"""
        try:
            self.ax.clear()
            
            # 使用索引作為 x 軸
            x = np.arange(len(data))
            
            # 繪製原始數據
            self.ax.plot(x, data, 'b-', linewidth=1, label='原始數據')
            
            # 找到激發區間的索引
            start_idx = activate_time
            end_idx = end_time
            
            # 計算激發區間內的區段
            sections = [key for key in results.keys() if key != '總區段']
            active_duration = end_idx - start_idx
            points_per_section = active_duration // len(sections)
            
            # 繪製區段分隔線和標籤
            for i in range(len(sections)):
                section_start = start_idx + i * points_per_section
                
                # 繪製分隔線
                if i > 0:  # 不在第一個區段的開始畫線
                    self.ax.axvline(x=section_start, color='r', linestyle='-', alpha=0.5)
                
                # 添加區段標籤
                if i == len(sections) - 1:
                    # 最後一個區段
                    section_center = (section_start + end_idx) / 2
                else:
                    section_center = (section_start + (start_idx + (i + 1) * points_per_section)) / 2
                
                # 在區段中心上方添加標籤
                y_pos = max(data) + (max(data) - min(data)) * 0.05
                self.ax.text(section_center, y_pos, f'區段{i+1}', 
                           horizontalalignment='center',
                           verticalalignment='bottom')
            
            # 設置圖表屬性
            self.ax.set_xlabel('時間')
            self.ax.set_ylabel('數值')
            self.ax.grid(True)
            
            # 調整布局
            self.figure.tight_layout()
            
            # 更新畫布
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error in plot_data: {e}")
            raise

class PlotDialog(QDialog):
    """對話框用於顯示分析圖表"""
    def __init__(self, data, results, activate_time, end_time, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分析圖表")
        self.setMinimumSize(1000, 500)
        
        layout = QVBoxLayout()
        
        # 創建圖表
        self.plot = AnalysisPlot()
        self.plot.plot_data(data, results, activate_time, end_time)
        
        # 添加關閉按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.plot)
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
        
        folder_layout = QHBoxLayout()
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # 允許多選
        btn_layout = QVBoxLayout()
        add_btn = QPushButton('添加資料夾')
        add_btn.clicked.connect(self._add_folder)
        add_multiple_btn = QPushButton('批次添加')  # 新增批次添加按鈕
        add_multiple_btn.clicked.connect(self._add_multiple_folders)
        remove_btn = QPushButton('移除所選')
        remove_btn.clicked.connect(self._remove_folder)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(add_multiple_btn)
        btn_layout.addWidget(remove_btn)
        
        folder_layout.addWidget(self.folder_list)
        folder_layout.addLayout(btn_layout)
        
        file_group.addWidget(QLabel('已選擇的資料夾：'))
        file_group.addLayout(folder_layout)
        
        self.main_layout.addLayout(file_group)

    def _add_folder(self) -> None:
        """添加資料夾到列表"""
        folder_paths = QFileDialog.getExistingDirectory(
            self, 
            '選擇資料夾',
            options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        )
        
        if folder_paths:
            # 如果是第一個資料夾，載入屬性
            if self.folder_list.count() == 0:
                self._load_file_attributes(folder_paths)
            self.folder_list.addItem(QListWidgetItem(folder_paths))

    def _add_multiple_folders(self) -> None:
        """批次添加多個資料夾"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        # 獲取檔案列表視圖並設定為多選
        listview = dialog.findChild(QListView, 'listView')
        if listview:
            listview.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        treeview = dialog.findChild(QTreeView)
        if treeview:
            treeview.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
            
        if dialog.exec() == QDialog.DialogCode.Accepted:
            folders = dialog.selectedFiles()
            for folder in folders:
                if self.folder_list.count() == 0:
                    self._load_file_attributes(folder)
                self.folder_list.addItem(QListWidgetItem(folder))

    def _remove_folder(self) -> None:
        """從列表中移除所選資料夾"""
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))

    def _on_folder_changed(self, folder: str) -> None:
        """處理資料夾選擇變更"""
        if folder and hasattr(self, 'folder_path_map'):
            self.current_folder = self.folder_path_map[folder]
            self._update_all_tables()

    def _setup_parameters_section(self) -> None:
        """設定參數輸入區"""
        params_layout = QVBoxLayout()
        
        params_title = QLabel('參數設定')
        params_title.setStyleSheet('font-weight: bold; font-size: 14px;')
        params_layout.addWidget(params_title)

        # 移除臨界值設定
        # threshold_layout = QHBoxLayout()
        # threshold_label = QLabel('power臨界值(範圍:0~1000):')
        # self.threshold_spin = QSpinBox()
        # self.threshold_spin.setRange(0, 1000)
        # self.threshold_spin.setValue(self.DEFAULT_PARAMS.threshold)
        # self.threshold_spin.setFixedWidth(100)
        # threshold_layout.addWidget(threshold_label)
        # threshold_layout.addWidget(self.threshold_spin)
        # threshold_layout.addStretch()
        
        # params_layout.addLayout(threshold_layout)
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
        """Setup the results table section."""
        
        # 添加資料夾選擇器
        folder_select_layout = QHBoxLayout()
        folder_select_layout.addWidget(QLabel("選擇資料夾："))
        self.folder_combo = QComboBox()
        self.folder_combo.setMinimumWidth(500)  # 設定最小寬度
        self.folder_combo.currentTextChanged.connect(self._on_folder_changed)
        folder_select_layout.addWidget(self.folder_combo)
        folder_select_layout.addStretch()
        self.main_layout.addLayout(folder_select_layout)

        self.results_layout = QHBoxLayout()
        # Create a results section for each file type
        self.result_sections = {}
        for file_type in self.FILE_TYPES:
            group = QGroupBox(f"{file_type} 分析結果")
            layout = QVBoxLayout()
            
            # Add attribute selector combo box
            attr_selector = QComboBox()
            attr_selector.currentTextChanged.connect(
                lambda text, ft=file_type: self._on_attribute_selected(ft, text)
            )
            
            # Add results table
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['區段', '平均值', '標準差', '穩定度'])
            
            # Set column widths
            table.setColumnWidth(0, 100)
            table.setColumnWidth(1, 100)
            table.setColumnWidth(2, 100)
            table.setColumnWidth(3, 100)
            
            # 啟用右鍵選單
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(
                lambda pos, t=table: self._show_context_menu(pos, t)
            )
            
            layout.addWidget(attr_selector)
            layout.addWidget(table)
            group.setLayout(layout)
            
            self.results_layout.addWidget(group)
            self.result_sections[file_type] = {
                'selector': attr_selector,
                'table': table
            }
        
        self.main_layout.addLayout(self.results_layout)

    def _analyze_data(self) -> None:
        """處理數據分析動作"""
        try:
            selected_folders = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
            if not selected_folders:
                self._show_warning("警告", "請先選擇資料夾")
                return

            self.results = {}
            for folder in selected_folders:
                # 檢查所需檔案是否存在
                if not all(os.path.exists(os.path.join(folder, file)) for file in self.FILE_TYPES):
                    logger.warning(f"資料夾 {folder} 未包含所有必要檔案，已跳過")
                    continue

                # 設定資料夾路徑並尋找激發時間
                self.analyzer.set_folder_path(folder)
                self.analyzer.find_activation_time()
                activation_time = self.analyzer.activate_time
                end_time = self.analyzer.end_time

                # 執行分析
                folder_results = {}
                for file_type, selector in self.file_selectors.items():
                    selected_attrs = selector.get_selected_attributes()
                    if selected_attrs:
                        file_results = {}
                        for attr, sections in selected_attrs.items():
                            section_results = self.analyzer.analyze_sections(file_type, attr, sections)
                            total_results = self.analyzer.analyze_sections(file_type, attr, 1)
                            section_results['總區段'] = total_results[1]
                            file_results[attr] = section_results
                        folder_results[file_type] = file_results
                self.results[folder] = {
                    'activation_time': activation_time,
                    'end_time': end_time,
                    'analysis': folder_results
                }

            if not self.results:
                self._show_warning("警告", "分析未產生任何結果")
                return

            # 更新資料夾選擇器並顯示結果
            self.folder_combo.clear()
            # 保存完整路徑和基底名稱的對應關係
            self.folder_path_map = {}
            for folder in self.results.keys():
                folder_name = os.path.basename(folder)
                self.folder_path_map[folder_name] = folder
                self.folder_combo.addItem(folder_name)
            if self.results:
                self.folder_combo.setCurrentIndex(0)
                self.current_folder = list(self.results.keys())[0]  # 使用完整路徑作為當前資料夾
                self._update_results_selectors()
                self._update_all_tables()
                self.save_btn.setEnabled(True)
                self._show_info("成功", "分析完成！")
            
        except Exception as e:
            logger.error(f"數據分析時發生錯誤: {e}")
            self._show_error("分析錯誤", str(e))

    def _update_all_tables(self) -> None:
        """更新所有結果表格"""
        for file_type in self.FILE_TYPES:
            self._update_table(file_type)

    def _update_table(self, file_type: str) -> None:
        """更新特定檔案類型的結果表格"""
        attribute = self.result_sections[file_type]['selector'].currentText()
        if attribute and self.current_folder in self.results:
            table = self.result_sections[file_type]['table']
            results = self.results[self.current_folder]['analysis'][file_type][attribute]
            total_rows = len(results)
            table.setRowCount(total_rows)
            row = 0
            for section, values in results.items():
                if section == '總區段':
                    continue
                table.setItem(row, 0, QTableWidgetItem(f"區段 {section}"))
                table.setItem(row, 1, QTableWidgetItem(f"{values['平均值']:.2f}"))
                table.setItem(row, 2, QTableWidgetItem(f"{values['標準差']:.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{values['穩定度']:.2f}"))
                row += 1
            if '總區段' in results:
                total_values = results['總區段']
                table.setItem(row, 0, QTableWidgetItem("總區段"))
                table.setItem(row, 1, QTableWidgetItem(f"{total_values['平均值']:.2f}"))
                table.setItem(row, 2, QTableWidgetItem(f"{total_values['標準差']:.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{total_values['穩定度']:.2f}"))

    def _update_results_selectors(self) -> None:
        """更新屬性選擇器"""
        if self.results:
            first_folder = list(self.results.keys())[0]
            for file_type, section in self.result_sections.items():
                selector = section['selector']
                selector.clear()
                if file_type in self.results[first_folder]['analysis']:
                    attributes = list(self.results[first_folder]['analysis'][file_type].keys())
                    selector.addItems(attributes)
                    if attributes:
                     selector.setCurrentIndex(0)

    def _on_attribute_selected(self, file_type: str, attribute: str) -> None:
        """處理結果區的屬性選擇變更"""
        if self.current_folder and file_type in self.results[self.current_folder]['analysis']:
            self._update_table(file_type)
        


    def _show_context_menu(self, pos, table):
        """顯示右鍵選單"""
        menu = QMenu()
        copy_cell_action = menu.addAction("複製當前儲存格")
        copy_row_action = menu.addAction("複製當前行")
        copy_all_action = menu.addAction("複製全部")
        menu.addSeparator()  # 添加分隔線
        show_plot_action = menu.addAction("顯示圖表")  # 新增圖表選項
        
        action = menu.exec(table.mapToGlobal(pos))
        
        if action == copy_cell_action:
            self._copy_cell(table)
        elif action == copy_row_action:
            self._copy_row(table)
        elif action == copy_all_action:
            self._copy_all(table)
        elif action == show_plot_action:
            self._show_plot(table)

    def _copy_cell(self, table):
        """複製選中儲存格"""
        if table.currentItem() is not None:
            clipboard = QApplication.clipboard()
            clipboard.setText(table.currentItem().text())
            self._show_info("複製成功", "已複製選中儲存格內容")

    def _copy_row(self, table):
        """複製整行數值"""
        current_row = table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(1, table.columnCount()):  # 跳過第一列（區段標籤）
                item = table.item(current_row, col)
                if item is not None:
                    row_data.append(item.text())
            
            clipboard = QApplication.clipboard()
            clipboard.setText('\t'.join(row_data))
            self._show_info("複製成功", "已複製整行數值")

    def _copy_all(self, table):
        """複製全部數值"""
        all_data = []
        # 添加數據（跳過第一列）
        for row in range(table.rowCount()):
            row_data = []
            for col in range(1, table.columnCount()):  # 跳過第一列（區段標籤）
                item = table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
            all_data.append('\t'.join(row_data))
        
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(all_data))
        self._show_info("複製成功", "已複製全部數值")

    def _show_plot(self, table):
        """顯示分析圖表"""
        try:
            for file_type, section in self.result_sections.items():
                if section['table'] == table:
                    attribute = section['selector'].currentText()
                    if attribute and self.current_folder in self.results:
                        df = pd.read_csv(os.path.join(self.current_folder, file_type))
                        data = df[attribute].values
                        
                        df['Time_seconds'] = df['Time'].apply(lambda x: sum(float(i) * m for i, m in zip(x.split(':'), [3600, 60, 1])))
                        activation_time = self.results[self.current_folder]['activation_time']
                        end_time = self.results[self.current_folder]['end_time']
                        start_idx = np.where(df['Time_seconds'] >= float(activation_time.split(':')[0]) * 3600 + 
                                            float(activation_time.split(':')[1]) * 60 + 
                                            float(activation_time.split(':')[2]))[0][0]
                        end_idx = np.where(df['Time_seconds'] <= float(end_time.split(':')[0]) * 3600 + 
                                        float(end_time.split(':')[1]) * 60 + 
                                        float(end_time.split(':')[2]))[0][-1]
                        
                        dialog = PlotDialog(data, self.results[self.current_folder]['analysis'][file_type][attribute], 
                                            start_idx, end_idx, self)
                        dialog.exec()
                        break
        except Exception as e:
            logger.error(f"顯示圖表時發生錯誤: {e}")
            self._show_error("圖表顯示錯誤", str(e))

    def _clear_all_data(self) -> None:
        """清理所有數據和選擇"""
        # 清理所有選擇器的數據
        for selector in self.file_selectors.values():
            selector.combo_box.clear()
            selector.selected_attributes.clear()
            selector._update_selected_list()

        # 清理所有結果表格
        for table in self.result_sections.values():
            table['table'].setRowCount(0)

        # 禁用儲存按鈕
        self.save_btn.setEnabled(False)

    def _load_file_attributes(self, folder_path: str) -> None:
        for file_type in self.FILE_TYPES:  # FILE_TYPES 包含 'RF.csv', 'MFC.csv', 'BgCgTemp.csv'
            try:
                file_path = os.path.join(folder_path, file_type)
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    columns = df.columns.tolist()
                    if 'Time' in columns:
                        columns.remove('Time')  # 移除 'Time' 欄位，避免作為特徵屬性
                    self.file_selectors[file_type].set_available_attributes(columns)
                else:
                    logger.warning(f"檔案不存在: {file_path}")
                    self.file_selectors[file_type].set_available_attributes([])
            except Exception as e:
                logger.error(f"載入 {file_type} 的屬性時發生錯誤: {e}")
                self.file_selectors[file_type].set_available_attributes([])

    def _save_results(self) -> None:
        """處理結果儲存動作"""
        try:
            if not self.results:
                self._show_warning("警告", "請先執行分析")
                return

            base_save_dir = QFileDialog.getExistingDirectory(self, '選擇儲存位置')
            if base_save_dir:
                for folder in self.results:
                    folder_name = os.path.basename(folder)
                    save_path = os.path.join(base_save_dir, folder_name)
                    os.makedirs(save_path, exist_ok=True)
                    self.analyzer.output_path = save_path
                    self.analyzer.save_results(self.results[folder]['analysis'])
                self._show_info("成功", "結果已成功儲存！")
            
        except Exception as e:
            logger.error(f"儲存結果時發生錯誤: {e}")
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