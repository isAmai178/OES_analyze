import os
import pandas as pd
from typing import List, Dict, Tuple

class OESAnalyzer:
    """OES光譜分析器"""
    
    def __init__(self, start_value: float = 195.0):
        self.start_value = start_value
        self.all_values = {}
        self.selected_files = []
        self.status_callback = None
        
    def set_status_callback(self, callback):
        """設置狀態更新回調函數"""
        self.status_callback = callback
        
    def update_status(self, message: str):
        """更新狀態"""
        if self.status_callback:
            self.status_callback(message)

    def set_files(self, file_paths: List[str]):
        """設置要分析的文件列表"""
        self.selected_files = file_paths

    def read_values_by_line(self, file_path: str) -> Dict[float, float]:
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
                            self.update_status(f"Skipping line due to ValueError: {line.strip()}")
        except FileNotFoundError:
            self.update_status(f"The file at {file_path} was not found.")
        except Exception as e:
            self.update_status(f"An error occurred: {e}")
        return values

    def gather_values(self) -> Dict:
        """收集所有文件的數據"""
        self.all_values = {}
        for file_path in self.selected_files:
            file_values = self.read_values_by_line(file_path)
            if not file_values:
                self.update_status(f"No valid data found in {file_path}")
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

    def extend_range(self, current_index: int, range_size: int = 10) -> List[str]:
        """計算前後range_size個文件的範圍"""
        start_index = max(0, current_index - range_size)
        end_index = min(len(self.selected_files) - 1, current_index + range_size)
        return self.selected_files[start_index:end_index + 1]

    def analyze_and_export(self, wavebands: List[float], thresholds: List[float], 
                          initial_start: int, initial_end: int) -> Tuple[str, str]:
        """執行分析並導出結果"""
        try:
            if not self.selected_files:
                raise ValueError("No files selected for analysis")

            # 收集數據
            self.gather_values()
            
            # 準備Excel輸出
            output_directory = os.path.basename(os.path.dirname(self.selected_files[0]))
            excel_name = f"{output_directory}_spectral_dissociations.xlsx"
            specific_excel_name = f"{output_directory}_specific_wavebands.xlsx"

            # 處理特定波段數據
            with pd.ExcelWriter(specific_excel_name) as specific_writer:
                for threshold in thresholds:
                    specific_differences = self.find_specific_wavebands_differences(wavebands, threshold)
                    if specific_differences:
                        specific_data = []
                        for value, (min_measurement, max_measurement, largest_diff, _) in sorted(specific_differences.items()):
                            specific_data.append({
                                '波段': value,
                                '最小值': min_measurement,
                                '最大值': max_measurement,
                                '差值': max_measurement - min_measurement
                            })
                        specific_df = pd.DataFrame(specific_data)
                        specific_df.to_excel(specific_writer, sheet_name=f"threshold_{threshold}", index=False)

            # 處理所有波段數據
            with pd.ExcelWriter(excel_name) as writer:
                for threshold in thresholds:
                    significant_differences = self.find_significant_differences(threshold)
                    if significant_differences:
                        data = []
                        for value, (min_measurement, max_measurement, largest_diff) in sorted(significant_differences.items()):
                            data.append({
                                '波段': value,
                                '最小值': min_measurement,
                                '最大值': max_measurement,
                                '差值': max_measurement - min_measurement
                            })
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=f"threshold_{threshold}", index=False)

            self.update_status(f"Data written to {excel_name} and {specific_excel_name}")
            return excel_name, specific_excel_name

        except Exception as e:
            self.update_status(f"Analysis failed: {str(e)}")
            raise