import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.cli.commands.edit_wizard import EditWizardCommand
from ArticleCrawler.cli.models.experiment_config import ExperimentConfig


@pytest.mark.integration
class TestEditWizardIntegration:
    
    @pytest.fixture
    def mock_prompter(self):
        prompter = Mock()
        prompter.console = Mock()
        prompter.input = Mock()
        prompter.input_int = Mock()
        prompter.choice = Mock()
        prompter.confirm = Mock()
        prompter.checkbox = Mock()
        prompter.error = Mock()
        return prompter
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def edit_wizard(self, mock_prompter, mock_console):
        return EditWizardCommand(mock_prompter, mock_console)
    
    @pytest.fixture
    def sample_config(self, temp_dir):
        config = ExperimentConfig(
            name='original_exp',
            seeds=['W123', 'W456'],
            keywords=['AI', 'ML'],
            api_provider='openalex',
            max_iterations=3,
            papers_per_iteration=5
        )
        exp_dir = temp_dir / 'crawler_experiments' / 'original_exp'
        exp_dir.mkdir(parents=True)
        from ArticleCrawler.cli.utils.config_loader import save_config
        save_config(config, exp_dir / 'config.yaml')
        return exp_dir / 'config.yaml'
    
    def test_run_with_config_path(self, edit_wizard, mock_prompter, sample_config):
        mock_prompter.input.return_value = "edited_exp"
        mock_prompter.confirm.return_value = True
        
        with patch.object(edit_wizard, '_show_edit_menu', side_effect=[6]):
            config = edit_wizard.run(config_path=sample_config)
        
        assert config is not None
        assert config.name == "edited_exp"
        assert config.seeds == ['W123', 'W456']
        assert config.keywords == ['AI', 'ML']
    
    def test_run_without_config_path_select_existing(self, edit_wizard, mock_prompter, sample_config, temp_dir):
        mock_prompter.input.return_value = "new_exp"
        mock_prompter.input_int.return_value = 1
        mock_prompter.confirm.return_value = True
        
        with patch.object(edit_wizard, '_select_experiment') as mock_select_exp:
            from ArticleCrawler.cli.utils.config_loader import load_config
            mock_select_exp.return_value = load_config(sample_config)
            
            with patch.object(edit_wizard, '_show_edit_menu', side_effect=[6]):
                config = edit_wizard.run()
            
            assert config is not None
            assert config.name == "new_exp"
    
    def test_edit_seeds_add_more(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_seeds(['W123'])
        builder.with_api_provider('openalex')
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.choice.return_value = 0
        with patch.object(wizard_cmd, '_get_seed_papers', return_value=['W456', 'W789']):
            edit_wizard._edit_seeds(builder, wizard_cmd)
        
        seeds = builder._config['seeds']
        assert 'W123' in seeds
        assert 'W456' in seeds
        assert 'W789' in seeds
    
    def test_edit_seeds_remove(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_seeds(['W123', 'W456', 'W789'])
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.choice.return_value = 1
        mock_prompter.checkbox.return_value = ['W456']
        
        edit_wizard._edit_seeds(builder, wizard_cmd)
        
        seeds = builder._config['seeds']
        assert 'W123' in seeds
        assert 'W456' not in seeds
        assert 'W789' in seeds
    
    def test_edit_seeds_replace_all(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        from ArticleCrawler.cli.commands.wizard import WizardCommand
        
        builder = ConfigBuilder()
        builder.with_seeds(['W123', 'W456'])
        builder.with_api_provider('openalex')
        
        wizard_cmd = WizardCommand(mock_prompter, ConfigBuilder(), mock_prompter.console)
        
        mock_prompter.choice.return_value = 2
        with patch.object(wizard_cmd, '_get_seed_papers', return_value=['W999']):
            edit_wizard._edit_seeds(builder, wizard_cmd)
        
        seeds = builder._config['seeds']
        assert seeds == ['W999']
    
    def test_edit_keywords_add_more(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        
        builder = ConfigBuilder()
        builder.with_keywords(['AI'])
        
        mock_prompter.choice.return_value = 0
        mock_prompter.input.side_effect = ['ML', 'NLP', '']
        
        edit_wizard._edit_keywords(builder)
        
        keywords = builder._config['keywords']
        assert 'AI' in keywords
        assert 'ML' in keywords
        assert 'NLP' in keywords
    
    def test_edit_keywords_remove(self, edit_wizard, mock_prompter):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        
        builder = ConfigBuilder()
        builder.with_keywords(['AI', 'ML', 'NLP'])
        
        mock_prompter.choice.return_value = 1
        mock_prompter.checkbox.return_value = ['ML']
        
        edit_wizard._edit_keywords(builder)
        
        keywords = builder._config['keywords']
        assert 'AI' in keywords
        assert 'ML' not in keywords
        assert 'NLP' in keywords
    
    def test_run_cancelled_by_user(self, edit_wizard, mock_prompter, sample_config):
        mock_prompter.input.side_effect = KeyboardInterrupt()
        
        config = edit_wizard.run(config_path=sample_config)
        
        assert config is None
    
    def test_select_from_path_nonexistent(self, edit_wizard, mock_prompter):
        mock_prompter.input.return_value = "/nonexistent/config.yaml"
        
        result = edit_wizard._select_from_path()
        
        assert result is None
        mock_prompter.error.assert_called_once()
    
    def test_populate_builder_from_config(self, edit_wizard):
        from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
        
        config = ExperimentConfig(
            name='test',
            seeds=['W123'],
            keywords=['AI'],
            api_provider='semantic_scholar',
            max_iterations=5,
            papers_per_iteration=10,
            num_topics=15,
            topic_model='LDA',
            include_author_nodes=True
        )
        
        builder = ConfigBuilder()
        edit_wizard._populate_builder_from_config(builder, config)
        
        assert builder._config['seeds'] == ['W123']
        assert builder._config['keywords'] == ['AI']
        assert builder._config['api_provider'] == 'semantic_scholar'
        assert builder._config['max_iterations'] == 5
        assert builder._config['papers_per_iteration'] == 10
        assert builder._config['num_topics'] == 15
        assert builder._config['topic_model'] == 'LDA'
        assert builder._config['include_author_nodes'] == True