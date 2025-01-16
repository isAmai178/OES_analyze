import os
import pandas as pd
import numpy as np

# 設定資料夾路徑
folder_path = '../電漿光譜/1107H2/電漿0926-500~3000current模式0~6PIV/\
1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(6)-7/'
output_path = '分析結果/'
# 定義要分析的檔案和對應的欄位
files_config = {
    'RF.csv': ['Power', 'Voltage', 'Current'],
    'BgCgTemp.csv': ['BG', 'CG'],
    'MFC.csv': ['H2(sccm)']
}
threshold = 200  # Power的臨界值

# 讀取RF檔案並找出激發時間
rf_df = pd.read_csv(os.path.join(folder_path, 'RF.csv'))
time_series = rf_df['Power'].values


# 找出激發和結束時間
activated = False
activate_time = None
end_time = None
for i, value in enumerate(time_series):
    if not activated and value > threshold:
        activate_time = rf_df['Time'].iloc[i]  # 使用實際的Time值
        activated = True
    elif activated and value < threshold:
        end_time = rf_df['Time'].iloc[i-1]  # 使用實際的Time值
        break

print(f"激發時間: {activate_time}, 結束時間: {end_time}")

# 讀取所有檔案並計算統計量
results = {}
for file_name, columns in files_config.items():
    df = pd.read_csv(os.path.join(folder_path, file_name))
    
    # 使用Time值篩選資料
    df_activated = df[(df['Time'] >= activate_time) & (df['Time'] <= end_time)]
    print(df_activated)
    # 創建當前檔案的結果字典
    file_results = {}
    # 計算每個欄位的統計量
    for col in columns:
        data = df_activated[col]
        mean_val = np.mean(data)
        std_val = np.std(data)
        stability = (std_val / mean_val) * 100
        
        file_results[col] = {
            '平均值': mean_val,
            '標準差': std_val,
            '穩定度': round(stability, 3)
        }
    
    # 為每個檔案創建獨立的DataFrame並儲存
    results_df = pd.DataFrame(file_results)
    output_name = f'{file_name[:-4]}.xlsx'
    # 使用os.path.join組合完整的輸出路徑
    full_output_path = os.path.join(output_path, output_name)
    results_df.to_excel(full_output_path)
    print(f"已儲存 {output_name}")
