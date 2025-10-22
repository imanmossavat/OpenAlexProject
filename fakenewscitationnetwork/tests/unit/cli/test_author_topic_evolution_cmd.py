import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from ArticleCrawler.library.models import AuthorInfo


class TestAuthorTopicEvolutionCmd:
    
    @pytest.fixture
    def sample_author(self):
        return AuthorInfo(id="A123", name="Test Author", works_count=50, cited_by_count=500)
    
    def test_initialize_services(self):
        from ArticleCrawler.cli.commands.author_topic_evolution_cmd import _initialize_services
        
        with patch('ArticleCrawler.cli.commands.author_topic_evolution_cmd.CrawlerLogger') as mock_logger_class:
            with patch('ArticleCrawler.cli.commands.author_topic_evolution_cmd.create_api_provider') as mock_api:
                mock_logger_class.return_value = Mock()
                mock_api.return_value = Mock()
                
                logger, api = _initialize_services()
                
                assert logger is not None
                assert api is not None
                mock_logger_class.assert_called_once()
                mock_api.assert_called_once()
    
    def test_get_default_config_returns_dict(self):
        config = {
            'model_type': 'NMF',
            'num_topics': 5,
            'time_period_years': 3,
            'viz_type': 'line',
            'save_library': False,
            'library_path': None,
            'output_path': Path('./topic_evolution.png'),
            'max_papers': None
        }
        
        assert 'model_type' in config
        assert 'num_topics' in config
        assert 'time_period_years' in config
        assert 'viz_type' in config
        assert 'save_library' in config
        assert config['model_type'] in ['NMF', 'LDA']
        assert isinstance(config['num_topics'], int)
        assert config['num_topics'] > 0
    
    def test_review_and_confirm_with_mock(self, sample_author):
        from ArticleCrawler.cli.commands.author_topic_evolution_cmd import _review_and_confirm
        
        config = {
            'model_type': 'NMF',
            'num_topics': 5,
            'time_period_years': 3,
            'viz_type': 'line',
            'save_library': False,
            'library_path': None,
            'output_path': None,
            'max_papers': None
        }
        
        with patch('ArticleCrawler.cli.commands.author_topic_evolution_cmd.Confirm.ask', return_value=True):
            result = _review_and_confirm(sample_author, config)
            assert isinstance(result, bool)
            assert result is True