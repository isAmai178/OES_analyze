#!/usr/bin/env python3
"""
OES (Optical Emission Spectroscopy) Data Analyzer

This module provides functionality for analyzing OES data files, including
data reading, processing, and analysis of spectral information.

Author: [Your Name]
Date: [Current Date]
Version: 1.0.0
"""

import os
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SpectralData:
    """Data class for storing spectral measurement data."""
    time_point: float
    intensity: float

class OESAnalyzer:
    """
    Analyzer class for processing OES data.
    
    This class provides methods for reading, processing, and analyzing
    spectral data from OES measurements.
    """
    
    def __init__(self):
        """Initialize the OES Analyzer."""
        self._all_data: Dict[float, List[float]] = {}
        logger.info("OES Analyzer initialized")



    @staticmethod
    def generate_file_names(base_name: str, start: int, end: int, extension: str = '.txt') -> List[str]:
        """
        Generate a list of file names based on the parameters.

        Args:
            base_name: Base name for the files
            start: Starting index
            end: Ending index
            extension: File extension (default: '.txt')

        Returns:
            List of generated file names
        """
        return [f"{base_name}_S{str(i).zfill(4)}{extension}" for i in range(start, end + 1)]

    def read_data(self, file_path: str) -> List[SpectralData]:
        """
        Read data from a given file.

        Args:
            file_path: Path to the data file

        Returns:
            List of SpectralData objects containing time points and intensities
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                contents = file.readlines()
            
            data = []
            for line in contents:
                if ';' in line:
                    try:
                        time_point, intensity = map(float, line.strip().split(';'))
                        data.append(SpectralData(time_point, intensity))
                    except ValueError as e:
                        logger.warning(f"Skipping invalid line in {file_path}: {e}")
                        continue
            
            logger.debug(f"Successfully read {len(data)} data points from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    def read_file_to_data(self, file_names: List[str], base_path: str) -> Dict[float, List[float]]:
        """
        Read all files and store data.

        Args:
            file_names: List of file names to process
            base_path: Base path for the files

        Returns:
            Dictionary mapping time points to lists of intensity values
        """
        self._all_data.clear()
        
        for file_name in file_names:
            try:
                file_path = os.path.join(base_path, file_name)
                data = self.read_data(file_path)
                
                for spectral_data in data:
                    if spectral_data.time_point not in self._all_data:
                        self._all_data[spectral_data.time_point] = []
                    self._all_data[spectral_data.time_point].append(spectral_data.intensity)
                    
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {e}")
                continue
        
        logger.info(f"Processed {len(file_names)} files with {len(self._all_data)} time points")
        return self._all_data

    def detect_activate_time(self, max_wave: float, threshold: float, start_index: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Find activation time points.

        Args:
            max_wave: Wave length to analyze
            threshold: Threshold for activation detection
            start_index: Starting index for the analysis

        Returns:
            Tuple of activation start and end times
        """
        if max_wave not in self._all_data:
            logger.error(f"Wave length {max_wave} not found in data")
            return None, None

        time_series = self._all_data[max_wave]
        activated = False
        activate_time = None
        end_time = None
        
        for i in range(len(time_series) - 1):
            diff = time_series[i + 1] - time_series[i]
            
            if not activated and diff > threshold:
                activate_time = i + 1 + start_index
                activated = True
                logger.debug(f"Activation detected at index {activate_time}")
            elif activated and diff < -threshold:
                end_time = i + 1 + start_index
                logger.debug(f"Deactivation detected at index {end_time}")
                break
                
        return activate_time, end_time

    def analyze_data(self, 
                    base_path: str, 
                    base_name: str, 
                    detect_wave: float = 657, 
                    threshold: float = 1000, 
                    section: int = 3, 
                    start_index: int = 0) -> pd.DataFrame:
        """
        Analyze data and return results DataFrame.

        Args:
            base_path: Base path for the files
            base_name: Base name for the files
            detect_wave: Wave length to analyze
            threshold: Threshold for analysis
            section: Number of sections to analyze
            start_index: Starting index for analysis

        Returns:
            DataFrame containing analysis results
        """
        try:
            # Detect activation time
            activate_time, end_time = self.detect_activate_time(detect_wave, threshold, start_index)
            if not all([activate_time, end_time]):
                raise ValueError("Could not detect activation time")

            # Process data for activation period
            activate_time_file = self.generate_file_names(base_name, activate_time + 10, end_time - 10)
            activate_time_data = self.read_file_to_data(activate_time_file, base_path)
            
            wave_data = activate_time_data[detect_wave]
            section_size = len(wave_data) // section
            
            # Analyze sections
            sectioned_data = self._analyze_sections(wave_data, section, section_size)
            
            # Convert results to DataFrame
            results = self._prepare_results_dataframe(sectioned_data)
            
            logger.info("Data analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error during data analysis: {e}")
            raise

    def _analyze_sections(self, wave_data: List[float], section: int, section_size: int) -> Dict[str, Dict[str, float]]:
        """
        Analyze wave data in sections.

        Args:
            wave_data: List of wave data points
            section: Number of sections
            section_size: Size of each section

        Returns:
            Dictionary containing analysis results for each section
        """
        sectioned_data = {}
        
        # Analyze individual sections
        for i in range(section):
            start_idx = i * section_size
            end_idx = start_idx + section_size if i < section - 1 else len(wave_data)
            section_wave_data = wave_data[start_idx:end_idx]
            
            std_value = np.std(section_wave_data)
            average_value = np.mean(section_wave_data)
            stability = round((std_value / average_value) * 100, 3)
            
            sectioned_data[f'區段{i+1}'] = {
                'mean': average_value,
                'std': std_value,
                '穩定度': stability
            }
        
        # Analyze total section
        total_mean = np.mean(wave_data)
        total_std = np.std(wave_data)
        total_stability = round((total_std / total_mean) * 100, 3)
        
        sectioned_data['總區段'] = {
            'mean': total_mean,
            'std': total_std,
            '穩定度': total_stability
        }
        
        return sectioned_data

    def _prepare_results_dataframe(self, sectioned_data: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Prepare results DataFrame from sectioned data.

        Args:
            sectioned_data: Dictionary containing analysis results

        Returns:
            DataFrame containing formatted results
        """
        results = []
        for section_name, stats in sectioned_data.items():
            results.append([
                section_name,
                stats['mean'],
                stats['std'],
                stats['穩定度']
            ])
        
        return pd.DataFrame(results, columns=['區段', '平均值', '標準差', '穩定度'])

    def save_to_excel(self, df: pd.DataFrame, base_path: str, threshold: float = 1000) -> None:
        """
        Save analysis results to Excel file.

        Args:
            df: DataFrame containing results
            base_path: Base path for saving the file
            threshold: Threshold value used in analysis
        """
        try:
            # 使用用戶選擇的儲存路徑
            output_name = os.path.basename(base_path)
            excel_name = os.path.join(base_path, f'{output_name}.xlsx')  # 更新儲存路徑
            
            with pd.ExcelWriter(excel_name) as writer:
                df.to_excel(writer, sheet_name=str(threshold), index=False)
            
            logger.info(f"Results successfully saved to {excel_name}")
            
        except Exception as e:
            logger.error(f"Error saving results to Excel: {e}")
            raise

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