import pytest
from pathlib import Path
from ArticleCrawler.utils.library_temp_manager import TempLibraryManager


class TestTempLibraryManager:
    
    @pytest.fixture
    def manager(self, mock_logger):
        return TempLibraryManager(mock_logger)
    
    def test_create_temp_library(self, manager):
        temp_path = manager.create_temp_library(prefix="test_")
        
        assert temp_path.exists()
        assert temp_path.is_dir()
        assert "test_" in temp_path.name
        
        manager.cleanup_temp_library(temp_path)
    
    def test_cleanup_temp_library(self, manager):
        temp_path = manager.create_temp_library()
        assert temp_path.exists()
        
        result = manager.cleanup_temp_library(temp_path)
        
        assert result is True
        assert not temp_path.exists()
    
    def test_cleanup_nonexistent_library(self, manager):
        fake_path = Path("/nonexistent/path")
        result = manager.cleanup_temp_library(fake_path)
        assert result is False
    
    def test_make_permanent(self, manager, temp_dir):
        temp_lib = manager.create_temp_library()
        permanent_path = temp_dir / "permanent_library"
        
        result = manager.make_permanent(temp_lib, permanent_path)
        
        assert result == permanent_path
        assert permanent_path.exists()
        assert not temp_lib.exists()
    
    def test_make_permanent_existing_path_raises(self, manager, temp_dir):
        temp_lib = manager.create_temp_library()
        permanent_path = temp_dir / "existing"
        permanent_path.mkdir()
        
        with pytest.raises(FileExistsError):
            manager.make_permanent(temp_lib, permanent_path)
        
        manager.cleanup_temp_library(temp_lib)