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

    def analyze_sections(self, wave_data: List[float], section: int) -> Dict[str, Dict[str, float]]:
        """
        Analyze wave data in sections.

        Args:
            wave_data: List of wave data points
            section: Number of sections

        Returns:
            Dictionary containing analysis results for each section
        """
        section_size = len(wave_data) // section
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

    def prepare_results_dataframe(self, sectioned_data: Dict[str, Dict[str, float]]) -> pd.DataFrame:
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
