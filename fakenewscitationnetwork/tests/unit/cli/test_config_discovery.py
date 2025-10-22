import pytest
from pathlib import Path
from datetime import datetime
from ArticleCrawler.cli.utils.config_discovery import ConfigDiscovery, ConfigSummary
from ArticleCrawler.cli.models.experiment_config import ExperimentConfig


@pytest.mark.unit
class TestConfigDiscovery:
    
    @pytest.fixture
    def experiments_folder(self, temp_dir):
        folder = temp_dir / 'crawler_experiments'
        folder.mkdir()
        return folder
    
    @pytest.fixture
    def sample_experiment(self, experiments_folder):
        exp_dir = experiments_folder / 'test_exp1'
        exp_dir.mkdir()
        config = ExperimentConfig(
            name='test_exp1',
            seeds=['W123', 'W456'],
            keywords=['AI'],
            api_provider='openalex'
        )
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config, exp_dir / 'config.yaml')
        return exp_dir
    
    def test_find_experiments_empty_folder(self, experiments_folder):
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 0
    
    def test_find_experiments_nonexistent_folder(self, temp_dir):
        nonexistent = temp_dir / 'does_not_exist'
        summaries = ConfigDiscovery.find_experiments(nonexistent)
        assert len(summaries) == 0
    
    def test_find_experiments_with_valid_config(self, experiments_folder, sample_experiment):
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 1
        assert summaries[0].name == 'test_exp1'
        assert summaries[0].num_seeds == 2
        assert summaries[0].num_keywords == 1
        assert summaries[0].api_provider == 'openalex'
    
    def test_find_experiments_multiple_experiments(self, experiments_folder):
        exp1_dir = experiments_folder / 'exp1'
        exp1_dir.mkdir()
        config1 = ExperimentConfig(
            name='exp1',
            seeds=['W123'],
            keywords=['ML'],
            api_provider='openalex'
        )
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config1, exp1_dir / 'config.yaml')
        
        exp2_dir = experiments_folder / 'exp2'
        exp2_dir.mkdir()
        config2 = ExperimentConfig(
            name='exp2',
            seeds=['W789', 'W012'],
            keywords=['AI', 'NLP'],
            api_provider='semantic_scholar'
        )
        save_config(config2, exp2_dir / 'config.yaml')
        
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 2
        names = [s.name for s in summaries]
        assert 'exp1' in names
        assert 'exp2' in names
    
    def test_find_experiments_skips_invalid_configs(self, experiments_folder):
        valid_dir = experiments_folder / 'valid'
        valid_dir.mkdir()
        config = ExperimentConfig(
            name='valid',
            seeds=['W123'],
            keywords=['test'],
            api_provider='openalex'
        )
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config, valid_dir / 'config.yaml')
        
        invalid_dir = experiments_folder / 'invalid'
        invalid_dir.mkdir()
        (invalid_dir / 'config.yaml').write_text('invalid: yaml: content')
        
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 1
        assert summaries[0].name == 'valid'
    
    def test_find_experiments_skips_directories_without_config(self, experiments_folder):
        with_config = experiments_folder / 'has_config'
        with_config.mkdir()
        config = ExperimentConfig(
            name='has_config',
            seeds=['W123'],
            keywords=[],
            api_provider='openalex'
        )
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config, with_config / 'config.yaml')
        
        without_config = experiments_folder / 'no_config'
        without_config.mkdir()
        
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 1
        assert summaries[0].name == 'has_config'
    
    def test_find_experiments_sorted_by_created_date(self, experiments_folder):
        import time
        
        exp1_dir = experiments_folder / 'exp1'
        exp1_dir.mkdir()
        config1 = ExperimentConfig(
            name='exp1',
            seeds=['W123'],
            keywords=[],
            api_provider='openalex'
        )
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config1, exp1_dir / 'config.yaml')
        
        time.sleep(0.1)
        
        exp2_dir = experiments_folder / 'exp2'
        exp2_dir.mkdir()
        config2 = ExperimentConfig(
            name='exp2',
            seeds=['W456'],
            keywords=[],
            api_provider='openalex'
        )
        save_config(config2, exp2_dir / 'config.yaml')
        
        summaries = ConfigDiscovery.find_experiments(experiments_folder)
        assert len(summaries) == 2
        assert summaries[0].name == 'exp2'
        assert summaries[1].name == 'exp1'
    
    def test_get_default_experiments_folder(self):
        default_folder = ConfigDiscovery.get_default_experiments_folder()
        assert isinstance(default_folder, Path)
        assert default_folder.name == 'crawler_experiments'
        assert 'data' in default_folder.parts
    
    def test_config_summary_dataclass(self):
        summary = ConfigSummary(
            name='test',
            path=Path('/test/path'),
            config_path=Path('/test/path/config.yaml'),
            created=datetime(2024, 1, 1),
            num_seeds=5,
            num_keywords=3,
            api_provider='openalex'
        )
        assert summary.name == 'test'
        assert summary.num_seeds == 5
        assert summary.num_keywords == 3