import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.cli.ui.prompts import RichPrompter, SimplePrompter
from rich.console import Console


@pytest.mark.unit
class TestRichPrompter:
    
    @pytest.fixture
    def console(self):
        return Console()
    
    @pytest.fixture
    def prompter(self, console):
        return RichPrompter(console)
    
    def test_initialization(self, prompter, console):
        assert prompter.console == console
        assert prompter.style is not None
    
    @patch('questionary.text')
    def test_input(self, mock_text, prompter):
        mock_text.return_value.ask.return_value = "user input"
        result = prompter.input("Enter value")
        assert result == "user input"
        mock_text.assert_called_once()
    
    @patch('questionary.text')
    def test_input_with_default(self, mock_text, prompter):
        mock_text.return_value.ask.return_value = ""
        result = prompter.input("Enter value", default="default_value")
        assert result == ""
    
    @patch('questionary.text')
    def test_input_cancelled(self, mock_text, prompter):
        mock_text.return_value.ask.return_value = None
        result = prompter.input("Enter value", default="default")
        assert result == ""
    
    @patch('questionary.text')
    def test_input_int_valid(self, mock_text, prompter):
        mock_text.return_value.ask.return_value = "42"
        result = prompter.input_int("Enter number", default=0)
        assert result == 42
    
    @patch('questionary.text')
    def test_input_int_with_min_max(self, mock_text, prompter):
        mock_text.return_value.ask.side_effect = ["5", "25", "15"]
        result = prompter.input_int("Enter number", default=10, min_value=10, max_value=20)
        assert result == 15
    
    @patch('questionary.confirm')
    def test_confirm_true(self, mock_confirm, prompter):
        mock_confirm.return_value.ask.return_value = True
        result = prompter.confirm("Continue?")
        assert result is True
    
    @patch('questionary.confirm')
    def test_confirm_false(self, mock_confirm, prompter):
        mock_confirm.return_value.ask.return_value = False
        result = prompter.confirm("Continue?")
        assert result is False
    
    @patch('questionary.confirm')
    def test_confirm_default(self, mock_confirm, prompter):
        mock_confirm.return_value.ask.return_value = None
        result = prompter.confirm("Continue?", default=True)
        assert result is True
    
    @patch('questionary.select')
    def test_choice(self, mock_select, prompter):
        mock_select.return_value.ask.return_value = "Option 2"
        choices = ["Option 1", "Option 2", "Option 3"]
        result = prompter.choice("Select option", choices)
        assert result == 1
    
    @patch('questionary.select')
    def test_choice_cancelled(self, mock_select, prompter):
        mock_select.return_value.ask.return_value = None
        choices = ["Option 1", "Option 2"]
        result = prompter.choice("Select option", choices, default=1)
        assert result == 1


@pytest.mark.unit
class TestSimplePrompter:
    
    @pytest.fixture
    def prompter(self):
        return SimplePrompter()
    
    @patch('builtins.input')
    def test_input(self, mock_input, prompter):
        mock_input.return_value = "user response"
        result = prompter.input("Enter value")
        assert result == "user response"
    
    @patch('builtins.input')
    def test_input_with_default_empty(self, mock_input, prompter):
        mock_input.return_value = ""
        result = prompter.input("Enter value", default="default")
        assert result == "default"
    
    @patch('builtins.input')
    def test_input_int_valid(self, mock_input, prompter):
        mock_input.return_value = "42"
        result = prompter.input_int("Enter number")
        assert result == 42
    
    @patch('builtins.input')
    def test_input_int_invalid_then_valid(self, mock_input, prompter):
        mock_input.side_effect = ["invalid", "42"]
        result = prompter.input_int("Enter number")
        assert result == 42
    
    @patch('builtins.input')
    def test_confirm_yes(self, mock_input, prompter):
        mock_input.return_value = "y"
        result = prompter.confirm("Continue?")
        assert result is True
    
    @patch('builtins.input')
    def test_confirm_no(self, mock_input, prompter):
        mock_input.return_value = "n"
        result = prompter.confirm("Continue?")
        assert result is False
    
    @patch('builtins.input')
    def test_confirm_default(self, mock_input, prompter):
        mock_input.return_value = ""
        result = prompter.confirm("Continue?", default=True)
        assert result is True
    
    @patch('builtins.input')
    def test_choice(self, mock_input, prompter):
        mock_input.return_value = "2"
        choices = ["Option 1", "Option 2", "Option 3"]
        result = prompter.choice("Select", choices)
        assert result == 1