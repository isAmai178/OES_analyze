import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QMessageBox
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
        self.setGeometry(100, 100, 600, 400)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        self._setup_file_selection()
        self._setup_parameters_section()
        self._setup_results_section()
        self._setup_actions()

    def _setup_file_selection(self):
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

    def _setup_parameters_section(self):
        """Create parameters input section."""
        params_layout = QHBoxLayout()

        self.detect_wave_spin = QDoubleSpinBox()
        self.detect_wave_spin.setRange(0, 1000)
        self.detect_wave_spin.setValue(657)
        self.detect_wave_spin.setPrefix("波長: ")
        self.detect_wave_spin.setSuffix(" nm")

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setValue(1000)
        self.threshold_spin.setPrefix("閾值: ")
        self.threshold_spin.setSuffix(" a.u.")

        self.section_spin = QSpinBox()
        self.section_spin.setRange(2, 10)
        self.section_spin.setValue(3)
        self.section_spin.setPrefix("分段數: ")

        params_layout.addWidget(self.detect_wave_spin)
        params_layout.addWidget(self.threshold_spin)
        params_layout.addWidget(self.section_spin)

        self.main_layout.addLayout(params_layout)

    def _setup_results_section(self):
        """Create results display section."""
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["區段", "平均值", "標準差", "穩定度"])

        self.main_layout.addWidget(self.results_table)

    def _setup_actions(self):
        """Create action buttons."""
        actions_layout = QHBoxLayout()

        analyze_button = QPushButton("分析")
        analyze_button.clicked.connect(self._analyze_data)

        save_button = QPushButton("儲存結果")
        save_button.clicked.connect(self._save_results)

        actions_layout.addWidget(analyze_button)
        actions_layout.addWidget(save_button)

        self.main_layout.addLayout(actions_layout)

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
                    f"檔案名稱{base_name}"
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
                section_count=section_count
            )

            self._update_results_table(results_df)
            QMessageBox.information(self, "成功", "分析完成！")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def _save_results(self):
        """Save analysis results through the controller."""
        try:
            base_path = self.path_edit.text()
            if not base_path:
                raise ValueError("請選擇資料夾路徑")

            self.controller.save_results_to_excel(base_path, self.threshold_spin.value())
            QMessageBox.information(self, "成功", "結果已儲存！")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def _update_results_table(self, results_df: pd.DataFrame):
        """Update the results table with analysis data."""
        self.results_table.setRowCount(len(results_df))
        for i, row in results_df.iterrows():
            for j, value in enumerate(row):
                self.results_table.setItem(i, j, QTableWidgetItem(str(value)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = OESAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
