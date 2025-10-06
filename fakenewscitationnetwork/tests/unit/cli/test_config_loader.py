import pytest
import yaml
from pathlib import Path
from ArticleCrawler.cli.utils.config_loader import load_config, save_config, _flatten_config, _structure_config
from ArticleCrawler.cli.models.experiment_config import ExperimentConfig


@pytest.mark.unit
class TestConfigLoader:
    
    @pytest.fixture
    def sample_config_dict(self):
        return {
            "name": "test_experiment",
            "seeds": ["W123", "W456"],
            "keywords": ["AI", "ML"],
            "max_iterations": 3,
            "papers_per_iteration": 5,
            "api_provider": "openalex"
        }
    
    @pytest.fixture
    def sample_config_file(self, temp_dir, sample_config_dict):
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config_dict, f)
        return config_file
    
    def test_load_config_success(self, sample_config_file):
        config = load_config(sample_config_file)
        assert isinstance(config, ExperimentConfig)
        assert config.name == "test_experiment"
        assert config.seeds == ["W123", "W456"]
        assert config.keywords == ["AI", "ML"]
        assert config.max_iterations == 3
    
    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))
    
    def test_load_config_nested_structure(self, temp_dir):
        nested_config = {
            "experiment": {
                "name": "nested_test",
                "seeds": ["W789"]
            },
            "crawling": {
                "max_iterations": 2,
                "papers_per_iteration": 3
            }
        }
        config_file = temp_dir / "nested.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(nested_config, f)
        config = load_config(config_file)
        assert config.name == "nested_test"
        assert config.seeds == ["W789"]
    
    def test_save_config_success(self, temp_dir):
        config = ExperimentConfig(
            name="save_test",
            seeds=["W123"],
            keywords=["test"],
            max_iterations=2
        )
        config_file = temp_dir / "saved_config.yaml"
        save_config(config, config_file)
        assert config_file.exists()
        with open(config_file, 'r') as f:
            loaded_data = yaml.safe_load(f)
        assert "name" in loaded_data or any("name" in v for v in loaded_data.values() if isinstance(v, dict))
    
    
    def test_save_config_creates_directory(self, temp_dir):
        config = ExperimentConfig(name="test", seeds=["W123"])
        nested_path = temp_dir / "subdir" / "config.yaml"
        save_config(config, nested_path)
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_flatten_config_already_flat(self):
        flat_dict = {"name": "test", "seeds": ["W123"], "max_iterations": 5}
        result = _flatten_config(flat_dict)
        assert result == flat_dict
    
    def test_flatten_config_nested(self):
        nested_dict = {
            "experiment": {"name": "test", "seeds": ["W123"]},
            "settings": {"max_iterations": 5}
        }
        result = _flatten_config(nested_dict)
        assert result["name"] == "test"
        assert result["seeds"] == ["W123"]
        assert result["max_iterations"] == 5