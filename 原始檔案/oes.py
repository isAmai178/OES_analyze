import os
import pandas as pd
import numpy as np
#產生檔案的名稱
def generate_file_names(base_name, start, end, extension='.txt'):
    """Generate a list of file names based on the base name, start, and end indices."""
    return [f"{base_name}_S{str(i).zfill(4)}{extension}" for i in range(start, end + 1)]

#讀取檔案裏面的波長和強度並用
def read_data(file_path):
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
#把檔案名稱讀取成資料
def read_file_to_data(file_names,base_path):
    all_data = {}
    for file_name in file_names:
        file_path = os.path.join(base_path, file_name)
        data = read_data(file_path)
        for time_point, value in data:
            if time_point not in all_data:
                all_data[time_point] = []
            all_data[time_point].append(value)
    return all_data
#利用最大最小值找出波段並回傳anomalies(list型態)
def detect_anomalies_across_files(all_data, threshold):
    """Detect points where the rate of change across files exceeds the given threshold."""
    anomalies = []
    for time_point in sorted(all_data.keys()):
        values = all_data[time_point]
        rate_of_change = max(values)-min(values)
        if rate_of_change > threshold:
            anomalies.append((time_point, rate_of_change))
    return anomalies
#找出激發的時間點
def detect_activate_time(all_data,max_wave,threshold,start_index):
    time_series=[]
    time_series = all_data[max_wave]
    activated = False
    end_time = None
    #利用後一個時間點比較，如果大於臨界值回傳
    for i in range(len(time_series)-1):
        dif = time_series[i+1] - time_series[i]
        if not activated and dif > threshold:
            acctivate_time = i + 1 + start_index
            activated = True
        elif activated and dif < -(threshold):
            end_time = i + 1 + start_index
            print(dif)
            break
            
    return acctivate_time ,end_time

def data_to_excel(all_data,base_path,base_name):
    output_name=os.path.basename(base_path)
    excel_name=f'{output_name}.xlsx'
    with pd.ExcelWriter(excel_name) as writer:
        threshold = 1000
        #找出最大波段
        detect_wave = 657
        section = 3
        #找出激發時間點
        activate_time , end_time = detect_activate_time(all_data,detect_wave,threshold,start_index)
        activate_time_file = generate_file_names(base_name,activate_time + 10,end_time - 10)
        activate_time_data = read_file_to_data(activate_time_file,base_path)
        print(len(activate_time_data[detect_wave]))
        # 取得特定波長的數據並計算平均值
        wave_data = activate_time_data[detect_wave]
        section_size = len(wave_data) // section  # 計算每段的大小
    
        sectioned_data = {}
        for i in range(section):
            start_idx = i * section_size
            end_idx = start_idx + section_size if i < section - 1 else len(wave_data)
            section_wave_data = wave_data[start_idx:end_idx]
            std_value = np.std(section_wave_data) 
            average_value = sum(section_wave_data) / len(section_wave_data)
            stability = round((std_value / average_value)*100,3)
            # 計算每段的平均值和標準差
            sectioned_data[f'區段{i+1}'] = {
                'mean': average_value,
                'std': std_value,
                '穩定度': stability
            }
        # 創建DataFrame來存儲所有段的結果
        results = []
        for section_name, stats in sectioned_data.items():
            results.append([
                section_name,
                stats['mean'],
                stats['std'],
                stats['穩定度']
            ])
        
        activate_time_df = pd.DataFrame(results, 
                                            columns=['區段', '平均值', '標準差','穩定度'])
        print(activate_time_df)
        # df = pd.DataFrame(activate_time_after_df)
        # df = df.rename(columns={'平均值_x': '激發前平均值', '平均值_y': '激發後平均值'})
        activate_time_df.to_excel(writer,sheet_name=str(threshold),index=False)
# Define the base file name and range
base_path = '電漿光譜/1107H2/電漿0926-500~3000current模式0~6PIV/OES光譜/1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(6)-7'
base_name = 'Spectrum_T2024-09-26-13-55-47'
start_index = 0
end_index = 143

# Generate file names
file_names = generate_file_names(base_name, start_index, end_index)

all_data = read_file_to_data(file_names,base_path)

data_to_excel(all_data,base_path,base_name)
