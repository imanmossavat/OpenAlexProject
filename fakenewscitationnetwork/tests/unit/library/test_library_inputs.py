
import pytest
from pathlib import Path
from ArticleCrawler.cli.models.library_inputs import LibraryCreationInputs


@pytest.mark.unit
class TestLibraryCreationInputs:
    
    def test_creation_inputs_basic(self, temp_dir):
        inputs = LibraryCreationInputs(
            name="test_library",
            path=temp_dir,
            description="Test desc",
            paper_ids=["W123", "W456"],
            api_provider="openalex"
        )
        
        assert inputs.name == "test_library"
        assert inputs.path == temp_dir
        assert len(inputs.paper_ids) == 2
        assert inputs.api_provider == "openalex"
    
    def test_creation_inputs_with_description(self, temp_dir):
        inputs = LibraryCreationInputs(
            name="test",
            path=temp_dir,
            description="Test description",
            paper_ids=["W123"],
            api_provider="openalex"
        )
        
        assert inputs.description == "Test description"
    
    def test_creation_inputs_defaults(self, temp_dir):
        inputs = LibraryCreationInputs(
            name="test",
            path=temp_dir,
            description=None,
            paper_ids=["W123"],
            api_provider="openalex"
        )
        
        assert inputs.description is None