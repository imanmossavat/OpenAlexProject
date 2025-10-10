
import pytest
from pathlib import Path
from ArticleCrawler.cli.validators.library_validator import LibraryValidator
from ArticleCrawler.cli.models.library_inputs import LibraryCreationInputs
from ArticleCrawler.cli.models.topic_modeling_inputs import TopicModelingInputs


@pytest.mark.unit
class TestLibraryValidator:
    
    @pytest.fixture
    def validator(self, mock_logger):
        return LibraryValidator(logger=mock_logger)
    
    @pytest.fixture
    def valid_creation_inputs(self, temp_dir):
        return LibraryCreationInputs(
            name="test_library",
            path=temp_dir / "new_library",
            description="Test description",
            paper_ids=["W123", "W456"],
            api_provider="openalex"
        )
    
    def test_validate_creation_success(self, validator, valid_creation_inputs):
        result = validator.validate_creation(valid_creation_inputs)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_creation_empty_name(self, validator, temp_dir):
        inputs = LibraryCreationInputs(
            name="",
            path=temp_dir,
            description="Test",
            paper_ids=["W123"],
            api_provider="openalex"
        )
        
        result = validator.validate_creation(inputs)
        
        assert not result.is_valid
        assert any(e.field == "name" for e in result.errors)
    
    def test_validate_creation_library_exists(self, validator, temp_dir):
        library_path = temp_dir / "existing"
        library_path.mkdir()
        (library_path / "library_config.yaml").touch()
        
        inputs = LibraryCreationInputs(
            name="test",
            path=library_path,
            description="Test",
            paper_ids=["W123"],
            api_provider="openalex"
        )
        
        result = validator.validate_creation(inputs)
        
        assert not result.is_valid
        assert any(e.field == "path" for e in result.errors)
    
    def test_validate_creation_no_papers(self, validator, temp_dir):
        inputs = LibraryCreationInputs(
            name="test",
            path=temp_dir,
            description="Test",
            paper_ids=[],
            api_provider="openalex"
        )
        
        result = validator.validate_creation(inputs)
        
        assert not result.is_valid
        assert any(e.field == "paper_ids" for e in result.errors)
    
    def test_validate_creation_invalid_provider(self, validator, temp_dir):
        inputs = LibraryCreationInputs(
            name="test",
            path=temp_dir,
            description="Test",
            paper_ids=["W123"],
            api_provider="invalid_provider"
        )
        
        result = validator.validate_creation(inputs)
        
        assert not result.is_valid
        assert any(e.field == "api_provider" for e in result.errors)
    
    def test_validate_topic_modeling_success(self, validator, temp_dir):
        library_path = temp_dir / "library"
        library_path.mkdir()
        (library_path / "library_config.yaml").touch()
        
        inputs = TopicModelingInputs(
            library_path=library_path,
            model_type="NMF",
            num_topics=5
        )
        
        result = validator.validate_topic_modeling(inputs)
        
        assert result.is_valid
    
    def test_validate_topic_modeling_library_not_found(self, validator, temp_dir):
        inputs = TopicModelingInputs(
            library_path=temp_dir / "nonexistent",
            model_type="NMF",
            num_topics=5
        )
        
        result = validator.validate_topic_modeling(inputs)
        
        assert not result.is_valid
    
    def test_validate_topic_modeling_invalid_model_type(self, validator, temp_dir):
        library_path = temp_dir / "library"
        library_path.mkdir()
        (library_path / "library_config.yaml").touch()
        
        inputs = TopicModelingInputs(
            library_path=library_path,
            model_type="INVALID",
            num_topics=5
        )
        
        result = validator.validate_topic_modeling(inputs)
        
        assert not result.is_valid