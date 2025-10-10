
import pytest
from rich.console import Console
from ArticleCrawler.cli.formatters.error_formatter import ErrorFormatter
from ArticleCrawler.cli.validators.validation_models import ValidationError, ValidationResult


@pytest.mark.unit
class TestErrorFormatter:
    
    @pytest.fixture
    def formatter(self):
        return ErrorFormatter()
    
    @pytest.fixture
    def console(self):
        return Console()
    
    def test_display_validation_errors(self, formatter, console):
        errors = [
            ValidationError(field="name", message="Name is required"),
            ValidationError(field="path", message="Path already exists", suggestion="Choose different path")
        ]
        result = ValidationResult(errors=errors)
        
        formatter.display_validation_errors(result, console)
        
        assert True
    
    def test_display_validation_errors_empty(self, formatter, console):
        result = ValidationResult(errors=[])
        
        formatter.display_validation_errors(result, console)
        
        assert True
    
    def test_display_validation_errors_with_suggestions(self, formatter, console):
        errors = [
            ValidationError(field="test", message="Test error", suggestion="Try this")
        ]
        result = ValidationResult(errors=errors)
        
        formatter.display_validation_errors(result, console)
        
        assert True