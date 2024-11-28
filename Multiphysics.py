import os
import pandas as pd
import numpy as np

file_path = '電漿光譜/1107H2/電漿0926-500~3000current模式0~6PIV/1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(6)-7/'
file_name = ''
select_colums = ['Power','Voltage','Current']
df = pd.read_csv(file_path)
df = df[select_colums]
# 找出每個欄位不為 0 的數值

non_zero_values = {col: df[col][df[col] != 0].tolist() for col in df.columns}

# 計算每個欄位的平均值和標準差
means = {col: np.mean(non_zero_values[col]) for col in non_zero_values}
stds = {col: np.std(non_zero_values[col]) for col in non_zero_values}
# 計算穩定度 (標準差/平均值)
stability = {col: (stds[col]/means[col])*100 for col in non_zero_values}

# 創建新的DataFrame來存儲結果
results_df = pd.DataFrame({
    'Power': [means['Power'], stds['Power'], stability['Power']],
    'Voltage': [means['Voltage'], stds['Voltage'], stability['Voltage']],
    'Current': [means['Current'], stds['Current'], stability['Current']]
}, index=['平均值', '標準差', '穩定度'])

# 將結果輸出到Excel檔案
output_path = '.xlsx'
results_df.to_excel(output_path)