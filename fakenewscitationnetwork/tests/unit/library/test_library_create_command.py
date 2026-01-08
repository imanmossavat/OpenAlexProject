import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from ArticleCrawler.cli.main import app


@pytest.mark.unit
class TestLibraryCreateCommand:
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @patch('ArticleCrawler.cli.commands.library_create._get_papers_from_sources')
    @patch('ArticleCrawler.cli.commands.library_create.LibraryCreationOrchestrator')
    @patch('ArticleCrawler.cli.commands.library_create.RichPrompter')
    @patch('rich.prompt.Confirm.ask')
    @patch('rich.prompt.Prompt.ask')
    def test_library_create_success(self, mock_prompt, mock_confirm, mock_prompter, 
                                    mock_orchestrator, mock_get_papers, runner, temp_dir):
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
    
    @patch('ArticleCrawler.cli.commands.library_create._get_papers_from_sources')
    @patch('ArticleCrawler.cli.commands.library_create.LibraryCreationOrchestrator')
    @patch('rich.prompt.Confirm.ask')
    @patch('rich.prompt.Prompt.ask')
    def test_library_create_validation_fails(self, mock_prompt, mock_confirm, 
                                            mock_orchestrator, mock_get_papers, runner):

        mock_prompt.side_effect = ["test_library", "/tmp/test", "Test description"]
        mock_confirm.return_value = False
        mock_get_papers.return_value = ["W123"]
        
        result = runner.invoke(app, ["library-create"])
        
        mock_orchestrator.return_value.create_library.assert_not_called()
        
    @patch('ArticleCrawler.cli.commands.library_create._get_papers_from_sources')
    @patch('ArticleCrawler.cli.commands.library_create.LibraryCreationOrchestrator')
    @patch('rich.prompt.Prompt.ask')
    def test_library_create_no_papers_found(self, mock_prompt, mock_orchestrator, 
                                           mock_get_papers, runner):
        mock_prompt.side_effect = ["test_library", "/tmp/test", "Test description"]
        mock_get_papers.return_value = []
        
        result = runner.invoke(app, ["library-create"])
        
        assert result.exit_code in [0, 1]
