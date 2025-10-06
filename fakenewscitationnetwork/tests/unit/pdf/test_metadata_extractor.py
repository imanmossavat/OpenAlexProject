import pytest
from unittest.mock import Mock
from ArticleCrawler.pdf_processing.metadata_extractor import PDFMetadataExtractor
from ArticleCrawler.pdf_processing.models import PDFMetadata


@pytest.mark.unit
class TestPDFMetadataExtractor:
    
    @pytest.fixture
    def extractor(self, mock_logger):
        return PDFMetadataExtractor(logger=mock_logger)
    
    @pytest.fixture
    def sample_xml_full(self):
        return """<?xml version="1.0"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Sample Research Paper Title</title>
                    </titleStmt>
                    <sourceDesc>
                        <biblStruct>
                            <analytic>
                                <author>
                                    <persName><surname>Doe</surname><forename>John</forename></persName>
                                </author>
                                <author>
                                    <persName><surname>Smith</surname><forename>Jane</forename></persName>
                                </author>
                                <idno type="DOI">10.1234/test.2024.001</idno>
                            </analytic>
                            <monogr>
                                <title level="j">Test Journal</title>
                                <imprint>
                                    <date type="published" when="2024">2024</date>
                                </imprint>
                            </monogr>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>
        """
    
    @pytest.fixture
    def sample_xml_minimal(self):
        return """<?xml version="1.0"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Basic Title Only</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
        </TEI>
        """
    
    def test_extract_full_metadata(self, extractor, sample_xml_full):
        result = extractor.extract(sample_xml_full, "test.pdf")
        assert result is not None
        assert result.filename == "test.pdf"
        assert result.title == "Sample Research Paper Title"
        assert "John Doe" in result.authors
        assert "Jane Smith" in result.authors
        assert result.doi == "10.1234/test.2024.001"
        assert result.venue == "Test Journal"
        assert result.year == "2024"
    
    def test_extract_minimal_metadata(self, extractor, sample_xml_minimal):
        result = extractor.extract(sample_xml_minimal, "minimal.pdf")
        assert result is not None
        assert result.filename == "minimal.pdf"
        assert result.title == "Basic Title Only"
        assert result.authors is None
        assert result.doi is None
        assert result.venue is None
        assert result.year is None
    
    def test_extract_invalid_xml(self, extractor, mock_logger):
        invalid_xml = "<invalid>not proper xml"
        result = extractor.extract(invalid_xml, "invalid.pdf")
        assert result is None
        mock_logger.error.assert_called()
    
    def test_extract_empty_xml(self, extractor):
        result = extractor.extract("", "empty.pdf")
        assert result is None
    
    def test_extract_no_title(self, extractor):
        xml_no_title = """<?xml version="1.0"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <sourceDesc>
                        <biblStruct>
                            <analytic>
                                <author>
                                    <persName><surname>Doe</surname></persName>
                                </author>
                            </analytic>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>
        """
        result = extractor.extract(xml_no_title, "notitle.pdf")
        assert result is not None
        assert result.title is None or result.title == ""