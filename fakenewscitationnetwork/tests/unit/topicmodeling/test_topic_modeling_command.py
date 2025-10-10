
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typer.testing import CliRunner
from ArticleCrawler.cli.main import app


@pytest.mark.unit
class TestTopicModelingCommand:
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.Prompt.ask')
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.Confirm.ask')
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.questionary.select')
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.TopicModelingOrchestrator')
    def test_topic_modeling_success(self, mock_orchestrator, mock_select, mock_confirm, mock_prompt, runner, temp_dir):
        library_path = temp_dir / "library"
        library_path.mkdir()
        (library_path / "library_config.yaml").touch()
        
        mock_select_instance = Mock()
        mock_select_instance.ask.side_effect = ["existing", "NMF"]
        mock_select.return_value = mock_select_instance
        
        mock_prompt.side_effect = [str(library_path), "5"]
        mock_confirm.return_value = True
        
        mock_orch_instance = Mock()
        mock_orch_instance.run_topic_modeling.return_value = []
        mock_orchestrator.return_value = mock_orch_instance
        
        result = runner.invoke(app, ["topic-modeling"])
        
        assert result.exit_code == 0
    
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.questionary.select')
    @patch('ArticleCrawler.cli.commands.topic_modeling_cmd.Prompt.ask')
    def test_topic_modeling_validation_fails(self, mock_prompt, mock_select, runner, temp_dir):
        mock_select_instance = Mock()
        mock_select_instance.ask.return_value = "existing"
        mock_select.return_value = mock_select_instance
        
        mock_prompt.return_value = str(temp_dir / "nonexistent")
        
        result = runner.invoke(app, ["topic-modeling"])
        
        assert result.exit_code == 0