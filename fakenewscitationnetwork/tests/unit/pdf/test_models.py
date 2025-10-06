import pytest
from pathlib import Path
from ArticleCrawler.pdf_processing.models import PDFMetadata, PDFProcessingResult, APIMatchResult


@pytest.mark.unit
class TestPDFMetadata:
    
    def test_initialization_full(self):
        metadata = PDFMetadata(
            filename="test.pdf",
            title="Test Title",
            doi="10.1234/test",
            year="2024",
            authors="John Doe",
            venue="Test Venue"
        )
        assert metadata.filename == "test.pdf"
        assert metadata.title == "Test Title"
        assert metadata.doi == "10.1234/test"
        assert metadata.year == "2024"
        assert metadata.authors == "John Doe"
        assert metadata.venue == "Test Venue"
    
    def test_initialization_minimal(self):
        metadata = PDFMetadata(filename="test.pdf")
        assert metadata.filename == "test.pdf"
        assert metadata.title is None
        assert metadata.doi is None
        assert metadata.year is None
        assert metadata.authors is None
        assert metadata.venue is None
    
    def test_is_valid_with_title(self):
        metadata = PDFMetadata(filename="test.pdf", title="Valid Title")
        assert metadata.is_valid() is True
    
    def test_is_valid_without_title(self):
        metadata = PDFMetadata(filename="test.pdf")
        assert metadata.is_valid() is False
    
    def test_to_dict(self):
        metadata = PDFMetadata(
            filename="test.pdf",
            title="Test Title",
            doi="10.1234/test"
        )
        result = metadata.to_dict()
        assert isinstance(result, dict)
        assert result['filename'] == "test.pdf"
        assert result['title'] == "Test Title"
        assert result['doi'] == "10.1234/test"
    
    def test_str_representation(self):
        metadata = PDFMetadata(
            filename="test.pdf",
            title="Test Title",
            authors="John Doe"
        )
        result = str(metadata)
        assert "test.pdf" in result
        assert "Test Title" in result
        assert "John Doe" in result


@pytest.mark.unit
class TestPDFProcessingResult:
    
    def test_initialization_success(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test")
        result = PDFProcessingResult(
            pdf_path=Path("test.pdf"),
            metadata=metadata,
            success=True
        )
        assert result.pdf_path == Path("test.pdf")
        assert result.metadata == metadata
        assert result.success is True
        assert result.error_message is None
    
    def test_initialization_failure(self):
        result = PDFProcessingResult(
            pdf_path=Path("test.pdf"),
            success=False,
            error_message="Processing failed"
        )
        assert result.pdf_path == Path("test.pdf")
        assert result.metadata is None
        assert result.success is False
        assert result.error_message == "Processing failed"
    
    def test_str_representation_success(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test Title")
        result = PDFProcessingResult(
            pdf_path=Path("test.pdf"),metadata=metadata,
            success=True
        )
        output = str(result)
        assert "Test Title" in output
    
    def test_str_representation_failure(self):
        result = PDFProcessingResult(
            pdf_path=Path("test.pdf"),
            success=False,
            error_message="Failed to process"
        )
        output = str(result)
        assert "test.pdf" in output
        assert "Failed to process" in output


@pytest.mark.unit
class TestAPIMatchResult:
    
    def test_initialization_matched(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test")
        result = APIMatchResult(
            metadata=metadata,
            matched=True,
            paper_id="W123456789",
            confidence=0.95,
            match_method="DOI"
        )
        assert result.metadata == metadata
        assert result.matched is True
        assert result.paper_id == "W123456789"
        assert result.confidence == 0.95
        assert result.match_method == "DOI"
    
    def test_initialization_not_matched(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test")
        result = APIMatchResult(metadata=metadata, matched=False)
        assert result.metadata == metadata
        assert result.matched is False
        assert result.paper_id is None
        assert result.confidence == 0.0
        assert result.match_method is None
    
    def test_str_representation_matched(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test")
        result = APIMatchResult(
            metadata=metadata,
            matched=True,
            paper_id="W123",
            confidence=0.95,
            match_method="DOI"
        )
        output = str(result)
        assert "Matched" in output
        assert "W123" in output
        assert "DOI" in output
    
    def test_str_representation_not_matched(self):
        metadata = PDFMetadata(filename="test.pdf", title="Test")
        result = APIMatchResult(metadata=metadata, matched=False)
        output = str(result)
        assert "Not found" in output
        assert "test.pdf" in output