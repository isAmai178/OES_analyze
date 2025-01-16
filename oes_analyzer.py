import os
import pandas as pd
import numpy as np

class OESAnalyzer:
    def __init__(self):
        self.all_data = {}
        
    def generate_file_names(self, base_name, start, end, extension='.txt'):
        """Generate a list of file names based on the base name, start, and end indices."""
        return [f"{base_name}_S{str(i).zfill(4)}{extension}" for i in range(start, end + 1)]

    def read_data(self, file_path):
        """Read data from a given file and return as a list of lists."""
        with open(file_path, 'r') as file:
            contents = file.readlines()
        
        data = []
        for line in contents:
            if ';' in line:
                parts = line.strip().split(';')
                try:
                    parts = [float(part) for part in parts]
                    data.append(parts)
                except ValueError:
                    continue
        return data

    def read_file_to_data(self, file_names, base_path):
        """Read all files and store data"""
        self.all_data = {}
        for file_name in file_names:
            file_path = os.path.join(base_path, file_name)
            data = self.read_data(file_path)
            for time_point, value in data:
                if time_point not in self.all_data:
                    self.all_data[time_point] = []
                self.all_data[time_point].append(value)
        return self.all_data

    def detect_anomalies_across_files(self, threshold):
        """Detect points where the rate of change across files exceeds the given threshold."""
        anomalies = []
        for time_point in sorted(self.all_data.keys()):
            values = self.all_data[time_point]
            rate_of_change = max(values)-min(values)
            if rate_of_change > threshold:
                anomalies.append((time_point, rate_of_change))
        return anomalies

    def detect_activate_time(self, max_wave, threshold, start_index):
        """Find activation time points"""
        time_series = self.all_data[max_wave]
        activated = False
        end_time = None
        
        for i in range(len(time_series)-1):
            dif = time_series[i+1] - time_series[i]
            if not activated and dif > threshold:
                activate_time = i + 1 + start_index
                activated = True
            elif activated and dif < -(threshold):
                end_time = i + 1 + start_index
                break
                
        return activate_time, end_time

    def analyze_data(self, base_path, base_name, detect_wave=657, threshold=1000, section=3, start_index=0):
        """Analyze data and return results DataFrame"""
        activate_time, end_time = self.detect_activate_time(detect_wave, threshold, start_index)
        activate_time_file = self.generate_file_names(base_name, activate_time + 10, end_time - 10)
        activate_time_data = self.read_file_to_data(activate_time_file, base_path)
        
        wave_data = activate_time_data[detect_wave]
        section_size = len(wave_data) // section
        
        sectioned_data = {}
        for i in range(section):
            start_idx = i * section_size
            end_idx = start_idx + section_size if i < section - 1 else len(wave_data)
            section_wave_data = wave_data[start_idx:end_idx]
            std_value = np.std(section_wave_data) 
            average_value = sum(section_wave_data) / len(section_wave_data)
            stability = round((std_value / average_value)*100, 3)
            
            sectioned_data[f'區段{i+1}'] = {
                'mean': average_value,
                'std': std_value,
                '穩定度': stability
            }

        results = []
        for section_name, stats in sectioned_data.items():
            results.append([
                section_name,
                stats['mean'],
                stats['std'],
                stats['穩定度']
            ])
        
        return pd.DataFrame(results, columns=['區段', '平均值', '標準差', '穩定度'])

    def save_to_excel(self, df, base_path, threshold=1000):
        """Save analysis results to Excel"""
        output_name = os.path.basename(base_path)
        excel_name = f'{output_name}.xlsx'
        with pd.ExcelWriter(excel_name) as writer:
            df.to_excel(writer, sheet_name=str(threshold), index=False) 
def main():
    # 使用示例
    analyzer = OESAnalyzer()

    # 設定基本參數
    base_path = '../電漿光譜/1107H2/電漿0926-500~3000current模式0~6PIV/OES光譜/1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(6)-7'
    base_name = 'Spectrum_T2024-09-26-13-55-47'
    start_index = 0
    end_index = 143

    # 生成檔案名稱並讀取數據
    file_names = analyzer.generate_file_names(base_name, start_index, end_index)
    analyzer.read_file_to_data(file_names, base_path)

    # 分析數據
    results_df = analyzer.analyze_data(base_path, base_name)

    # 儲存結果
    analyzer.save_to_excel(results_df, base_path)
if __name__ == '__main__':
    main()