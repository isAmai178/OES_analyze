import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt
from controller.controller import OESController
import pandas as pd

class OESAnalyzerGUI(QMainWindow):
    """
    Main GUI class for the OES Analyzer application.
    This View interacts with the Controller to display results and handle user input.
    """

    def __init__(self):
        super().__init__()
        self.controller = OESController()
        self.start_index = 0
        self.end_index = 0
        self._init_ui()

    def _init_ui(self):
        """Initialize the GUI layout and components."""
        self.setWindowTitle("OES Analyzer")
        self.setGeometry(100, 100, 425, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self._setup_file_section()
        self._setup_parameters_section()
        self._setup_analysis_section()
        self._setup_results_section()

    def _setup_file_section(self):
        """Create file selection section."""
        file_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("選擇資料夾路徑...")

        browse_button = QPushButton("瀏覽")
        browse_button.clicked.connect(self._browse_folder)

        file_layout.addWidget(QLabel("資料夾路徑:"))
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_button)

        self.main_layout.addLayout(file_layout)
        self.file_info_label = QLabel()
        self.main_layout.addWidget(self.file_info_label)
        
    def _setup_parameters_section(self):
        """Create parameters input section."""
        params_layout = QVBoxLayout()

        # Title
        params_title = QLabel('參數設定')
        params_title.setStyleSheet('font-weight: bold; font-size: 14px;')
        params_layout.addWidget(params_title)
        
        # Parameters grid
        params_grid = QHBoxLayout()
        params_grid.setSpacing(20)
        
        #Wave detection
        wave_layout = QVBoxLayout()
        wave_label = QLabel('檢測波長:')
        self.detect_wave_spin = QDoubleSpinBox()
        self.detect_wave_spin.setRange(0, 1000)
        self.detect_wave_spin.setValue(657)
        self.detect_wave_spin.setFixedWidth(125)
        self.detect_wave_spin.setSuffix(" nm")
        wave_layout.addWidget(wave_label)
        wave_layout.addWidget(self.detect_wave_spin)
        params_grid.addLayout(wave_layout)
        
        # Threshold
        threshold_layout = QVBoxLayout()
        threshold_label = QLabel('光譜強度:')
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setValue(1000)
        self.threshold_spin.setSuffix(" a.u.")
        self.threshold_spin.setFixedWidth(125)
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        params_grid.addLayout(threshold_layout)
        
        # Section count
        section_layout = QVBoxLayout()
        section_label = QLabel('解離區段數:')
        self.section_spin = QSpinBox()
        self.section_spin.setRange(2, 10)
        self.section_spin.setValue(3)
        self.section_spin.setFixedWidth(125)
        section_layout.addWidget(section_label)
        section_layout.addWidget(self.section_spin)
        params_grid.addLayout(section_layout)

        params_layout.addLayout(params_grid)
        self.main_layout.addLayout(params_layout)

    def _setup_results_section(self):
        """Create results display section."""
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["區段", "平均值", "標準差", "穩定度"])
        self.main_layout.addWidget(self.results_table)
        # 啟用右鍵選單
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_context_menu)
        save_btn = QPushButton('儲存結果')
        save_btn.clicked.connect(self._save_results)
        self.main_layout.addWidget(save_btn)
    def _setup_analysis_section(self):
        """Setup the analysis button section."""
        analyze_button = QPushButton("分析")
        analyze_button.clicked.connect(self._analyze_data)
        analyze_button.setStyleSheet("""
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

        self.main_layout.addWidget(analyze_button)

    def _browse_folder(self):
        """Handle folder browsing action."""
        folder_path = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder_path:
            self.path_edit.setText(folder_path)

            # 自動掃描 start_index 和 end_index
            try:
                base_name, start_index, end_index = self.controller.scan_file_indices(folder_path)
                self.start_index = start_index
                self.end_index = end_index
                self.base_name = base_name

                QMessageBox.information(
                    self,
                    "成功",
                    f"檢測到檔案範圍：起始索引 {start_index}, 結束索引 {end_index}"
                )

            except Exception as e:
                QMessageBox.critical(self, "錯誤", str(e))

    def _analyze_data(self):
        """Trigger analysis through the controller."""
        try:
            base_path = self.path_edit.text()
            if not base_path:
                raise ValueError("請選擇資料夾路徑")

            detect_wave = self.detect_wave_spin.value()
            threshold = self.threshold_spin.value()
            section_count = self.section_spin.value()

            self.controller.load_and_process_data(
                base_path=base_path,
                base_name= self.base_name,
                start_index=self.start_index,
                end_index=self.end_index
            )

            results_df = self.controller.analyze_data(
                detect_wave=detect_wave,
                threshold=threshold,
                section_count=section_count,
                base_name=self.base_name,
                base_path=base_path,
                start_index= self.start_index
            )

            self._update_results_table(results_df)
            QMessageBox.information(self, "成功", "分析完成！")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def _save_results(self):
        """Save analysis results through the controller."""
        try:
            # 新增選擇儲存目錄的對話框
            save_dir = QFileDialog.getExistingDirectory(self, '選擇儲存位置')
            if not save_dir:
                raise ValueError("請選擇資料夾路徑")        

            self.controller.save_results_to_excel(save_dir, self.threshold_spin.value(),self.base_name)
            QMessageBox.information(self, "成功", "結果已儲存！")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def _update_results_table(self, results_df: pd.DataFrame):
        """Update the results table with analysis data."""
        self.results_table.setRowCount(len(results_df))
        for i, row in results_df.iterrows():
            for j, value in enumerate(row):
                self.results_table.setItem(i, j, QTableWidgetItem(str(value)))
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        menu = QMenu()
        copy_cell_action = menu.addAction("複製當前儲存格")
        copy_row_action = menu.addAction("複製當前行")
        copy_all_action = menu.addAction("複製全部")
        
        action = menu.exec(self.results_table.mapToGlobal(pos))
        
        if action == copy_cell_action:
            self._copy_cell()
        elif action == copy_row_action:
            self._copy_row()
        elif action == copy_all_action:
            self._copy_all()
    def _copy_cell(self):
        """複製選中儲存格"""
        if self.results_table.currentItem() is not None:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.results_table.currentItem().text())
            QMessageBox.information(self, "複製成功", "已複製選中儲存格內容")

    def _copy_row(self):
        """複製整行"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(current_row, col)
                if item is not None:
                    row_data.append(item.text())
            
            clipboard = QApplication.clipboard()
            clipboard.setText('\t'.join(row_data))
            QMessageBox.information(self, "複製成功", "已複製整行內容")

    def _copy_all(self):
        """複製全部內容"""
        all_data = []
        # 添加表頭
        headers = []
        for col in range(self.results_table.columnCount()):
            headers.append(self.results_table.horizontalHeaderItem(col).text())
        all_data.append('\t'.join(headers))
        
        # 添加數據
        for row in range(self.results_table.rowCount()):
            row_data = []
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
            all_data.append('\t'.join(row_data))
        
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(all_data))
        QMessageBox.information(self, "複製成功", "已複製全部內容")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = OESAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
