<<<<<<< HEAD
<<<<<<< HEAD
import os
from typing import List, Dict
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QTextEdit, QGroupBox, QMessageBox,QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGridLayout
from OES_analyze import OESAnalyzer  # 引入我們的分析類
=======
=======
#!/usr/bin/env python3
"""
OES Analyzer GUI Application
This module provides a graphical user interface for the OES Analyzer tool.

Author: Benson
Date: 01/16/25
Version: 1.0.0
"""

>>>>>>> 8c23e14 (新增多重物理量分析介面)
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
>>>>>>> de8bb88 (介面第一版-初始設計)

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
<<<<<<< HEAD
        self.analyzer = OESAnalyzer()  # 稍後初始化
        self.previous_values = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('OES 光譜分析工具')
        self.setGeometry(100, 100, 800, 600)
        
        # 創建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 創建各個設定區域
        self.create_file_selection(layout)
        self.create_save_directory_selection(layout)
        self.create_parameter_settings(layout)
        self.create_waveband_settings(layout)
        self.create_execute_button(layout)
        self.create_peak_display(layout)
        self.create_image_display(layout)  
        self.create_status_display(layout)
    
    def create_image_display(self, parent_layout):
        """創建圖片顯示區域"""
        group = QGroupBox("波長比較圖")
        layout = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(300)
        layout.addWidget(self.image_label)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def update_image_display(self, image_path: str):
        """更新圖片顯示"""
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def create_peak_display(self, parent_layout):
        """創建峰值顯示區域"""
        group = QGroupBox("峰值比較")
        layout = QVBoxLayout()
        
        self.peak_text = QTextEdit()
        self.peak_text.setReadOnly(True)
        self.peak_text.setMaximumHeight(150)  # 限制高度
        layout.addWidget(self.peak_text)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def update_peak_display(self, peak_points: List[Dict], comparison_results: List[Dict] = None):
        """更新峰值顯示"""
        peak_info = "當前數據的主要峰值點：\n"
        # 只顯示前5個最高點
        for point in peak_points[:5]:
            peak_info += (f"波段: {point['波段']:.1f} nm, "
                         f"最大值: {point['最大值']:.2f}, "
                         f"時間點: {point['時間點']}秒\n")
            
        if comparison_results:
            peak_info += "\n兩個數據集的比較結果：\n"
            for result in comparison_results:
                peak_info += f"\n波段: {result['波段']:.1f} nm\n"
                if result['數據集1_最大值'] is not None:
                    peak_info += f"數據集1: 最大值={result['數據集1_最大值']:.2f}, 時間點={result['數據集1_時間點']}秒\n"
                if result['數據集2_最大值'] is not None:
                    peak_info += f"數據集2: 最大值={result['數據集2_最大值']:.2f}, 時間點={result['數據集2_時間點']}秒\n"
                if '差異' in result:
                    peak_info += f"差異: {result['差異']:.2f}\n"

        self.peak_text.setText(peak_info)
    
    def create_file_selection(self, parent_layout):
        group = QGroupBox("檔案設定")
        layout = QVBoxLayout()
        
        # 資料夾選擇
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        browse_button = QPushButton("瀏覽")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(QLabel("資料夾路徑:"))
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(browse_button)
        
        # 檔案名稱格式
=======
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
<<<<<<< HEAD
        layout.addLayout(file_group)

        # 基本名稱輸入
>>>>>>> de8bb88 (介面第一版-初始設計)
        name_layout = QHBoxLayout()
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setPlaceholderText('輸入基本檔名...')
        name_layout.addWidget(QLabel('基本檔名:'))
        name_layout.addWidget(self.base_name_edit)
        layout.addLayout(name_layout)
