import os
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlasmaAnalyzer:
    def __init__(self):
        # 預設設定
        self.folder_path = ''
        self.output_path = '分析結果/'
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
            rf_df = pd.read_csv(os.path.join(self.folder_path, 'RF.csv'))
            time_series = rf_df['Power'].values

            activated = False
            for i, value in enumerate(time_series):
                if not activated and value > self.threshold:
                    self.activate_time = rf_df['Time'].iloc[i]
                    activated = True
                elif activated and value < self.threshold:
                    self.end_time = rf_df['Time'].iloc[i-1]
                    break

            if not activated:
                raise ValueError("無法找到激發時間點")
            if self.end_time is None:
                self.end_time = rf_df['Time'].iloc[-1]

            return self.activate_time, self.end_time

        except Exception as e:
            logger.error(f"尋找激發時間時發生錯誤: {str(e)}")
            raise

    def analyze_data(self):
        """分析所有檔案並計算統計量"""
        try:
            # 先找出激發時間
            self.find_activation_time()
            if self.activate_time is None or self.end_time is None:
                raise ValueError("無法找到有效的激發時間")

            results = {}
            for file_name, columns in self.files_config.items():
                try:
                    file_path = os.path.join(self.folder_path, file_name)
                    if not os.path.exists(file_path):
                        logger.warning(f"找不到檔案: {file_path}")
                        continue

                    df = pd.read_csv(file_path)
                    
                    # 使用Time值篩選資料
                    df_activated = df[(df['Time'] >= self.activate_time) & 
                                    (df['Time'] <= self.end_time)]
                    
                    if df_activated.empty:
                        logger.warning(f"檔案 {file_name} 在指定時間範圍內沒有數據")
                        continue

                    # 創建當前檔案的結果字典
                    file_results = {}
                    # 計算每個欄位的統計量
                    for col in columns:
                        if col not in df_activated.columns:
                            logger.warning(f"找不到欄位 {col} 在檔案 {file_name} 中")
                            continue

                        data = df_activated[col].astype(float)  # 確保數據為數值型態
                        if data.empty:
                            continue

                        mean_val = data.mean()
                        std_val = data.std()
                        stability = (std_val / mean_val) * 100 if mean_val != 0 else 0
                        
                        file_results[col] = {
                            '平均值': mean_val,
                            '標準差': std_val,
                            '穩定度': round(stability, 3)
                        }
                    
                    if file_results:  # 只有在有結果時才添加到結果字典
                        results[file_name] = file_results

                except Exception as e:
                    logger.error(f"處理檔案 {file_name} 時發生錯誤: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"分析過程中發生錯誤: {str(e)}")
            raise

    def save_results(self, results: dict) -> None:
        """儲存分析結果"""
        try:
            for file_name, file_results in results.items():
                # 為每個檔案創建獨立的DataFrame並儲存
                results_df = pd.DataFrame(file_results)
                output_name = f'{file_name[:-4]}.xlsx'
                full_output_path = os.path.join(self.output_path, output_name)
                
                # 確保輸出目錄存在
                os.makedirs(self.output_path, exist_ok=True)
                
                # 儲存結果
                results_df.to_excel(full_output_path)
                logger.info(f"已儲存結果到: {full_output_path}")

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
        results = analyzer.analyze_data()
        
        # 儲存結果
        logger.info("儲存分析結果...")
        analyzer.save_results(results)
        
        logger.info("分析完成")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"找不到檔案或目錄: {e}")
        return 1
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)