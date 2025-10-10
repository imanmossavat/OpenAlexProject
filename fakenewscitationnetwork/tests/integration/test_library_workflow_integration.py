
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.library.paper_file_reader import PaperFileReader
from ArticleCrawler.library.models import LibraryConfig, PaperData


@pytest.mark.integration
class TestLibraryWorkflowIntegration:
    
    @pytest.fixture
    def library_manager(self, mock_logger):
        return LibraryManager(logger=mock_logger)
    
    @pytest.fixture
    def paper_reader(self, mock_logger):
        return PaperFileReader(logger=mock_logger)
    
    def test_create_and_read_library(self, library_manager, paper_reader, temp_dir):
        library_path = temp_dir / "workflow_library"
        
        library_manager.create_library_structure(library_path, "workflow_library")
        
        config = LibraryConfig(
            name="workflow_library",
            base_path=library_path,
            description="Integration test"
        )
        library_manager.save_library_config(config)
        
        papers_dir = library_manager.get_papers_directory(library_path)
        paper_content = """---
paper_id: W123
title: Test Paper
authors:
  - id: A123
    name: Test Author
year: 2024
abstract: Test abstract
---

# Test Paper
"""
        (papers_dir / "test_paper.md").write_text(paper_content)
        
        loaded_config = library_manager.load_library_config(library_path)
        assert loaded_config.name == "workflow_library"
        
        papers = paper_reader.read_papers_from_directory(papers_dir)
        assert len(papers) == 1
        assert papers[0].paper_id == "W123"
    
    def test_create_topic_folders_and_organize(self, library_manager, temp_dir):
        library_path = temp_dir / "organized_library"
        library_manager.create_library_structure(library_path, "organized_library")
        
        topic1_folder = library_manager.create_topic_folder(library_path, "Machine Learning")
        topic2_folder = library_manager.create_topic_folder(library_path, "Computer Vision")
        
        assert topic1_folder.exists()
        assert topic2_folder.exists()
        assert topic1_folder.parent.name == "topics"
        assert topic2_folder.parent.name == "topics"