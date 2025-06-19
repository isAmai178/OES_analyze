from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QListWidget, QListWidgetItem, QTabWidget, QWidget
from PyQt6.QtCore import Qt
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import logging
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

class AttributeSelectionDialog(QDialog):
    """對話框用於選擇要繪製的多個特徵屬性"""
    def __init__(self, attributes: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("選擇要顯示的特徵屬性")
        self.selected_attributes: List[str] = []
        self._init_ui(attributes)

    def _init_ui(self, attributes: List[str]) -> None:
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for attr in attributes:
            item = QListWidgetItem(attr)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # 預設選中第一個屬性
            if not self.selected_attributes and attributes:
                 item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _on_accept(self) -> None:
        self.selected_attributes = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_attributes.append(item.text())
        self.accept()

    def get_selected_attributes(self) -> List[str]:
        return self.selected_attributes

class AnalysisPlot(QWidget):
    """用於顯示時間序列折線圖的組件"""
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

    def plot_data(self, data_map: Dict[str, np.ndarray], representative_results: Dict, activate_time_idx: int, end_time_idx: int):
        """繪製多個屬性的數據和區段分析圖"""
        try:
            self.ax.clear()
            
            if not data_map:
                logger.warning("No data provided to plot.")
                self.canvas.draw()
                return

            first_attr_data = next(iter(data_map.values()))
            x = np.arange(len(first_attr_data))
            
            num_lines = len(data_map)
            colors = plt.cm.get_cmap('tab10', num_lines if num_lines > 0 else 1)

            for i, (attr_name, data_values) in enumerate(data_map.items()):
                self.ax.plot(x, data_values, color=colors(i % colors.N), linewidth=1, label=attr_name)
            
            start_idx = activate_time_idx
            end_idx = end_time_idx
            
            sections = [key for key in representative_results.keys() if key != '總區段']
            
            if sections and start_idx < end_idx :
                active_duration = end_idx - start_idx
                points_per_section = active_duration // len(sections)

                if points_per_section > 0:
                    for i in range(len(sections)):
                        section_start = start_idx + i * points_per_section
                        if i > 0:
                            self.ax.axvline(x=section_start, color='r', linestyle='-', alpha=0.5)
                        
                        if i == len(sections) - 1:
                            section_center = (section_start + end_idx) / 2
                        else:
                            section_center = (section_start + (start_idx + (i + 1) * points_per_section)) / 2
                        
                        all_data_concatenated = np.concatenate([d for d in data_map.values() if d is not None and len(d)>0])
                        if len(all_data_concatenated) > 0:
                            max_val = np.max(all_data_concatenated)
                            min_val = np.min(all_data_concatenated)
                            y_pos = max_val + (max_val - min_val) * 0.05 if max_val > min_val else max_val + 0.05 * abs(max_val) if max_val != 0 else 0.05
                        else:
                            y_pos = 0.05
                            
                        self.ax.text(section_center, y_pos, f'區段{i+1}', horizontalalignment='center', verticalalignment='bottom')
                else:
                    logger.warning(f"Points per section is not positive ({points_per_section}), cannot draw section lines accurately.")

            self.ax.set_xlabel('時間 (資料點)')
            self.ax.set_ylabel('數值')
            self.ax.grid(True)
            self.ax.legend()
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error in plot_data: {e}")
            raise

class ErrorBarPlot(QWidget):
    """用於顯示 Error Bar 圖的組件"""
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

    def plot_data(self, error_bar_data: Dict[str, Dict[str, Any]]):
        """繪製 Error Bar 圖，並自動縮短標籤"""
        self.ax.clear()
        
        if not error_bar_data:
            self.ax.text(0.5, 0.5, "沒有可用於比較的數據\n(可能未選擇'Power'屬性或少於2個資料夾)", ha='center', va='center')
            self.canvas.draw()
            return
        
        num_attributes = len(error_bar_data)
        first_attr_data = next(iter(error_bar_data.values()))
        num_folders = len(first_attr_data['folders'])
        x_indices = np.arange(num_folders)
        
        # 動態調整寬度以避免重疊
        width = 0.8 / num_attributes

        for i, (attr_name, data) in enumerate(error_bar_data.items()):
            # 計算每個屬性的偏移量
            offset = (i - (num_attributes - 1) / 2) * (width / num_attributes) * 0.8
            self.ax.errorbar(x_indices + offset, data['means'], yerr=data['stds'], fmt='o', capsize=5, label=attr_name)

        # --- 修改部分：縮短X軸標籤 ---
        original_labels = first_attr_data['folders']
        shortened_labels = []
        for label in original_labels:
            if "TAP(" in label:
                # 找到 "TAP(" 最後出現的位置並截取之後的字串
                start_index = label.rfind("TAP(")
                shortened_labels.append(label[start_index:])
            else:
                # 備用方案：如果找不到特定模式，則取最後25個字符
                shortened_labels.append(label[-25:] if len(label) > 25 else label)
        
        self.ax.set_xticks(x_indices)
        self.ax.set_xticklabels(shortened_labels, rotation=45, ha="right")
        # --- 修改結束 ---
        
        self.ax.set_xlabel('資料夾')
        self.ax.set_ylabel('數值')
        self.ax.set_title('各資料夾平均值 ± 標準差')
        self.ax.legend()
        self.ax.grid(True, axis='y')
        self.figure.tight_layout()
        self.canvas.draw()

class PlotDialog(QDialog):
    """顯示分析圖表的對話框，包含多個分頁"""
    def __init__(self, 
                 line_plot_data_map: Dict[str, np.ndarray], 
                 representative_results: Dict, 
                 activate_time_idx: int, 
                 end_time_idx: int,
                 error_bar_data: Dict[str, Dict[str, Any]],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("分析圖表")
        self.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout()
        
        # 創建 Tab 組件
        tab_widget = QTabWidget()

        # 分頁一: 折線圖
        self.line_plot_widget = AnalysisPlot()
        self.line_plot_widget.plot_data(line_plot_data_map, representative_results, activate_time_idx, end_time_idx)
        tab_widget.addTab(self.line_plot_widget, "摺線圖")

        # 分頁二: Error Bar 圖
        self.error_bar_widget = ErrorBarPlot()
        self.error_bar_widget.plot_data(error_bar_data)
        tab_widget.addTab(self.error_bar_widget, "Error Bar 圖")
        
        layout.addWidget(tab_widget)
        
        # 添加關閉按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)