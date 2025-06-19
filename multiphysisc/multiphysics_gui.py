import sys
import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
import logging
from dataclasses import dataclass
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,  QFileDialog, 
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QGroupBox,  QMenu, QDialog, QListWidget,
    QListWidgetItem, QListView, QTreeView
)
from PyQt6.QtCore import Qt
from Multiphysics import PlasmaAnalyzer
from Attribute_Selector import FileAttributeSelector
from Plot_data import PlotDialog, AttributeSelectionDialog, AnalysisPlot, ErrorBarPlot

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
        self.results: Dict[str, Any] = {}
        self.current_folder: Optional[str] = None
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
        self.folder_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        btn_layout = QVBoxLayout()
        add_btn = QPushButton('添加資料夾')
        add_btn.clicked.connect(self._add_folder)
        add_multiple_btn = QPushButton('批次添加')
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
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            '選擇資料夾'
        )
        
        if folder_path:
            if self.folder_list.count() == 0:
                self._load_file_attributes(folder_path)
            self.folder_list.addItem(QListWidgetItem(folder_path))

    def _add_multiple_folders(self) -> None:
        """批次添加多個資料夾"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        
        # Use the non-native dialog to enable multi-selection features
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        listview = dialog.findChild(QListView)
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

    def _on_folder_changed(self, folder_name: str) -> None:
        """處理資料夾選擇變更"""
        if folder_name and hasattr(self, 'folder_path_map') and folder_name in self.folder_path_map:
            self.current_folder = self.folder_path_map[folder_name]
            self._update_all_tables()

    def _setup_parameters_section(self) -> None:
        """設定參數輸入區"""
        params_layout = QVBoxLayout()
        
        params_title = QLabel('參數設定')
        params_title.setStyleSheet('font-weight: bold; font-size: 14px;')
        params_layout.addWidget(params_title)
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
        
        analyze_btn = QPushButton('開始分析')
        analyze_btn.clicked.connect(self._analyze_data)
        analyze_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #45a049; }")
        
        self.save_btn = QPushButton('儲存結果')
        self.save_btn.clicked.connect(self._save_results)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("QPushButton { background-color: #008CBA; color: white; padding: 5px; border-radius: 3px; } QPushButton:hover { background-color: #007B9A; } QPushButton:disabled { background-color: #cccccc; }")
        
        button_layout.addWidget(analyze_btn)
        button_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(button_layout)

    def _setup_results_section(self) -> None:
        """Setup the results table section."""
        folder_select_layout = QHBoxLayout()
        folder_select_layout.addWidget(QLabel("選擇資料夾："))
        self.folder_combo = QComboBox()
        self.folder_combo.setMinimumWidth(500)
        self.folder_combo.currentTextChanged.connect(self._on_folder_changed)
        folder_select_layout.addWidget(self.folder_combo)
        folder_select_layout.addStretch()
        self.main_layout.addLayout(folder_select_layout)

        self.results_layout = QHBoxLayout()
        self.result_sections = {}
        for file_type in self.FILE_TYPES:
            group = QGroupBox(f"{file_type} 分析結果")
            layout = QVBoxLayout()
            
            attr_selector = QComboBox()
            attr_selector.currentTextChanged.connect(lambda text, ft=file_type: self._on_attribute_selected(ft, text))
            
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(['區段', '平均值', '標準差', '變異數','穩定度'])
            
            for i in range(5): table.setColumnWidth(i, 75)
            
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(lambda pos, t=table: self._show_context_menu(pos, t))
            
            layout.addWidget(attr_selector)
            layout.addWidget(table)
            group.setLayout(layout)
            
            self.results_layout.addWidget(group)
            self.result_sections[file_type] = {'selector': attr_selector, 'table': table}
        
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
                if not all(os.path.exists(os.path.join(folder, file)) for file in self.FILE_TYPES):
                    logger.warning(f"資料夾 {folder} 未包含所有必要檔案，已跳過")
                    continue

                self.analyzer.set_folder_path(folder)
                self.analyzer.find_activation_time()
                
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
                    'activation_time': self.analyzer.activate_time,
                    'end_time': self.analyzer.end_time,
                    'analysis': folder_results
                }

            if not self.results:
                self._show_warning("警告", "分析未產生任何結果")
                return

            self.folder_combo.clear()
            self.folder_path_map = {}
            sorted_folders = sorted(self.results.keys(), key=os.path.basename)
            for folder in sorted_folders:
                folder_name = os.path.basename(folder)
                self.folder_path_map[folder_name] = folder
                self.folder_combo.addItem(folder_name)
            
            self.current_folder = sorted_folders[0]
            self._update_results_selectors()
            self._update_all_tables()
            self.save_btn.setEnabled(True)
            self._show_info("成功", "分析完成！")
            
        except Exception as e:
            logger.error(f"數據分析時發生錯誤: {e}", exc_info=True)
            self._show_error("分析錯誤", str(e))

    def _update_all_tables(self) -> None:
        """更新所有結果表格"""
        for file_type in self.FILE_TYPES:
            self._update_table(file_type)

    def _update_table(self, file_type: str) -> None:
        """更新特定檔案類型的結果表格"""
        attribute = self.result_sections[file_type]['selector'].currentText()
        if attribute and self.current_folder and self.current_folder in self.results and \
           file_type in self.results[self.current_folder]['analysis'] and \
           attribute in self.results[self.current_folder]['analysis'][file_type]:
            
            table = self.result_sections[file_type]['table']
            results = self.results[self.current_folder]['analysis'][file_type][attribute]
            
            table.setRowCount(0) # Clear table before populating
            
            # Sort sections, ensuring '總區段' is last
            sorted_sections = sorted(results.keys(), key=lambda x: (isinstance(x, str), x))
            
            for section in sorted_sections:
                row_position = table.rowCount()
                table.insertRow(row_position)
                values = results[section]
                sec_name = f"區段 {section}" if section != '總區段' else "總區段"
                table.setItem(row_position, 0, QTableWidgetItem(sec_name))
                table.setItem(row_position, 1, QTableWidgetItem(f"{values['平均值']:.2f}"))
                table.setItem(row_position, 2, QTableWidgetItem(f"{values['標準差']:.2f}"))
                table.setItem(row_position, 3, QTableWidgetItem(f"{values['變異數']:.3f}"))
                table.setItem(row_position, 4, QTableWidgetItem(f"{values['穩定度']:.2f}"))

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

    def _on_attribute_selected(self, file_type: str, attribute: str) -> None:
        """處理結果區的屬性選擇變更"""
        if self.current_folder and self.current_folder in self.results:
            self._update_table(file_type)

    def _show_context_menu(self, pos, table):
        """顯示右鍵選單"""
        menu = QMenu()
        copy_cell_action = menu.addAction("複製當前儲存格")
        copy_row_action = menu.addAction("複製當前行")
        copy_all_action = menu.addAction("複製全部")
        menu.addSeparator()
        show_plot_action = menu.addAction("顯示圖表")
        
        action = menu.exec(table.mapToGlobal(pos))
        
        if action == show_plot_action:
            self._show_plot(table)
        elif action == copy_cell_action: self._copy_cell(table)
        elif action == copy_row_action: self._copy_row(table)
        elif action == copy_all_action: self._copy_all(table)

    def _copy_cell(self, table):
        if table.currentItem():
            QApplication.clipboard().setText(table.currentItem().text())

    def _copy_row(self, table):
        current_row = table.currentRow()
        if current_row >= 0:
            row_data = [table.item(current_row, col).text() for col in range(table.columnCount()) if table.item(current_row, col)]
            QApplication.clipboard().setText('\t'.join(row_data))

    def _copy_all(self, table):
        all_data = []
        for row in range(table.rowCount()):
            row_data = [table.item(row, col).text() for col in range(table.columnCount()) if table.item(row, col)]
            all_data.append('\t'.join(row_data))
        QApplication.clipboard().setText('\n'.join(all_data))
        
    def _show_plot(self, table: QTableWidget) -> None:
        """顯示包含折線圖和Error Bar圖的分頁圖表"""
        try:
            file_type_of_table = next((ft for ft, sec in self.result_sections.items() if sec['table'] == table), None)
            if not file_type_of_table:
                self._show_error("錯誤", "無法確定表格對應的檔案類型。")
                return

            if not self.current_folder or self.current_folder not in self.results:
                self._show_warning("警告", "請先選擇並分析一個有效的資料夾。")
                return

            available_attributes = list(self.file_selectors[file_type_of_table].get_selected_attributes().keys())
            if not available_attributes:
                self._show_warning("提示", f"請先在左側為 {file_type_of_table} 添加要分析的屬性。")
                return

            selection_dialog = AttributeSelectionDialog(available_attributes, self)
            if selection_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            selected_plot_attributes = selection_dialog.get_selected_attributes()
            if not selected_plot_attributes:
                self._show_warning("提示", "未選擇任何屬性進行繪圖。")
                return

            # --- 1. 準備折線圖數據 (來自當前選擇的資料夾) ---
            df_full = pd.read_csv(os.path.join(self.current_folder, file_type_of_table))
            data_to_plot_map = {attr: df_full[attr].values for attr in selected_plot_attributes if attr in df_full.columns}
            
            if not data_to_plot_map:
                self._show_error("錯誤", "選擇的屬性均無法在數據檔案中找到。")
                return

            activation_time_str = self.results[self.current_folder]['activation_time']
            end_time_str = self.results[self.current_folder]['end_time']
            df_full['Time_seconds'] = df_full['Time'].apply(lambda x: sum(float(i) * m for i, m in zip(str(x).split(':'), [3600, 60, 1])))
            activation_sec = sum(float(i) * m for i, m in zip(activation_time_str.split(':'), [3600, 60, 1]))
            end_sec = sum(float(i) * m for i, m in zip(end_time_str.split(':'), [3600, 60, 1]))
            
            start_idx = np.where(df_full['Time_seconds'] >= activation_sec)[0][0]
            end_idx = np.where(df_full['Time_seconds'] <= end_sec)[0][-1]
            representative_section_results = self.results[self.current_folder]['analysis'][file_type_of_table][selected_plot_attributes[0]]

            # --- 2. 準備 Error Bar 圖數據 (來自所有已分析的資料夾) ---
            error_bar_data = {}
            sorted_folder_paths = sorted(self.results.keys(), key=os.path.basename)

            # --- 修改部分: 決定要在Error Bar中繪製哪些屬性 ---
            attributes_for_error_plot = []
            if file_type_of_table == 'RF.csv' and 'Power' in selected_plot_attributes:
                # 如果是 RF.csv 的圖，且使用者有選Power，則Error Bar只畫Power
                attributes_for_error_plot.append('Power')
                logger.info("為 'RF.csv' 產生圖表，Error Bar 圖將僅顯示 'Power'。")
            else:
                # 其他情況 (如 MFC.csv, BgCgTemp.csv)，則顯示所有選擇的屬性
                attributes_for_error_plot = selected_plot_attributes
            # --- 修改結束 ---

            for attr_name in attributes_for_error_plot:
                attr_data_for_error_plot = {'folders': [], 'means': [], 'stds': []}
                for folder_path in sorted_folder_paths:
                    # 使用 os.path.basename 傳遞資料夾名稱給繪圖類
                    folder_name_for_dict = os.path.basename(folder_path)
                    if file_type_of_table in self.results[folder_path]['analysis'] and \
                       attr_name in self.results[folder_path]['analysis'][file_type_of_table] and \
                       '總區段' in self.results[folder_path]['analysis'][file_type_of_table][attr_name]:
                        
                        total_section = self.results[folder_path]['analysis'][file_type_of_table][attr_name]['總區段']
                        attr_data_for_error_plot['folders'].append(folder_name_for_dict)
                        attr_data_for_error_plot['means'].append(total_section['平均值'])
                        attr_data_for_error_plot['stds'].append(total_section['標準差'])

                if attr_data_for_error_plot['folders']:
                    error_bar_data[attr_name] = attr_data_for_error_plot

            # --- 3. 創建並顯示對話框 ---
            dialog = PlotDialog(
                data_to_plot_map, 
                representative_section_results, 
                start_idx, 
                end_idx,
                error_bar_data,
                self
            )
            dialog.exec()

        except Exception as e:
            logger.error(f"顯示圖表時發生錯誤: {e}", exc_info=True)
            self._show_error("圖表顯示錯誤", f"發生未預期的錯誤: {str(e)}")


    def _load_file_attributes(self, folder_path: str) -> None:
        """從指定資料夾載入檔案的欄位屬性"""
        for file_type in self.FILE_TYPES:
            try:
                file_path = os.path.join(folder_path, file_type)
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path, nrows=1) # 只讀第一行來獲取欄位
                    columns = [col for col in df.columns if col != 'Time']
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
            if not base_save_dir:
                return
            
            self.analyzer.output_path = base_save_dir
            self.analyzer.save_results(self.results)
            
            plots_dir = os.path.join(base_save_dir, 'plots_results')
            os.makedirs(plots_dir, exist_ok=True)
            
            # 遍歷所有分析過的資料夾來儲存圖表
            for folder_path, folder_data in self.results.items():
                folder_name = os.path.basename(folder_path)
                folder_plots_dir = os.path.join(plots_dir, folder_name)
                os.makedirs(folder_plots_dir, exist_ok=True)
                
                for file_type, analysis_data in folder_data['analysis'].items():
                    attributes = list(analysis_data.keys())
                    if not attributes: continue

                    df = pd.read_csv(os.path.join(folder_path, file_type))
                    data_to_plot_map = {attr: df[attr].values for attr in attributes if attr in df.columns}
                    if not data_to_plot_map: continue
                    
                    df['Time_seconds'] = df['Time'].apply(lambda x: sum(float(i) * m for i, m in zip(str(x).split(':'), [3600, 60, 1])))
                    act_sec = sum(float(i) * m for i, m in zip(folder_data['activation_time'].split(':'), [3600, 60, 1]))
                    end_sec = sum(float(i) * m for i, m in zip(folder_data['end_time'].split(':'), [3600, 60, 1]))
                    start_idx = np.where(df['Time_seconds'] >= act_sec)[0][0]
                    end_idx = np.where(df['Time_seconds'] <= end_sec)[0][-1]
                    
                    # 創建折線圖
                    plot = AnalysisPlot()
                    plot.plot_data(data_to_plot_map, analysis_data[attributes[0]], start_idx, end_idx)
                    plot_path = os.path.join(folder_plots_dir, f"{file_type[:-4]}_line_plot.png")
                    plot.figure.savefig(plot_path, dpi=300, bbox_inches='tight')
                    plt.close(plot.figure)

            # 創建並儲存比較性的Error Bar圖
            for file_type in self.FILE_TYPES:
                all_attributes = self.file_selectors[file_type].get_selected_attributes().keys()
                if not all_attributes: continue
                
                error_bar_data = {}
                sorted_folders = sorted(self.results.keys(), key=os.path.basename)
                for attr in all_attributes:
                    attr_data = {'folders': [], 'means': [], 'stds': []}
                    for folder in sorted_folders:
                        if file_type in self.results[folder]['analysis'] and attr in self.results[folder]['analysis'][file_type]:
                             total_section = self.results[folder]['analysis'][file_type][attr]['總區段']
                             attr_data['folders'].append(os.path.basename(folder))
                             attr_data['means'].append(total_section['平均值'])
                             attr_data['stds'].append(total_section['標準差'])
                    if attr_data['folders']:
                        error_bar_data[attr] = attr_data
                
                if error_bar_data:
                    err_plot = ErrorBarPlot()
                    err_plot.plot_data(error_bar_data)
                    err_plot_path = os.path.join(plots_dir, f"{file_type[:-4]}_errorbar_comparison.png")
                    err_plot.figure.savefig(err_plot_path, dpi=300, bbox_inches='tight')
                    plt.close(err_plot.figure)

            self._show_info("成功", f"結果和圖表已成功儲存至 '{base_save_dir}'")
            
        except Exception as e:
            logger.error(f"儲存結果時發生錯誤: {e}", exc_info=True)
            self._show_error("儲存錯誤", str(e))

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

def main():
    """GUI 應用程式主入口點"""
    try:
        app = QApplication(sys.argv)
        logger.info("初始化 GUI 介面...")
        window = PlasmaAnalyzerGUI()
        window.show()
        logger.info("啟動 GUI 應用程式...")
        return app.exec()
    except Exception as e:
        logger.critical(f"GUI 應用程式執行錯誤: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())