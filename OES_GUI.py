import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QSpinBox,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from oes_analyzer import OESAnalyzer

class OESAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analyzer = OESAnalyzer()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('OES Analyzer')
        self.setGeometry(100, 100, 800, 600)

        # 創建主要widget和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 檔案選擇區域
        file_group = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText('選擇資料夾路徑...')
        browse_btn = QPushButton('瀏覽')
        browse_btn.clicked.connect(self.browse_folder)
        file_group.addWidget(QLabel('資料夾路徑:'))
        file_group.addWidget(self.path_edit)
        file_group.addWidget(browse_btn)
        layout.addLayout(file_group)

        # 基本名稱輸入
        name_layout = QHBoxLayout()
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setPlaceholderText('輸入基本檔名...')
        name_layout.addWidget(QLabel('基本檔名:'))
        name_layout.addWidget(self.base_name_edit)
        layout.addLayout(name_layout)

        # 參數設定區域
        params_layout = QHBoxLayout()
        
        # 起始索引
        self.start_index_spin = QSpinBox()
        self.start_index_spin.setRange(0, 9999)
        params_layout.addWidget(QLabel('起始索引:'))
        params_layout.addWidget(self.start_index_spin)

        # 結束索引
        self.end_index_spin = QSpinBox()
        self.end_index_spin.setRange(0, 9999)
        self.end_index_spin.setValue(143)
        params_layout.addWidget(QLabel('結束索引:'))
        params_layout.addWidget(self.end_index_spin)

        # 檢測波長
        self.detect_wave_spin = QSpinBox()
        self.detect_wave_spin.setRange(0, 1000)
        self.detect_wave_spin.setValue(657)
        params_layout.addWidget(QLabel('檢測波長:'))
        params_layout.addWidget(self.detect_wave_spin)

        # 閾值
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setValue(1000)
        params_layout.addWidget(QLabel('閾值:'))
        params_layout.addWidget(self.threshold_spin)

        # 區段數
        self.section_spin = QSpinBox()
        self.section_spin.setRange(1, 10)
        self.section_spin.setValue(3)
        params_layout.addWidget(QLabel('區段數:'))
        params_layout.addWidget(self.section_spin)

        layout.addLayout(params_layout)

        # 分析按鈕
        analyze_btn = QPushButton('開始分析')
        analyze_btn.clicked.connect(self.analyze_data)
        layout.addWidget(analyze_btn)

        # 結果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(['區段', '平均值', '標準差', '穩定度'])
        layout.addWidget(self.result_table)

        # 儲存按鈕
        save_btn = QPushButton('儲存結果')
        save_btn.clicked.connect(self.save_results)
        layout.addWidget(save_btn)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '選擇資料夾')
        if folder_path:
            self.path_edit.setText(folder_path)

    def analyze_data(self):
        try:
            base_path = self.path_edit.text()
            base_name = self.base_name_edit.text()
            
            if not base_path or not base_name:
                QMessageBox.warning(self, '警告', '請填寫資料夾路徑和基本檔名')
                return

            # 生成檔案名稱並讀取數據
            file_names = self.analyzer.generate_file_names(
                base_name,
                self.start_index_spin.value(),
                self.end_index_spin.value()
            )
            self.analyzer.read_file_to_data(file_names, base_path)

            # 分析數據
            results_df = self.analyzer.analyze_data(
                base_path,
                base_name,
                detect_wave=self.detect_wave_spin.value(),
                threshold=self.threshold_spin.value(),
                section=self.section_spin.value(),
                start_index=self.start_index_spin.value()
            )

            # 更新表格
            self.update_table(results_df)
            
            QMessageBox.information(self, '成功', '分析完成！')
            
        except Exception as e:
            QMessageBox.critical(self, '錯誤', f'分析過程中發生錯誤：{str(e)}')

    def update_table(self, df):
        self.result_table.setRowCount(len(df))
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.result_table.setItem(i, j, item)

    def save_results(self):
        try:
            base_path = self.path_edit.text()
            if not base_path:
                QMessageBox.warning(self, '警告', '請先選擇資料夾路徑')
                return

            # 從表格創建DataFrame
            data = []
            for row in range(self.result_table.rowCount()):
                row_data = []
                for col in range(self.result_table.columnCount()):
                    item = self.result_table.item(row, col)
                    row_data.append(item.text() if item else '')
                data.append(row_data)

            df = pd.DataFrame(data, columns=['區段', '平均值', '標準差', '穩定度'])
            
            # 儲存到Excel
            self.analyzer.save_to_excel(df, base_path, self.threshold_spin.value())
            QMessageBox.information(self, '成功', '結果已成功儲存！')
            
        except Exception as e:
            QMessageBox.critical(self, '錯誤', f'儲存過程中發生錯誤：{str(e)}')

def main():
    app = QApplication(sys.argv)
    gui = OESAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 