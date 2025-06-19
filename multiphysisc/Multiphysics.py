import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 常量定義
TIME_COLUMN = 'Time'
ACTIVATION_FILE = 'RF.csv'
ACTIVATION_COLUMN = 'Power'
DEFAULT_OUTPUT_DIR = '分析結果'
MAX_SHEETNAME_LENGTH = 31

class PlasmaAnalyzer:
    def __init__(self):
        # 預設設定
        self.folder_path = ''
        self.output_path = DEFAULT_OUTPUT_DIR
        self.files_config = {
            'RF.csv': ['Power', 'Voltage', 'Current'],
            'BgCgTemp.csv': ['BG', 'CG'],
            'MFC.csv': ['H2(sccm)']
        }
        self.threshold = 200
        self.activate_time = None
        self.end_time = None

    def set_folder_path(self, path):
        """設定資料夾路徑"""
        self.folder_path = path

    def set_threshold(self, value):
        """設定閾值"""
        self.threshold = value

    def find_activation_time(self):
        """找出激發和結束時間"""
        try:
            rf_df = pd.read_csv(os.path.join(self.folder_path, ACTIVATION_FILE))
            time_series = rf_df[ACTIVATION_COLUMN].values

            # 尋找第一個不為0的值作為激發時間
            activated = False
            for i, value in enumerate(time_series):
                if value != 0 and not activated:
                    self.activate_time = rf_df[TIME_COLUMN].iloc[i]
                    activated = True
                elif activated and value == 0:
                    self.end_time = rf_df[TIME_COLUMN].iloc[i-1]
                    break

            if not activated:
                raise ValueError("找不到激發時間點")
            if self.end_time is None:
                self.end_time = rf_df[TIME_COLUMN].iloc[-1]

        except Exception as e:
            logger.error(f"尋找激發時間時發生錯誤: {str(e)}")
            raise

    def analyze_sections(self, file_name: str, column: str, num_sections: int) -> Dict[str, Dict[str, float]]:
        """
        對指定檔案的特定欄位進行區段分析
        
        Args:
            file_name: CSV檔案名稱
            column: 要分析的欄位名稱
            num_sections: 要分割的區段數
            
        Returns:
            Dict[str, Dict[str, float]]: 各區段的分析結果, 其中 '變異數' 欄位儲存的是變異係數 (CV)
        """
        try:
            # 確保已找到激發時間
            if self.activate_time is None:
                self.find_activation_time()

            # 讀取檔案
            file_path = os.path.join(self.folder_path, file_name)
            df = pd.read_csv(file_path)
            # 篩選有效時間範圍的數據
            mask = (df[TIME_COLUMN] >= self.activate_time) & (df[TIME_COLUMN] <= self.end_time)
            df_activated = df[mask]
            if df_activated.empty:
                raise ValueError(f"在有效時間範圍內找不到數據")

            # 計算全部激發資料的平均值
            total_mean = df_activated[column].mean()

            # 計算每個區段的資料點數
            total_points = len(df_activated)
            points_per_section = total_points // num_sections
            
            # 分析每個區段
            results = {}
            for i in range(num_sections):
                start_idx = i * points_per_section
                end_idx = start_idx + points_per_section if i < num_sections - 1 else None
                
                # 取得區段數據
                section_data = df_activated[column].iloc[start_idx:end_idx]
                
                # 計算統計量
                mean_val = section_data.mean()
                std_val = section_data.std()
                
                # 計算變異係數 (Coefficient of Variation, CV)
                # CV = 標準差 / 整體激發區間的平均值
                coefficient_of_variation = (std_val / total_mean) if total_mean != 0 else 0
                
                # 計算穩定度
                # 穩定度 = (1 - CV) * 100%
                stability = (1 - coefficient_of_variation) * 100
                
                # 儲存結果
                results[i + 1] = {
                    '平均值': mean_val,
                    '標準差': std_val,
                    '變異數': round(coefficient_of_variation, 3), # 此處 '變異數' 實為變異係數 CV
                    '穩定度': round(stability, 3)
                }
            return results
            
        except Exception as e:
            logger.error(f"分析區段時發生錯誤: {str(e)}")
            raise

    def save_results(self, results: Dict[str, Any]) -> None:
        """儲存分析結果（多屬性多sheet，資料夾分塊，資料夾間空兩行）"""
        try:
            os.makedirs(self.output_path, exist_ok=True)
            for file_name in ['RF.csv', 'BgCgTemp.csv', 'MFC.csv']:
                output_name = f'{file_name[:-4]}_analysis.xlsx'
                full_output_path = os.path.join(self.output_path, output_name)

                # 自動收集所有出現過的屬性
                attrs = set()
                for folder_results in results.values():
                    if 'analysis' in folder_results and file_name in folder_results['analysis']:
                        attrs.update(folder_results['analysis'][file_name].keys())
                attrs = list(attrs)
                if not attrs:
                    continue  # 沒有任何屬性就跳過

                wb = Workbook()
                for idx, attr in enumerate(attrs):
                    if idx == 0:
                        ws = wb.active
                        ws.title = attr[:31]
                    else:
                        ws = wb.create_sheet(title=attr[:31])
                    for folder_name, folder_results in results.items():
                        if 'analysis' not in folder_results or file_name not in folder_results['analysis']:
                            continue
                        if attr not in folder_results['analysis'][file_name]:
                            continue
                        section_dict = folder_results['analysis'][file_name][attr]
                        ws.append([os.path.basename(folder_name)])
                        df = pd.DataFrame.from_dict(section_dict, orient='index')
                        # 插入標題
                        ws.append(['區段'] + list(df.columns))
                        # 插入資料
                        for r in dataframe_to_rows(df, index=True, header=False):
                            if r is None or (isinstance(r, list) and r[0] is None):
                                continue
                            ws.append(r)
                        ws.append([])
                        ws.append([])
                wb.save(full_output_path)
                logger.info(f"已儲存分析結果至: {full_output_path}")
        except Exception as e:
            logger.error(f"儲存結果時發生錯誤: {str(e)}")
            raise



def main():
    """
    主程式進入點
    用於測試 PlasmaAnalyzer 的基本功能
    """
    try:
        # 初始化分析器
        analyzer = PlasmaAnalyzer()
        
        # 設定測試參數
        test_folder = '../電漿光譜/1107H2/電漿0926-500~3000current模式0~6PIV/1130926_H2 Plasma_1.5torr_500w_9000sccm_TAP(6)-7/'
        analyzer.set_folder_path(test_folder)
        analyzer.set_threshold(200)
        
        # 執行分析
        logger.info("開始分析數據...")
        
        # 測試區段分析
        results = {}
        for file_name, columns in analyzer.files_config.items():
            file_results = {}
            for column in columns:
                section_results = analyzer.analyze_sections(file_name, column, 3)
                file_results[column] = section_results
            results[file_name] = file_results
        
        # 儲存結果
        logger.info("儲存分析結果...")
        analyzer.save_results(results)
        
        
        
        logger.info("分析完成")
        return 0
        
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)