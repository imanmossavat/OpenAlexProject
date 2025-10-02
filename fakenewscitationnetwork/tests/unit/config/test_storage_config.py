import pytest
from pathlib import Path
from ArticleCrawler.config import StorageAndLoggingConfig


@pytest.mark.unit
class TestStorageAndLoggingConfig:
    
    def test_default_initialization(self, temp_dir):
        config = StorageAndLoggingConfig(root_folder=temp_dir)
        assert config.experiment_file_name == 'myExperiment'
        assert config.root_folder == temp_dir
        assert config.log_level == 'DEBUG'
    
    def test_custom_initialization(self, temp_dir):
        config = StorageAndLoggingConfig(
            experiment_file_name='test_exp',
            root_folder=temp_dir,
            log_level='INFO',
            pkl_save_frequency=2
        )
        assert config.experiment_file_name == 'test_exp'
        assert config.log_level == 'INFO'
        assert config.pkl_save_frequency == 2
    
    def test_folder_structure_created(self, temp_dir):
        config = StorageAndLoggingConfig(
            experiment_file_name='test',
            root_folder=temp_dir
        )
        assert isinstance(config.experiment_folder, Path)
        assert isinstance(config.pkl_folder, Path)
        assert isinstance(config.log_folder, Path)
        assert isinstance(config.vault_folder, Path)
    
    def test_create_directories(self, temp_dir):
        config = StorageAndLoggingConfig(root_folder=temp_dir)
        config.create_directories()
        assert config.experiment_folder.exists()
        assert config.pkl_folder.exists()
        assert config.log_folder.exists()
    
    def test_all_folders_accessible(self, temp_dir):
        config = StorageAndLoggingConfig(root_folder=temp_dir)
        assert 'experiment_folder' in config.folders_all
        assert 'pkl_folder' in config.folders_all
        assert 'vault_folder' in config.folders_all 
