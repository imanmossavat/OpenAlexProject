import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.cli.commands.edit_wizard import EditWizardCommand
from ArticleCrawler.cli.models.experiment_config import ExperimentConfig, ConfigBuilder


@pytest.mark.unit
class TestEditWizardUnit:
    
    @pytest.fixture
    def mock_prompter(self):
        prompter = Mock()
        prompter.console = Mock()
        return prompter
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def edit_wizard(self, mock_prompter, mock_console):
        return EditWizardCommand(mock_prompter, mock_console)
    
    def test_get_new_experiment_name_valid(self, edit_wizard, mock_prompter):
        mock_prompter.input.return_value = "new_experiment"
        
        name = edit_wizard._get_new_experiment_name("old_experiment")
        
        assert name == "new_experiment"
    
    def test_get_new_experiment_name_sanitization(self, edit_wizard, mock_prompter):
        mock_prompter.input.return_value = "exp@test#name"
        
        name = edit_wizard._get_new_experiment_name("old")
        
        assert "@" not in name
        assert "#" not in name
        assert name == "exptestname"
    
    def test_get_new_experiment_name_empty_retry(self, edit_wizard, mock_prompter):
        mock_prompter.input.side_effect = ["", "valid_name"]
        
        name = edit_wizard._get_new_experiment_name("old")
        
        assert name == "valid_name"
        assert mock_prompter.input.call_count == 2
    
    def test_show_edit_menu(self, edit_wizard, mock_prompter):
        mock_prompter.choice.return_value = 2
        
        choice = edit_wizard._show_edit_menu()
        
        assert choice == 3
        mock_prompter.choice.assert_called_once()
    
    def test_edit_api_provider(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_api_provider('openalex')
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        with patch.object(wizard_cmd, '_get_api_provider', return_value='semantic_scholar'):
            edit_wizard._edit_api_provider(builder, wizard_cmd)
        
        assert builder._config['api_provider'] == 'semantic_scholar'
    
    def test_edit_basic_config_confirmed(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_max_iterations(1)
        builder.with_papers_per_iteration(1)
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.confirm.return_value = True
        with patch.object(wizard_cmd, '_get_basic_config') as mock_get:
            edit_wizard._edit_basic_config(builder, wizard_cmd)
        
        mock_get.assert_called_once()
    
    def test_edit_basic_config_declined(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.confirm.return_value = False
        with patch.object(wizard_cmd, '_get_basic_config') as mock_get:
            edit_wizard._edit_basic_config(builder, wizard_cmd)
        
        mock_get.assert_not_called()
    
    def test_review_and_confirm_accepted(self, edit_wizard, mock_prompter):
        config = ExperimentConfig(
            name='test',
            seeds=['W123'],
            keywords=['AI'],
            api_provider='openalex'
        )
        
        mock_prompter.confirm.return_value = True
        
        result = edit_wizard._review_and_confirm(config)
        
        assert result is True
    
    def test_review_and_confirm_rejected(self, edit_wizard, mock_prompter):
        config = ExperimentConfig(
            name='test',
            seeds=['W123'],
            keywords=['AI'],
            api_provider='openalex'
        )
        
        mock_prompter.confirm.return_value = False
        
        result = edit_wizard._review_and_confirm(config)
        
        assert result is False
    
    def test_edit_keywords_keep_current(self, edit_wizard, mock_prompter):
        builder = ConfigBuilder()
        builder.with_keywords(['AI', 'ML'])
        
        mock_prompter.choice.return_value = 3
        
        edit_wizard._edit_keywords(builder)
        
        assert builder._config['keywords'] == ['AI', 'ML']
    
    def test_edit_seeds_keep_current(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_seeds(['W123', 'W456'])
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.choice.return_value = 3
        
        edit_wizard._edit_seeds(builder, wizard_cmd)
        
        assert builder._config['seeds'] == ['W123', 'W456']