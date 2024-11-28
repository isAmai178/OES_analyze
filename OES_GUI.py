import os
from typing import List, Dict
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QTextEdit, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from OES_analyze import OESAnalyzer  # 引入我們的分析類
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class OESAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analyzer = None  # 稍後初始化
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
        self.create_parameter_settings(layout)
        self.create_waveband_settings(layout)
        self.create_execute_button(layout)
        self.create_peak_display(layout) 
        self.create_status_display(layout)
        self.create_plot_area(layout)  # 新增圖表區域
    
    def create_peak_display(self, parent_layout):
        """創建峰值顯示區域"""
        group = QGroupBox("最高點波段(由大到小)")
        layout = QVBoxLayout()
        
        self.peak_text = QTextEdit()
        self.peak_text.setReadOnly(True)
        self.peak_text.setMaximumHeight(100)  # 限制高度
        layout.addWidget(self.peak_text)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def update_peak_display(self, peak_points: List[Dict]):
        """更新峰值顯示"""
        peak_info = "分析發現的主要峰值點：\n"
        # 只顯示前5個最高點
        for point in peak_points[:5]:
            peak_info += (f"波段: {point['波段']:.1f} nm, "
                         f"最大值: {point['最大值']:.2f}, "
                         f"時間點: {point['時間點']}秒\n")
        self.peak_text.setText(peak_info)
    
    def create_plot_area(self, parent_layout):
        """創建圖表顯示區域"""
        group = QGroupBox("波型圖")
        layout = QVBoxLayout()
        
        # 創建matplotlib圖表
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def plot_spectrum(self, peak_points: List[dict]):
        """繪製光譜圖並標記最高點"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 獲取波長和強度數據
        wavelengths = []
        intensities = []
        for value, measurements in self.analyzer.all_values.items():
            wavelengths.append(value)
            # 使用最後一個測量值
            intensities.append(measurements[-1][1])
        
        # 繪製主要曲線
        ax.plot(wavelengths, intensities, 'b-', label='Spectrum', alpha=0.6)
        
        # 標記前5個最高點
        top_5_peaks = peak_points[:5]
        peak_wavelengths = [p['波段'] for p in top_5_peaks]
        peak_intensities = [p['最大值'] for p in top_5_peaks]
        
        ax.scatter(peak_wavelengths, peak_intensities, color='red', s=100, 
                  marker='o', label='Peak Points')
        
        # 為每個峰值添加標籤
        for i, (wave, intensity) in enumerate(zip(peak_wavelengths, peak_intensities)):
            ax.annotate(f'Peak {i+1}\n{wave:.1f}nm\n{intensity:.1f}',
                       (wave, intensity),
                       xytext=(10, 10),
                       textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                       arrowprops=dict(arrowstyle='->'))
        
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Intensity')
        ax.set_title('Spectrum Analysis with Peak Points')
        ax.grid(True)
        ax.legend()
        
        self.canvas.draw()
    
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
        name_layout = QHBoxLayout()
        self.base_name = QLineEdit("Spectrum_T2024-09-26-13-53-33_S")
        name_layout.addWidget(QLabel("基本檔名:"))
        name_layout.addWidget(self.base_name)
        
        layout.addLayout(folder_layout)
        layout.addLayout(name_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_parameter_settings(self, parent_layout):
        group = QGroupBox("參數設定")
        layout = QVBoxLayout()
        
        # 起始值設定
        start_layout = QHBoxLayout()
        self.start_value = QLineEdit("195.0")
        start_layout.addWidget(QLabel("起始值:"))
        start_layout.addWidget(self.start_value)
        
        # 初始範圍設定
        range_layout = QHBoxLayout()
        self.initial_start = QLineEdit("10")
        self.initial_end = QLineEdit("70")
        range_layout.addWidget(QLabel("初始範圍:"))
        range_layout.addWidget(self.initial_start)
        range_layout.addWidget(QLabel("到"))
        range_layout.addWidget(self.initial_end)
        
        layout.addLayout(start_layout)
        layout.addLayout(range_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_waveband_settings(self, parent_layout):
        group = QGroupBox("波段設定")
        layout = QVBoxLayout()
        
        # 特定波段設定
        self.wavebands = QLineEdit("486.0, 612.0, 656.0, 777.0")
        layout.addWidget(QLabel("特定波段值 (用逗號分隔):"))
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
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            self.folder_path.setText(folder)
            
    def update_status(self, message):
        self.status_text.append(message)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
        
    def execute_analysis(self):
        try:
            # 獲取所有輸入值
            folder_path = self.folder_path.text()
            if not folder_path:
                QMessageBox.warning(self, "警告", "請選擇資料夾路徑")
                return
            
            # 解析輸入值
            base_name = self.base_name.text()
            start_value = float(self.start_value.text())
            initial_start = int(self.initial_start.text())
            initial_end = int(self.initial_end.text())
            wavebands = [float(x.strip()) for x in self.wavebands.text().split(",")]
            thresholds = [float(x.strip()) for x in self.thresholds.text().split(",")]
        
            # 生成文件路徑列表
            file_paths = [
                os.path.join(folder_path, f"{base_name}{i:04d}.txt") 
                for i in range(initial_start, initial_end + 1)
            ]
        
            #  創建分析器實例並設置回調
            self.analyzer = OESAnalyzer(start_value=start_value)
            self.analyzer.set_status_callback(self.update_status)
            self.analyzer.set_files(file_paths)
        
            # 執行分析
            self.update_status("開始分析...")
            excel_file, specific_excel_file = self.analyzer.analyze_and_export(
                wavebands=wavebands,
                thresholds=thresholds,
                initial_start=initial_start,
                initial_end=initial_end
            )
             # 找出並顯示峰值點
            peak_points = self.analyzer.find_peak_points(self.analyzer.all_values)
            self.update_peak_display(peak_points)

            # 繪製波型圖
            self.plot_spectrum(peak_points)
            
            result_message = (
                f"分析完成！結果已保存至：\n"
                f"1. 光譜變化分析：{os.path.basename(excel_file)}\n"
                f"2. 特定波段分析：{os.path.basename(specific_excel_file)}"
            )
            self.update_status(result_message)
            QMessageBox.information(self, "完成", result_message)
        
        except ValueError as e:
            QMessageBox.critical(self, "輸入錯誤", str(e))
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"分析過程發生錯誤: {str(e)}")