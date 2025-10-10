
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typer.testing import CliRunner
from ArticleCrawler.cli.main import app


@pytest.mark.unit
class TestLibraryCreateCommand:
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @patch('ArticleCrawler.cli.commands.library_create.Prompt.ask')
    @patch('ArticleCrawler.cli.commands.library_create.Confirm.ask')
    @patch('ArticleCrawler.cli.commands.library_create.RichPrompter')
    @patch('ArticleCrawler.cli.commands.library_create.LibraryCreationOrchestrator')
    @patch('ArticleCrawler.cli.commands.library_create._get_papers_from_sources')
    def test_library_create_success(self, mock_get_papers, mock_orchestrator, mock_prompter, 
                                    mock_confirm, mock_prompt, runner, temp_dir):
        mock_prompt.side_effect = ["test_library", str(temp_dir), "Test description"]
        mock_confirm.return_value = True
        mock_get_papers.return_value = ["W123", "W456"]
        
        mock_orch_instance = Mock()
        mock_config = Mock()
        mock_config.base_path = temp_dir
        mock_config.name = "test_library"
        mock_orch_instance.create_library.return_value = mock_config
        mock_orchestrator.return_value = mock_orch_instance
        
        result = runner.invoke(app, ["library-create"])
        
        assert result.exit_code == 0
    
    @patch('ArticleCrawler.cli.commands.library_create.Prompt.ask')
    @patch('ArticleCrawler.cli.commands.library_create._get_papers_from_sources')
    def test_library_create_validation_fails(self, mock_get_papers, mock_prompt, runner):
        mock_prompt.return_value = ""
        mock_get_papers.return_value = []
        
        result = runner.invoke(app, ["library-create"])
        
        assert result.exit_code == 0