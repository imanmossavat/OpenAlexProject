import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.pdf_processing.grobid_client import GrobidClientWrapper


@pytest.mark.unit
class TestGrobidClientWrapper:
    
    @pytest.fixture
    def grobid_client(self, mock_logger):
        with patch('ArticleCrawler.pdf_processing.grobid_client.GrobidClient'):
            return GrobidClientWrapper(logger=mock_logger)
    
    @pytest.fixture
    def temp_pdf_files(self, temp_dir):
        pdf_dir = temp_dir / "pdfs"
        pdf_dir.mkdir()
        pdf1 = pdf_dir / "paper1.pdf"
        pdf2 = pdf_dir / "paper2.pdf"
        pdf1.write_bytes(b"fake pdf content 1")
        pdf2.write_bytes(b"fake pdf content 2")
        return [pdf1, pdf2]
    
    @patch('ArticleCrawler.pdf_processing.grobid_client.GrobidClient')
    def test_initialization_default(self, mock_grobid_class, mock_logger):
        client = GrobidClientWrapper(logger=mock_logger)
        assert client.server_url == "http://localhost:8070"
        assert client.logger == mock_logger
        mock_grobid_class.assert_called_once_with(grobid_server="http://localhost:8070")
    
    @patch('ArticleCrawler.pdf_processing.grobid_client.GrobidClient')
    def test_initialization_custom_url(self, mock_grobid_class, mock_logger):
        client = GrobidClientWrapper(server_url="http://custom:9000", logger=mock_logger)
        assert client.server_url == "http://custom:9000"
        mock_grobid_class.assert_called_once_with(grobid_server="http://custom:9000")
    
    def test_process_pdfs_empty_list(self, grobid_client):
        result = grobid_client.process_pdfs([])
        assert result == {}
    
    @patch('tempfile.TemporaryDirectory')
    def test_process_pdfs_grobid_error(self, mock_temp_dir, grobid_client, temp_pdf_files, mock_logger):
        temp_path = temp_pdf_files[0].parent.parent / "temp"
        temp_path.mkdir(exist_ok=True)
        mock_temp_dir.return_value.__enter__.return_value = str(temp_path)
        grobid_client.client.process.side_effect = Exception("GROBID failed")
        result = grobid_client.process_pdfs(temp_pdf_files)
        assert result == {}
        assert mock_logger.error.called
    
    def test_match_pdfs_to_xml_exact_match(self, grobid_client, temp_dir):
        xml_file1 = temp_dir / "paper1.tei.xml"
        xml_file2 = temp_dir / "paper2.tei.xml"
        xml_file1.touch()
        xml_file2.touch()
        pdf_filenames = ["paper1.pdf", "paper2.pdf"]
        xml_files = [xml_file1, xml_file2]
        result = grobid_client._match_pdfs_to_xml(pdf_filenames, xml_files)
        assert "paper1.pdf" in result
        assert "paper2.pdf" in result
        assert result["paper1.pdf"] == xml_file1
        assert result["paper2.pdf"] == xml_file2
    
    def test_match_pdfs_to_xml_partial_match(self, grobid_client, temp_dir):
        xml_file = temp_dir / "paper_long_name.tei.xml"
        xml_file.touch()
        pdf_filenames = ["paper.pdf"]
        xml_files = [xml_file]
        result = grobid_client._match_pdfs_to_xml(pdf_filenames, xml_files)
        assert "paper.pdf" in result
        assert result["paper.pdf"] == xml_file
    
    def test_match_pdfs_to_xml_no_match(self, grobid_client, temp_dir):
        xml_file = temp_dir / "different.tei.xml"
        xml_file.touch()
        pdf_filenames = ["paper.pdf"]
        xml_files = [xml_file]
        result = grobid_client._match_pdfs_to_xml(pdf_filenames, xml_files)
        assert len(result) == 0