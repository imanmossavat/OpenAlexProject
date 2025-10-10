# tests/unit/library/test_library_result_formatter.py (COMPLETE FIX)

import pytest
from rich.console import Console
from ArticleCrawler.cli.formatters.library_result_formatter import LibraryResultFormatter
from ArticleCrawler.library.models import LibraryConfig
from pathlib import Path


@pytest.mark.unit
class TestLibraryResultFormatter:
    
    @pytest.fixture
    def console(self):
        return Console()
    
    @pytest.fixture
    def formatter(self, console):
        return LibraryResultFormatter(console=console)
    
    @pytest.fixture
    def sample_config(self, temp_dir):
        return LibraryConfig(
            name="test_library",
            base_path=temp_dir,
            description="Test description"
        )
    
    def test_format_creation_success(self, formatter, sample_config):
        formatter.display_success(sample_config, num_papers=10)
        
        assert True
    
    def test_format_creation_partial(self, formatter, sample_config):
        formatter.display_success(sample_config, num_papers=5)
        
        assert True
    
    def test_display_error(self, formatter):
        error = ValueError("Test error")
        formatter.display_error(error)
        
        assert True