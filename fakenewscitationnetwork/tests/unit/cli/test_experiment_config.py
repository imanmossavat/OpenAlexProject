import pytest
from pathlib import Path
from ArticleCrawler.cli.models.experiment_config import ExperimentConfig, ConfigBuilder


@pytest.mark.unit
class TestExperimentConfig:
    
    def test_initialization_minimal(self):
        config = ExperimentConfig(
            name="test_experiment",
            seeds=["W123", "W456"]
        )
        assert config.name == "test_experiment"
        assert config.seeds == ["W123", "W456"]
        assert config.max_iterations == 1
        assert config.papers_per_iteration == 1
    
    def test_initialization_full(self, temp_dir):
        config = ExperimentConfig(
            name="full_experiment",
            seeds=["W123"],
            keywords=["machine learning", "AI"],
            max_iterations=5,
            papers_per_iteration=10,
            api_provider="semantic_scholar",
            num_topics=30,
            language="es",
            root_folder=temp_dir
        )
        assert config.name == "full_experiment"
        assert config.keywords == ["machine learning", "AI"]
        assert config.max_iterations == 5
        assert config.papers_per_iteration == 10
        assert config.api_provider == "semantic_scholar"
        assert config.num_topics == 30
        assert config.language == "es"
        assert config.root_folder == temp_dir
    
    def test_validate_api_provider_valid(self):
        config = ExperimentConfig(
            name="test",
            seeds=["W123"],
            api_provider="openalex"
        )
        assert config.api_provider == "openalex"
        
        config2 = ExperimentConfig(
            name="test",
            seeds=["W123"],
            api_provider="semantic_scholar"
        )
        assert config2.api_provider == "semantic_scholar"
    
    def test_validate_api_provider_invalid(self):
        with pytest.raises(ValueError):
            ExperimentConfig(
                name="test",
                seeds=["W123"],
                api_provider="invalid_provider"
            )
    
    def test_validate_topic_model_valid(self):
        config = ExperimentConfig(
            name="test",
            seeds=["W123"],
            topic_model="NMF"
        )
        assert config.topic_model == "NMF"
        
        config2 = ExperimentConfig(
            name="test",
            seeds=["W123"],
            topic_model="LDA"
        )
        assert config2.topic_model == "LDA"
    
    def test_validate_topic_model_invalid(self):
        with pytest.raises(ValueError):
            ExperimentConfig(
                name="test",
                seeds=["W123"],
                topic_model="INVALID"
            )
    
    def test_validate_log_level_valid(self):
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            config = ExperimentConfig(
                name="test",
                seeds=["W123"],
                log_level=level
            )
            assert config.log_level == level

    
    def test_default_values(self):
        config = ExperimentConfig(name="test", seeds=["W123"])
        assert config.max_iterations == 1
        assert config.papers_per_iteration == 1
        assert config.api_provider == "openalex"
        assert config.num_topics == 20
        assert config.topic_model == "NMF"
        assert config.language == "en"
        assert config.save_figures is True
        assert config.enable_retraction_watch is True


@pytest.mark.unit
class TestConfigBuilder:
    
    def test_builder_defaults(self):
        builder = ConfigBuilder()
        assert builder._config["max_iterations"] == 1
        assert builder._config["papers_per_iteration"] == 1
        assert builder._config["api_provider"] == "openalex"
        assert builder._config["num_topics"] == 20
    
    def test_builder_with_name(self):
        builder = ConfigBuilder()
        builder.with_name("my_experiment")
        assert builder._config["name"] == "my_experiment"
    
    def test_builder_with_seeds(self):
        builder = ConfigBuilder()
        builder.with_seeds(["W123", "W456"])
        assert builder._config["seeds"] == ["W123", "W456"]
    
    def test_builder_with_keywords(self):
        builder = ConfigBuilder()
        builder.with_keywords(["AI", "ML"])
        assert builder._config["keywords"] == ["AI", "ML"]
    
    def test_builder_with_iterations(self):
        builder = ConfigBuilder()
        builder.with_max_iterations(5)
        builder.with_papers_per_iteration(10)
        assert builder._config["max_iterations"] == 5
        assert builder._config["papers_per_iteration"] == 10
    
    def test_builder_chaining(self):
        builder = ConfigBuilder()
        builder.with_name("test").with_seeds(["W123"]).with_max_iterations(3)
        assert builder._config["name"] == "test"
        assert builder._config["seeds"] == ["W123"]
        assert builder._config["max_iterations"] == 3
    
    def test_builder_build(self):
        builder = ConfigBuilder()
        builder.with_name("test_exp").with_seeds(["W123", "W456"])
        config = builder.build()
        assert isinstance(config, ExperimentConfig)
        assert config.name == "test_exp"
        assert config.seeds == ["W123", "W456"]
    
    def test_builder_with_advanced_options(self):
        builder = ConfigBuilder()
        builder.with_name("advanced")
        builder.with_seeds(["W123"])
        builder.with_num_topics(30)
        builder.with_topic_model("LDA")
        builder.with_include_author_nodes(True)
        builder.with_enable_retraction_watch(False)
        builder.with_save_figures(False)
        builder.with_language("es")
        config = builder.build()
        assert config.num_topics == 30
        assert config.topic_model == "LDA"
        assert config.include_author_nodes is True
        assert config.enable_retraction_watch is False
        assert config.save_figures is False
        assert config.language == "es"