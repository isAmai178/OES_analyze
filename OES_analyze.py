import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable

class OESAnalyzer:
    """OES光譜分析器"""
    
    def __init__(self, start_value: float = 195.0):
        self.start_value = start_value
        self.all_values: Dict[float, List[Tuple[str, float]]] = {}
        self.selected_files: List[str] = []
        self.status_callback: Optional[Callable[[str], None]] = None
        
    def set_status_callback(self, callback):
        """設置狀態更新回調函數"""
        self.status_callback = callback
        
    def update_status(self, message: str):
        """更新狀態"""
        if self.status_callback:
            self.status_callback(message)

    def find_peak_points(self, data: Dict[float, List[Tuple[str, float]]]) -> List[dict]:
        """找出每個波段的最高點"""
        peak_points = []
        for value, measurements in data.items():
            measurements_only = [m[1] for m in measurements]
            max_value = max(measurements_only)
            max_index = measurements_only.index(max_value)
            file_name = measurements[max_index][0]
            
            peak_points.append({
                '波段': value,
                '最大值': max_value,
                '檔案名': file_name,
                '時間點': file_name.split('S')[-1].split('.')[0]
            })
        
        # 按最大值排序
        return sorted(peak_points, key=lambda x: x['最大值'], reverse=True)
    
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
    
    def compare_peak_points(self, data1: Dict[float, List[Tuple[str, float]]], 
                       data2: Dict[float, List[Tuple[str, float]]]) -> List[Dict]:
        """比較兩個數據集的峰值點"""
        peaks1 = self.find_peak_points(data1)[:5]  # 取前5高點
        peaks2 = self.find_peak_points(data2)[:5]  # 取前5高點
    
        comparison_results = []
        # 合併所有出現的波段
        all_wavelengths = set([p['波段'] for p in peaks1 + peaks2])
    
        for wavelength in all_wavelengths:
            result = {'波段': wavelength}
        
            # 在第一個數據集中尋找該波段
            peak1 = next((p for p in peaks1 if p['波段'] == wavelength), None)
            if peak1:
                result['數據集1_最大值'] = peak1['最大值']
                result['數據集1_時間點'] = peak1['時間點']
            else:
                result['數據集1_最大值'] = None
                result['數據集1_時間點'] = None
            
            # 在第二個數據集中尋找該波段
            peak2 = next((p for p in peaks2 if p['波段'] == wavelength), None)
            if peak2:
                result['數據集2_最大值'] = peak2['最大值']
                result['數據集2_時間點'] = peak2['時間點']
            else:
                result['數據集2_最大值'] = None
                result['數據集2_時間點'] = None
            
            # 計算差異
            if peak1 and peak2:
                result['差異'] = abs(peak1['最大值'] - peak2['最大值'])
        
            comparison_results.append(result)
    
        # 按差異大小排序（如果有差異的話）
        return sorted(comparison_results, 
                    key=lambda x: x.get('差異', 0) if x.get('差異') is not None else 0, 
                    reverse=True)
    
    def allSpectrum_plot(self, data1, skip_range_nm, output_directory, file_name):
        """繪製全波段圖形並標記出最高波段"""
        try:
            # 找出每個數據集的最大值點
            peaks1 = self.find_peak_points(data1)

            # 取得最大值的波長
            max_peak1 = peaks1[0]  # 已經按最大值排序，所以第一個就是最大的
            sorted_peaks = sorted(peaks1, key=lambda x:x['最大值'], reverse=True)
            # 準備數據
            wavelengths1 = sorted(data1.keys())
            y1 = [max(m[1] for m in data1[w]) for w in wavelengths1]
        
            # 創建圖表
            plt.figure(figsize=(10, 6))

            # 添加最大值波段信息到標題
            title_text = (f'ALL_Spectrum & Higher Peaks \n'
                        f'Max_peak: {max_peak1["波段"]:.1f}nm')
            plt.title(title_text)
            
            # 繪製線條
            plt.plot(wavelengths1, y1, color='red', label='Highest_data', linewidth=1)

            marked_peaks =[]
            for peak in sorted_peaks:
                if len(marked_peaks) >= 3:
                    break
                
                 # 檢查是否需要跳過範圍
                if not any(abs(peak['波段'] - marked_peak['波段']) <= skip_range_nm for marked_peak in marked_peaks):
                    plt.annotate(f'Peak: {peak["波段"]:.1f} nm, intensity: {peak["最大值"]:.1f}',
                                xy=(peak['波段'], peak['最大值']),
                                xytext=(7, 7), textcoords='offset points')
                    marked_peaks.append(peak)
            x_ticks = [peak['波段'] for peak in marked_peaks]
            plt.xticks(ticks=x_ticks, labels=[f'{wavelengths1:.1f}nm' for wavelengths1 in x_ticks], rotation=45)        
            
            # 設置圖表屬性
            plt.xlabel('Wavelength(nm)')
            plt.ylabel('Intensity(Cts)')
            plt.legend()
            #建構檔案名稱
            output_file_name = f"{file_name}_allspectrum_highestPeaks.png"

            # 保存圖表
            output_path = os.path.join(output_directory, output_file_name)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        
            self.update_status(f"已生成最大值比較圖：{output_path}")
            return output_path
        
        except Exception as e:
            self.update_status(f"生成比較圖時發生錯誤: {str(e)}")
            return None

    def analyze_and_export(self, wavebands: List[float], thresholds: List[float], 
                          initial_start: int, initial_end: int, skip_range_nm: float) -> Tuple[str, str]:
        """執行分析並導出結果"""
        try:
            if not self.selected_files:
                raise ValueError("未讀取到檔案進行分析")

            # 收集數據
            self.gather_values()

            # 創建結果資料夾
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_directory = os.path.join(current_dir, "OES光譜分析結果")
            os.makedirs(output_directory, exist_ok=True)
            self.update_status(f"將在以下目錄生成分析結果：{output_directory}")

            # 保存當前分析結果
            self.previous_values = self.all_values.copy()
            self.update_status(f"已保存當前分析結果，包含 {len(self.all_values)} 個波長點")
            experiment_file_name = os.path.splitext(os.path.basename(self.selected_files[0]))[0] #將分析檔案名稱讀取下來
            base_name = experiment_file_name.split('_')[1]  # 取得T2024-09-26

            # 處理特定波段數據
            specific_excel_name = os.path.join(output_directory, f"{base_name}_特定波段解離情況.xlsx")
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
            excel_name = os.path.join(output_directory, f"{base_name}_全部解離波段.xlsx")
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

            self.update_status(f"已將分析寫入 {excel_name} 與 {specific_excel_name}")
            return excel_name, specific_excel_name
        
        except Exception as e:
            self.update_status(f"Analysis failed: {str(e)}")
            raise