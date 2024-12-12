import os
import pandas as pd
from typing import List, Dict, Tuple, Optional

class FileReader:
    """處理文件讀取的類別"""
    def __init__(self, start_value: float = 195.0):
        self.start_value = start_value

    def read_single_file(self, file_path: str) -> Dict[float, float]:
        """讀取單個文件中的value和測量值"""
        values = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split(';')
                    if len(parts) > 1:
                        try:
                            value = float(parts[0])
                            if value >= self.start_value:
                                values[value] = float(parts[1])
                        except ValueError:
                            print(f"Skipping line due to ValueError: {line.strip()}")
        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return values

class DataAnalyzer:
    """處理數據分析的類別"""
    def __init__(self, file_reader: FileReader):
        self.file_reader = file_reader
        self.all_values = {}

    def gather_values(self, file_paths: List[str]) -> Dict:
        """收集所有文件的數據"""
        self.all_values = {}
        for file_path in file_paths:
            file_values = self.file_reader.read_single_file(file_path)
            if not file_values:
                print(f"No valid data found in {file_path}")
                continue
            for value, measurement in file_values.items():
                if value not in self.all_values:
                    self.all_values[value] = []
                self.all_values[value].append((os.path.basename(file_path), measurement))
        return self.all_values

    def find_specific_wavebands_differences(self, wavebands: List[float], threshold: float = 200) -> Dict:
        """分析特定波段的差異"""
        specific_differences = {}
        for value, measurements in self.all_values.items():
            if value in wavebands:
                measurements_only = [m[1] for m in measurements]
                min_measurement = min(measurements_only)
                max_measurement = max(measurements_only)
                if abs(max_measurement - min_measurement) > threshold:
                    largest_diff = max(measurements, key=lambda x: abs(x[1] - min_measurement))
                    filename = largest_diff[0]
                    file_second = filename.split('S')[-1].split('.')[0]
                    specific_differences[value] = (min_measurement, max_measurement, largest_diff, file_second)
        return specific_differences

    def find_significant_differences(self, threshold: float = 200) -> Dict:
        """分析所有波段的顯著差異"""
        significant_differences = {}
        for value, measurements in self.all_values.items():
            measurements_only = [m[1] for m in measurements]
            min_measurement = min(measurements_only)
            max_measurement = max(measurements_only)
            if abs(max_measurement - min_measurement) > threshold:
                largest_diff = max(measurements, key=lambda x: abs(x[1] - min_measurement))
                significant_differences[value] = (min_measurement, max_measurement, largest_diff)
        return significant_differences

class DataExporter:
    """處理數據導出的類別"""
    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        self.excel_name = f"{output_directory}_spectral_dissociations.xlsx"
        self.specific_excel_name = f"{output_directory}_specific_wavebands.xlsx"

    def export_data(self, specific_data: List[Dict], significant_data: List[Dict], threshold: float):
        """導出數據到Excel文件"""
        # 導出特定波段數據
        with pd.ExcelWriter(self.specific_excel_name) as writer:
            df = pd.DataFrame(specific_data)
            df.to_excel(writer, sheet_name=f"threshold_{threshold}", index=False)

        # 導出顯著差異數據
        with pd.ExcelWriter(self.excel_name) as writer:
            df = pd.DataFrame(significant_data)
            df.to_excel(writer, sheet_name=f"threshold_{threshold}", index=False)

class OESAnalysis:
    """主要分析類別"""
    def __init__(self, relative_directory: str, base_name: str, 
                 start_value: float = 195.0):
        self.relative_directory = relative_directory
        self.base_name = base_name
        self.file_reader = FileReader(start_value)
        self.data_analyzer = DataAnalyzer(self.file_reader)
        self.data_exporter = DataExporter(os.path.basename(relative_directory))

    def generate_file_paths(self, start_index: int, end_index: int) -> List[str]:
        """生成文件路徑列表"""
        return [os.path.join(self.relative_directory, 
                f"{self.base_name}{i:04d}.txt") 
                for i in range(start_index, end_index + 1)]

    def run_analysis(self, wavebands: List[float], thresholds: List[float], 
                    initial_start: int = 10, initial_end: int = 70):
        """執行完整分析流程"""
        # 生成初始文件路徑
        initial_file_paths = self.generate_file_paths(initial_start, initial_end)
        
        # 收集數據
        self.data_analyzer.gather_values(initial_file_paths)

        for threshold in thresholds:
            # 分析特定波段
            specific_differences = self.data_analyzer.find_specific_wavebands_differences(
                wavebands, threshold)

            if specific_differences:
                # 處理數據並導出
                source_seconds = [int(data[3]) for data in specific_differences.values()]
                min_source_second = min(source_seconds)

                # 計算新範圍
                min_second = max(0, min_source_second - 20)
                max_second = min_source_second + 20

                # 重新分析新範圍的數據
                new_file_paths = self.generate_file_paths(min_second, max_second)
                self.data_analyzer.gather_values(new_file_paths)
                significant_differences = self.data_analyzer.find_significant_differences(threshold)

                # 準備導出數據
                specific_data = self._prepare_specific_data(specific_differences)
                significant_data = self._prepare_significant_data(significant_differences)

                # 導出數據
                self.data_exporter.export_data(specific_data, significant_data, threshold)

    def _prepare_specific_data(self, specific_differences: Dict) -> List[Dict]:
        """準備特定波段的數據"""
        return [{
            '波段': value,
            '最小值': data[0],
            '最大值': data[1],
            '變化量': data[1] - data[0]
        } for value, data in sorted(specific_differences.items())]

    def _prepare_significant_data(self, significant_differences: Dict) -> List[Dict]:
        """準備顯著差異的數據"""
        return [{
            '波段': value,
            '最小值': data[0],
            '最大值': data[1],
            '變化量': data[1] - data[0]
        } for value, data in sorted(significant_differences.items())]

if __name__ == "__main__":
    # 設定參數
    RELATIVE_DIRECTORY = r'..\電漿光譜\1107H2\電漿0926-500~3000current模式0~6PIV\OES光譜\1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(5)-6'
    BASE_NAME = "Spectrum_T2024-09-26-13-53-33_S"
    START_VALUE = 195.0
    WAVEBANDS = [486.0, 612.0, 656.0, 777.0]
    THRESHOLDS = [250, 350, 450, 550]

    # 創建分析實例並執行
    analyzer = OESAnalysis(RELATIVE_DIRECTORY, BASE_NAME, START_VALUE)
    analyzer.run_analysis(WAVEBANDS, THRESHOLDS)