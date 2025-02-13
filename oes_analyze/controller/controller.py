import logging
from model.analyzer import OESAnalyzer
import pandas as pd
import os
from typing import Tuple, Optional, List
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OESController:
    """
    Controller class for coordinating the interaction between the Model (OESAnalyzer)
    and the View (GUI or other output mechanisms).
    """

    def __init__(self):
        """Initialize the OES Controller with the OESAnalyzer instance."""
        self.analyzer = OESAnalyzer()
        self.analysis_results = None  # To store analysis results

    def load_and_process_data(self, base_path: str, base_name: str, start_index: int, end_index: int) -> None:
        """
        Load data from files and process them.

        Args:
            base_path: Base directory where the data files are located.
            base_name: Base name of the files to process.
            start_index: Starting index of the files.
            end_index: Ending index of the files.

        Returns:
            None
        """
        try:
            logger.info("Generating file names...")
            file_names = self.analyzer.generate_file_names(base_name, start_index, end_index)

            logger.info("Reading and processing data...")
            self.analyzer.read_file_to_data(file_names, base_path)
            logger.info("Data successfully loaded and processed.")

        except Exception as e:
            logger.error(f"Error during data loading and processing: {e}")
            raise
    def scan_file_indices(self, folder_path: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Scan the folder to find the range of indices for the given base name.

        Args:
            folder_path: Path to the folder containing the files.
            base_name: Base name of the files.

        Returns:
            A tuple containing the start and end indices.
        """
        try:
            files = os.listdir(folder_path)
            spectrum_files = [f for f in files if f.endswith('.txt') and '_S' in f]
            
            if not spectrum_files:
                return None, None, None
            
            base_name = spectrum_files[0].split('_S')[0]            
            indices = []
            for file in spectrum_files:
                if file.startswith(base_name):
                    try:
                        index = int(file.split('_S')[-1].replace('.txt', ''))
                        indices.append(index)
                    except ValueError:
                        continue
            
            if not indices:
                return None, None, None
                
            return base_name, min(indices), max(indices)
        
        except Exception as e:
            logger.error(f"Error finding spectrum files: {e}")
            return None, None, None
    def analyze_data(self, detect_wave: float, threshold: float, section_count: int) -> pd.DataFrame:
        """
        Analyze the processed data and return a DataFrame of results.

        Args:
            detect_wave: Wave length to analyze.
            threshold: Threshold for activation detection.
            section_count: Number of sections for analysis.

        Returns:
            DataFrame containing the analysis results.
        """
        try:
            logger.info("Detecting activation and analyzing data...")

            # Ensure the data for the specific wave exists
            if detect_wave not in self.analyzer._all_data:
                raise ValueError(f"Wave length {detect_wave} not found in the data.")

            wave_data = self.analyzer._all_data[detect_wave]
            sectioned_data = self.analyzer.analyze_sections(wave_data, section_count)

            # Store and return results
            self.analysis_results = self.analyzer.prepare_results_dataframe(sectioned_data)
            logger.info("Data analysis completed successfully.")
            return self.analysis_results

        except Exception as e:
            logger.error(f"Error during data analysis: {e}")
            raise

    def save_results_to_excel(self, base_path: str, threshold: float) -> None:
        """
        Save the analysis results to an Excel file.

        Args:
            base_path: Directory where the results should be saved.
            threshold: Threshold value used in the analysis (included in file naming).

        Returns:
            None
        """
        try:
            if self.analysis_results is None:
                raise ValueError("No analysis results to save. Please run the analysis first.")

            output_name = "Analysis_Results.xlsx"
            excel_path = f"{base_path}/{output_name}"

            with pd.ExcelWriter(excel_path) as writer:
                self.analysis_results.to_excel(writer, sheet_name=f"Threshold_{threshold}", index=False)

            logger.info(f"Results successfully saved to {excel_path}")

        except Exception as e:
            logger.error(f"Error saving results to Excel: {e}")
            raise
