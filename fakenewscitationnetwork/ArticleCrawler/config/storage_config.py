from pathlib import Path
import inspect
from typing import Optional

class StorageAndLoggingConfig:
    """
    Configuration for file storage and logging operations.
    
    This class handles all storage and logging related settings including
    folder paths, log configuration, and experiment organization.
    """
    
    def __init__(self,
                 experiment_file_name: str = 'myExperiment',
                 root_folder: Path = Path('./data/crawler_experiments'),
                 
                 # Persistence settings
                 pkl_save_frequency: int = 1,
                 
                 # Logging settings
                 log_level: str = 'DEBUG',
                 log_format: str = '%(asctime)s - %(levelname)s - %(message)s',
                 max_log_size: int = 10 * 1024,
                 log_file_name: str = 'crawler.log',
                 log_backup_count: int = 5,
                 logger_name: str = 'crawler',
                 
                 # UI settings
                 open_vault_folder: bool = True):
        """
        Initialize storage and logging configuration.
        
        Args:
            experiment_file_name (str): Name for the experiment
            root_folder (Path): Base directory for experiments
            pkl_save_frequency (int): How often to save intermediate files
            log_level (str): Logging level
            log_format (str): Log message format
            max_log_size (int): Maximum log file size in bytes
            log_file_name (str): Name of log file
            log_backup_count (int): Number of log backup files to keep
            logger_name (str): Name of the logger
            open_vault_folder (bool): Whether to open vault folder after completion
        """
        caller_frame = inspect.stack()[1]
        caller_file = Path(caller_frame.filename).resolve()
        self.caller_file_path = caller_file
        self.caller_file_dir = caller_file.parent

        if not root_folder.is_absolute():
            self.root_folder = (self.caller_file_dir / root_folder).resolve()
        else:
            self.root_folder = root_folder.resolve()

        self.experiment_file_name = experiment_file_name
        self.pkl_save_frequency = pkl_save_frequency
        self.open_vault_folder = open_vault_folder

        self._setup_folder_structure()

        self.log_level = log_level
        self.log_format = log_format
        self.max_log_size = max_log_size
        self.log_file = log_file_name
        self.log_backup_count = log_backup_count
        self.logger_name = logger_name

        self.timestamp_final_pkl = None
        self.filepath_final_pkl = None

    def _setup_folder_structure(self):
        """Set up the complete folder structure for the experiment."""
        self.experiment_folder = self.root_folder / self.experiment_file_name
        
        # Core folders
        self.pkl_folder = self.experiment_folder / 'pkl'
        self.log_folder = self.experiment_folder / 'log'
        self.xlsx_folder = self.experiment_folder / 'xlsx'
        
        # Vault folders for outputs
        self.vault_folder = self.experiment_folder / 'vault'
        self.abstracts_folder = self.vault_folder / 'abstracts'
        self.figure_folder = self.vault_folder / 'figures'
        self.metadata_folder = self.vault_folder / 'meta_data'
        self.summary_folder = self.vault_folder / 'summary'
        self.recommendation_folder = self.vault_folder / 'recommendation'

        # Retraction watch files
        self.retraction_watch_csv_path = self.root_folder / "retraction_watch.csv"
        self.retraction_watch_version_file_path = self.root_folder / "retraction_watch_version.txt"

        # Dictionary of all folders for easy access
        self.folders_all = {
            'experiment_folder': self.experiment_folder,
            'pkl_folder': self.pkl_folder,
            'log_folder': self.log_folder,
            'vault_folder': self.vault_folder,
            'abstracts_folder': self.abstracts_folder,
            'figure_folder': self.figure_folder,
            'metadata_folder': self.metadata_folder,
            'summary_folder': self.summary_folder,
            'xlsx_folder': self.xlsx_folder,
            'recommendation_folder': self.recommendation_folder
        }

    def create_directories(self):
        """Create all necessary directories."""
        for folder in self.folders_all.values():
            folder.mkdir(parents=True, exist_ok=True)

    def copy(self):
        """Create a copy of this configuration."""
        return StorageAndLoggingConfig(
            experiment_file_name=self.experiment_file_name,
            root_folder=self.root_folder,
            pkl_save_frequency=self.pkl_save_frequency,
            log_level=self.log_level,
            log_format=self.log_format,
            max_log_size=self.max_log_size,
            log_file_name=self.log_file,
            log_backup_count=self.log_backup_count,
            logger_name=self.logger_name,
            open_vault_folder=self.open_vault_folder
        )

# Backward compatibility
class StorageAndLoggingOptions(StorageAndLoggingConfig):
    """Backward compatibility alias for StorageAndLoggingConfig."""
    pass