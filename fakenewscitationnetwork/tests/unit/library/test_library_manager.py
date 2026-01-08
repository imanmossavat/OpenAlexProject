
import pytest
from pathlib import Path
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.library.models import LibraryConfig


@pytest.mark.unit
class TestLibraryManager:
    
    @pytest.fixture
    def library_manager(self, mock_logger):
        return LibraryManager(logger=mock_logger)
    
    def test_create_library_structure(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        
        library_manager.create_library_structure(library_path, "test_library")
        
        assert library_path.exists()
        assert (library_path / "papers").exists()
    
    def test_save_library_config(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        library_path.mkdir()
        
        config = LibraryConfig(
            name="test_library",
            base_path=library_path,
            description="Test"
        )
        
        library_manager.save_library_config(config)
        
        config_file = library_path / "library_config.yaml"
        assert config_file.exists()
    
    def test_load_library_config(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        library_path.mkdir()
        
        config = LibraryConfig(
            name="test_library",
            base_path=library_path
        )
        library_manager.save_library_config(config)
        
        loaded_config = library_manager.load_library_config(library_path)
        
        assert loaded_config.name == config.name
    
    def test_library_exists(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        library_path.mkdir()
        
        config = LibraryConfig(name="test", base_path=library_path)
        library_manager.save_library_config(config)
        
        assert library_manager.library_exists(library_path) is True
        assert library_manager.library_exists(temp_dir / "nonexistent") is False
    
    def test_get_papers_directory(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        
        papers_dir = library_manager.get_papers_directory(library_path)
        
        assert papers_dir == library_path / "papers"
    
    def test_create_topic_folder(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        library_manager.create_library_structure(library_path, "test_library")
        
        topic_folder = library_manager.create_topic_folder(
            library_path=library_path,
            topic_label="Machine Learning"
        )
        
        assert topic_folder.exists()
        assert topic_folder.name == "Machine Learning"
        assert topic_folder.parent.name == "topics"
    
    def test_create_topic_folder_sanitizes_name(self, library_manager, temp_dir):
        library_path = temp_dir / "test_library"
        library_manager.create_library_structure(library_path, "test_library")
        
        topic_folder = library_manager.create_topic_folder(
            library_path=library_path,
            topic_label="Invalid/Name:With*Special?Chars"
        )
        
        assert topic_folder.exists()
        assert "/" not in topic_folder.name
        assert ":" not in topic_folder.name