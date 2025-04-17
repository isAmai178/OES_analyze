import os
from typing import List, Dict
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QTextEdit, QGroupBox, QMessageBox,QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGridLayout
from OES_analyze import OESAnalyzer  # 引入我們的分析類

class OESAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
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
        name_layout = QHBoxLayout()
        self.base_name = QLineEdit("Spectrum_T2024-09-26-13-53-33_S")
        name_layout.addWidget(QLabel("基本檔名:"))
        name_layout.addWidget(self.base_name)
        
        layout.addLayout(folder_layout)
        layout.addLayout(name_layout)
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
        # 點下按鈕會開始執行分析
        try:
            # 獲取所有輸入值
            folder_path = self.folder_path.text()
            if not folder_path:
                QMessageBox.warning(self, "警告", "請選擇資料夾路徑")
                return
            
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
            print(file_paths)
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
            )
            
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
            
        except ValueError as e:
            QMessageBox.critical(self, "輸入錯誤", str(e))
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"分析過程發生錯誤: {str(e)}")