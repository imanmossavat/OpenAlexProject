import pytest
from pathlib import Path
from ArticleCrawler.cli.ui.validators import validate_paper_id, validate_file_path, validate_experiment_name


@pytest.mark.unit
class TestValidatePaperId:
    
    def test_valid_openalex_id(self):
        assert validate_paper_id("W2134567890") is True
        assert validate_paper_id("W123") is True
    
    def test_valid_semantic_scholar_id(self):
        assert validate_paper_id("1234567890abcdef12345678") is True
        assert validate_paper_id("a1b2c3d4e5f67890abcdef1234567890abcdef12") is True
    
    def test_valid_doi_full_url(self):
        assert validate_paper_id("https://doi.org/10.1234/test.2024.001") is True
        assert validate_paper_id("http://doi.org/10.5678/paper") is True
    
    def test_valid_doi_short_form(self):
        assert validate_paper_id("10.1234/test.2024.001") is True
        assert validate_paper_id("10.5678/paper") is True
    
    def test_invalid_empty(self):
        assert validate_paper_id("") is False
        assert validate_paper_id("   ") is False
        assert validate_paper_id(None) is False
    
    def test_invalid_format(self):
        assert validate_paper_id("invalid_id") is False
        assert validate_paper_id("123456") is False
        assert validate_paper_id("X123456789") is False


@pytest.mark.unit
class TestValidateFilePath:
    
    def test_valid_file_path(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        is_valid, error_msg = validate_file_path(str(test_file))
        assert is_valid is True
        assert error_msg == ""
    
    def test_invalid_empty_path(self):
        is_valid, error_msg = validate_file_path("")
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_invalid_nonexistent_file(self):
        is_valid, error_msg = validate_file_path("/path/to/nonexistent/file.txt")
        assert is_valid is False
        assert "does not exist" in error_msg.lower()
    
    def test_invalid_directory_instead_of_file(self, temp_dir):
        is_valid, error_msg = validate_file_path(str(temp_dir))
        assert is_valid is False
        assert "not a file" in error_msg.lower()
    
    def test_expanduser_tilde(self, temp_dir):
        is_valid, error_msg = validate_file_path("~/nonexistent.txt")
        assert is_valid is False
        assert "does not exist" in error_msg.lower()


@pytest.mark.unit
class TestValidateExperimentName:
    
    def test_valid_name_alphanumeric(self):
        is_valid, error_msg = validate_experiment_name("MyExperiment123")
        assert is_valid is True
        assert error_msg == ""
    
    def test_valid_name_with_spaces(self):
        is_valid, error_msg = validate_experiment_name("My Experiment 2024")
        assert is_valid is True
    
    def test_valid_name_with_hyphens_underscores(self):
        is_valid, error_msg = validate_experiment_name("my-experiment_v2")
        assert is_valid is True
    
    def test_invalid_empty_name(self):
        is_valid, error_msg = validate_experiment_name("")
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_invalid_whitespace_only(self):
        is_valid, error_msg = validate_experiment_name("   ")
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_invalid_special_characters(self):
        is_valid, error_msg = validate_experiment_name("my@experiment!")
        assert is_valid is False
        assert "letters" in error_msg.lower() or "characters" in error_msg.lower()
    
    def test_invalid_too_long(self):
        long_name = "a" * 101
        is_valid, error_msg = validate_experiment_name(long_name)
        assert is_valid is False
        assert "long" in error_msg.lower()