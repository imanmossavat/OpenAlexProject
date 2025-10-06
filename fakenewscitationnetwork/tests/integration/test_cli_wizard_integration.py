import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.cli.commands.wizard import WizardCommand
from ArticleCrawler.cli.models.experiment_config import ConfigBuilder, ExperimentConfig


@pytest.mark.integration
class TestWizardCommandIntegration:
    
    @pytest.fixture
    def mock_prompter(self):
        prompter = Mock()
        prompter.console = Mock()
        return prompter
    
    @pytest.fixture
    def config_builder(self):
        return ConfigBuilder()
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def wizard(self, mock_prompter, config_builder, mock_console):
        return WizardCommand(mock_prompter, config_builder, mock_console)
    
    def test_wizard_complete_flow_minimal(self, wizard, mock_prompter, temp_dir):
        mock_prompter.input.side_effect = ["test_experiment"]
        mock_prompter.choice.side_effect = [0]
        with patch.object(wizard, '_get_seed_papers', return_value=["W123", "W456"]):
            with patch.object(wizard, '_get_keywords', return_value=["AI", "ML"]):
                with patch.object(wizard, '_get_basic_config'):
                    mock_prompter.confirm.side_effect = [False, True]
                    config = wizard.run(output_dir=temp_dir)
                    assert config is not None
                    assert config.name == "test_experiment"
                    assert config.seeds == ["W123", "W456"]
                    assert config.keywords == ["AI", "ML"]
    
    def test_wizard_complete_flow_with_advanced(self, wizard, mock_prompter, temp_dir):
        mock_prompter.input.side_effect = ["advanced_experiment"]
        mock_prompter.choice.side_effect = [1]
        with patch.object(wizard, '_get_seed_papers', return_value=["W789"]):
            with patch.object(wizard, '_get_keywords', return_value=["test"]):
                with patch.object(wizard, '_get_basic_config'):
                    with patch.object(wizard, '_get_advanced_config'):
                        mock_prompter.confirm.side_effect = [True, True]
                        config = wizard.run(output_dir=temp_dir)
                        assert config is not None
                        assert config.name == "advanced_experiment"
    
    def test_wizard_cancelled_by_user(self, wizard, mock_prompter, temp_dir):
        mock_prompter.input.side_effect = ["test"]
        mock_prompter.choice.side_effect = [0]
        with patch.object(wizard, '_get_seed_papers', return_value=["W123"]):
            with patch.object(wizard, '_get_keywords', return_value=["test"]):
                with patch.object(wizard, '_get_basic_config'):
                    mock_prompter.confirm.side_effect = [False, False]
                    config = wizard.run(output_dir=temp_dir)
                    assert config is None
    
    def test_get_experiment_name_sanitization(self, wizard, mock_prompter):
        mock_prompter.input.return_value = "test@experiment#name"
        name = wizard._get_experiment_name()
        assert "@" not in name
        assert "#" not in name
    
    def test_get_api_provider_openalex(self, wizard, mock_prompter):
        mock_prompter.choice.return_value = 0
        api_provider = wizard._get_api_provider()
        assert api_provider == "openalex"
    
    def test_get_api_provider_semantic_scholar(self, wizard, mock_prompter):
        mock_prompter.choice.return_value = 1
        api_provider = wizard._get_api_provider()
        assert api_provider == "semantic_scholar"