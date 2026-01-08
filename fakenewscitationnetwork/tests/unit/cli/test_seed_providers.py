import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.cli.ui.seed_providers import ManualSeedProvider, FileSeedProvider


@pytest.mark.unit
class TestManualSeedProvider:
    
    @pytest.fixture
    def mock_prompter(self):
        prompter = Mock()
        prompter.console = Mock()
        return prompter
    
    @pytest.fixture
    def provider(self, mock_prompter):
        return ManualSeedProvider(mock_prompter)
    
    def test_display_name(self, provider):
        assert provider.display_name() == "Enter paper IDs manually"
    
    @patch('ArticleCrawler.cli.ui.validators.validate_paper_id')
    def test_get_seeds_valid_input(self, mock_validate, provider, mock_prompter):
        mock_validate.return_value = True
        mock_prompter.input.side_effect = ["W123", "W456", ""]
        seeds = provider.get_seeds()
        assert seeds == ["W123", "W456"]
    
    @patch('ArticleCrawler.cli.ui.validators.validate_paper_id')
    def test_get_seeds_with_invalid(self, mock_validate, provider, mock_prompter):
        mock_validate.side_effect = [True, False, True, True]
        mock_prompter.input.side_effect = ["W123", "invalid", "W456", ""]
        seeds = provider.get_seeds()
        assert seeds == ["W123", "W456"]
        mock_prompter.error.assert_called_once()
    
    @patch('ArticleCrawler.cli.ui.validators.validate_paper_id')
    def test_get_seeds_empty(self, mock_validate, provider, mock_prompter):
        mock_prompter.input.return_value = ""
        seeds = provider.get_seeds()
        assert seeds == []


@pytest.mark.unit
class TestFileSeedProvider:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def provider(self, mock_prompter):
        return FileSeedProvider(mock_prompter)
    
    def test_display_name(self, provider):
        assert provider.display_name() == "Load from file"
    
    @patch('ArticleCrawler.cli.ui.validators.validate_file_path')
    def test_get_seeds_valid_file(self, mock_validate, provider, mock_prompter, temp_dir):
        seed_file = temp_dir / "seeds.txt"
        seed_file.write_text("W123\nW456\nW789")
        mock_validate.return_value = (True, "")
        mock_prompter.input.return_value = str(seed_file)
        seeds = provider.get_seeds()
        assert seeds == ["W123", "W456", "W789"]
    
    @patch('ArticleCrawler.cli.ui.validators.validate_file_path')
    def test_get_seeds_file_with_comments(self, mock_validate, provider, mock_prompter, temp_dir):
        seed_file = temp_dir / "seeds.txt"
        seed_file.write_text("W123\n# comment\nW456\n\nW789")
        mock_validate.return_value = (True, "")
        mock_prompter.input.return_value = str(seed_file)
        seeds = provider.get_seeds()
        assert seeds == ["W123", "W456", "W789"]
    
    @patch('ArticleCrawler.cli.ui.validators.validate_file_path')
    def test_get_seeds_invalid_path(self, mock_validate, provider, mock_prompter):
        mock_validate.return_value = (False, "File not found")
        mock_prompter.input.side_effect = ["/invalid/path", KeyboardInterrupt]
        with pytest.raises(KeyboardInterrupt):
            provider.get_seeds()
        mock_prompter.error.assert_called()
    
    def test_load_from_file_with_whitespace(self, provider, temp_dir):
        seed_file = temp_dir / "seeds.txt"
        seed_file.write_text("  W123  \n  W456  \n  W789  ")
        seeds = provider._load_from_file(seed_file)
        assert seeds == ["W123", "W456", "W789"]