<<<<<<< HEAD
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_save_directory_selection(self, parent_layout):
        group = QGroupBox("保存路徑設定")
        layout = QVBoxLayout()
        
        # 保存路徑選擇
        save_folder_layout = QHBoxLayout()
        self.save_folder_path = QLineEdit()
        save_browse_button = QPushButton("選擇保存路徑")
        save_browse_button.clicked.connect(self.browse_save_folder)
        save_folder_layout.addWidget(QLabel("保存路徑:"))
        save_folder_layout.addWidget(self.save_folder_path)
        save_folder_layout.addWidget(save_browse_button)
        
        layout.addLayout(save_folder_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def browse_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇保存路徑")
        if folder:
            self.save_folder_path.setText(folder)

    def create_parameter_settings(self, parent_layout):
        group = QGroupBox("參數設定")
        layout = QVBoxLayout()
        
        # 起始值設定
        start_layout = QHBoxLayout()
        self.start_value = QLineEdit("195.0")
        start_layout.addWidget(QLabel("全波段起始值:"))
        start_layout.addWidget(self.start_value)
        
        # 初始範圍設定
        range_layout = QHBoxLayout()
        self.initial_start = QLineEdit("10")
        self.initial_end = QLineEdit("70")
        range_layout.addWidget(QLabel("初始範圍(實驗秒數):"))
        range_layout.addWidget(self.initial_start)
        range_layout.addWidget(QLabel("到"))
        range_layout.addWidget(self.initial_end)
        
        # 添加跳過範圍設定
        skip_layout = QHBoxLayout()
        self.skip_range = QLineEdit("10")
        skip_layout.addWidget(QLabel("最高峰值跳過範圍(nm):"))
        skip_layout.addWidget(self.skip_range)
        
        # 添加過濾強度勾選框
        self.filter_checkbox = QCheckBox("過濾低於指定強度")
        self.intensity_threshold = QLineEdit("1000")  # 默認強度閾值
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(self.filter_checkbox)
        intensity_layout.addWidget(QLabel("想過濾的強度值:"))
        intensity_layout.addWidget(self.intensity_threshold)
        layout.addLayout(intensity_layout)

        layout.addLayout(start_layout)
        layout.addLayout(range_layout)
        layout.addLayout(skip_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_waveband_settings(self, parent_layout):
        group = QGroupBox("波段設定")
        layout = QVBoxLayout()
        
        # 特定波段設定
        self.wavebands = QLineEdit("486.0, 612.0, 656.0, 777.0")
        layout.addWidget(QLabel("特定波段值(必填) (用逗號分隔):"))
        layout.addWidget(self.wavebands)
        
        # 變化量設定
        self.thresholds = QLineEdit("250, 350, 450, 550")
        layout.addWidget(QLabel("變化量 (用逗號分隔):"))
        layout.addWidget(self.thresholds)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_execute_button(self, parent_layout):
        self.execute_button = QPushButton("執行分析")
        self.execute_button.clicked.connect(self.execute_analysis)
        parent_layout.addWidget(self.execute_button)
        
    def create_status_display(self, parent_layout):
        group = QGroupBox("執行狀態")
        layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
=======

        # 參數設定區域
        params_layout = QHBoxLayout()
>>>>>>> de8bb88 (介面第一版-初始設計)
=======
>>>>>>> 8c23e14 (新增多重物理量分析介面)
        
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

<<<<<<< HEAD
    def browse_folder(self):
<<<<<<< HEAD
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            self.folder_path.setText(folder)
            
    def update_status(self, message):
        self.status_text.append(message)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
        
    def execute_analysis(self):
        # 點下按鈕會開始執行分析
=======
        folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
        if folder_path:
            self.path_edit.setText(folder_path)

    def analyze_data(self):
>>>>>>> de8bb88 (介面第一版-初始設計)
=======
    def _browse_folder(self) -> None:
        """Handle folder browsing action."""
>>>>>>> 8c23e14 (新增多重物理量分析介面)
        try:
            folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
            if not folder_path:
                return
<<<<<<< HEAD
            
            save_folder_path = self.save_folder_path.text()
            if not save_folder_path:
                QMessageBox.warning(self, "警告", "請選擇保存路徑")
                return
            
            # 解析輸入值
            base_name = self.base_name.text()
            start_value = float(self.start_value.text())
            initial_start = int(self.initial_start.text())
            initial_end = int(self.initial_end.text())
            wavebands = [float(x.strip()) for x in self.wavebands.text().split(",")]
            thresholds = [float(x.strip()) for x in self.thresholds.text().split(",")]
            skip_range_nm = float(self.skip_range.text())  # 獲取跳過範圍

            # 生成文件路徑列表
            file_paths = [
                os.path.join(folder_path, f"{base_name}{i:04d}.txt") 
                for i in range(initial_start, initial_end + 1)
            ]

            file_name = base_name.split('_')[1]  # 取得檔案前段名稱(通常為時間)
            
            # 創建分析器並設置回調
            self.analyzer = OESAnalyzer(start_value=start_value)
            self.analyzer.set_status_callback(self.update_status)
            self.analyzer.set_files(file_paths)
        
            # 執行分析
            self.update_status("開始分析...")

            #使用用戶選擇的保存路徑新增資料夾名為
            if os.path.basename(save_folder_path) == "OES光譜分析結果":
                output_directory = save_folder_path
            else:
                output_directory = os.path.join(save_folder_path, "OES光譜分析結果")
                os.makedirs(output_directory,exist_ok=True)

            excel_file, specific_excel_file = self.analyzer.analyze_and_export(
                wavebands=wavebands,
                thresholds=thresholds,
                initial_start=initial_start,
                initial_end=initial_end,
                skip_range_nm=skip_range_nm,  # 傳遞跳過範圍
                output_directory=output_directory  # 傳遞用戶選擇的保存路徑
=======

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
<<<<<<< HEAD
                base_name,
                self.start_index_spin.value(),
                self.end_index_spin.value()
>>>>>>> de8bb88 (介面第一版-初始設計)
=======
                self.base_name,
                self.start_index,
                self.end_index
>>>>>>> 8c23e14 (新增多重物理量分析介面)
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

<<<<<<< HEAD
            # 更新表格
            self.update_table(results_df)
            
<<<<<<< HEAD
            # 檢查是否需要過濾低強度波段
            intensity_threshold = None
            if self.filter_checkbox.isChecked():
                intensity_threshold = float(self.intensity_threshold.text())
                self.analyzer.filter_low_intensity(intensity_threshold)

            # 找出並顯示峰值點
            peak_points = self.analyzer.find_peak_points(self.analyzer.all_values)

           
            self.update_status("開始生成全波段圖...")

            # # 儲存全波段圖
            # current_dir = os.path.dirname(os.path.abspath(__file__))
            # output_directory = os.path.join(current_dir, "OES光譜分析結果")
            # os.makedirs(output_directory, exist_ok=True)

            # 生成全波段圖
            output_path = self.analyzer.allSpectrum_plot(
                self.analyzer.all_values,  # data1
                float(self.skip_range.text()),  # skip_nm
                output_directory,  # output_directory
                file_name
            )

            self.update_image_display(output_path)

            self.update_peak_display(peak_points)

            # # 保存當前分析結果供下次比較
            # self.previous_values = self.analyzer.all_values.copy()
            # self.update_status(f"已保存當前分析結果，包含 {len(self.analyzer.all_values)} 個波長點")
        
            result_message = (
                f"分析完成！結果已保存至：{os.path.basename(save_folder_path)}\n"
                f"1. 光譜變化分析：{os.path.basename(excel_file)}\n"
                f"2. 特定波段分析：{os.path.basename(specific_excel_file)}\n"
                f"3. 全波段圖與前三強波段：{os.path.basename(output_path)}"
            )
            self.update_status(result_message)
            QMessageBox.information(self, "完成", result_message)
=======
            QMessageBox.information(self, '成功', '分析完成！')
>>>>>>> de8bb88 (介面第一版-初始設計)
=======
            self._update_results_table(results_df)
            self._show_info("成功", "分析完成！")
>>>>>>> 8c23e14 (新增多重物理量分析介面)
            
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