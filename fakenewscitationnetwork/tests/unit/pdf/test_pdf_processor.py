import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from ArticleCrawler.pdf_processing.pdf_processor import PDFProcessor
from ArticleCrawler.pdf_processing.models import PDFMetadata, PDFProcessingResult


@pytest.mark.unit
class TestPDFProcessor:
    
    @pytest.fixture
    def mock_docker_manager(self):
        manager = Mock()
        manager.is_grobid_running.return_value = True
        manager.start_container.return_value = True
        return manager
    
    @pytest.fixture
    def mock_grobid_client(self):
        return Mock()
    
    @pytest.fixture
    def mock_metadata_extractor(self):
        return Mock()
    
    @pytest.fixture
    def pdf_processor(self, mock_docker_manager, mock_grobid_client, mock_metadata_extractor, mock_logger):
        return PDFProcessor(
            docker_manager=mock_docker_manager,
            grobid_client=mock_grobid_client,
            metadata_extractor=mock_metadata_extractor,
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_pdf_paths(self, temp_dir):
        pdf1 = temp_dir / "paper1.pdf"
        pdf2 = temp_dir / "paper2.pdf"
        pdf1.touch()
        pdf2.touch()
        return [pdf1, pdf2]
    
    def test_initialization_with_defaults(self, mock_logger):
        processor = PDFProcessor(logger=mock_logger)
        assert processor.logger == mock_logger
        assert processor.docker_manager is not None
        assert processor.grobid_client is not None
        assert processor.metadata_extractor is not None
    
    def test_initialization_with_custom_components(self, mock_docker_manager, mock_grobid_client, mock_metadata_extractor, mock_logger):
        processor = PDFProcessor(
            docker_manager=mock_docker_manager,
            grobid_client=mock_grobid_client,
            metadata_extractor=mock_metadata_extractor,
            logger=mock_logger
        )
        assert processor.docker_manager == mock_docker_manager
        assert processor.grobid_client == mock_grobid_client
        assert processor.metadata_extractor == mock_metadata_extractor
    
    def test_ensure_grobid_running_already_running(self, pdf_processor, mock_docker_manager):
        mock_docker_manager.is_grobid_running.return_value = True
        result = pdf_processor.ensure_grobid_running()
        assert result is True
        mock_docker_manager.start_container.assert_not_called()
    
    def test_ensure_grobid_running_needs_start(self, pdf_processor, mock_docker_manager, mock_logger):
        mock_docker_manager.is_grobid_running.return_value = False
        result = pdf_processor.ensure_grobid_running()
        assert result is False
        mock_logger.error.assert_called()
        mock_docker_manager.start_container.assert_not_called()
    
    def test_ensure_grobid_running_fails_to_start(self, pdf_processor, mock_docker_manager):
        mock_docker_manager.is_grobid_running.return_value = False
        mock_docker_manager.start_container.return_value = False
        result = pdf_processor.ensure_grobid_running()
        assert result is False
    
    def test_process_pdfs_empty_list(self, pdf_processor):
        results = pdf_processor.process_pdfs([])
        assert results == []
    
    def test_process_pdfs_grobid_unavailable(self, pdf_processor, sample_pdf_paths, mock_docker_manager, mock_logger):
        mock_docker_manager.is_grobid_running.return_value = False
        mock_docker_manager.start_container.return_value = False
        results = pdf_processor.process_pdfs(sample_pdf_paths)
        assert len(results) == 2
        assert all(not r.success for r in results)
        assert all(r.error_message == "GROBID service unavailable" for r in results)
        mock_logger.error.assert_called()
    
    def test_process_pdfs_success(self, pdf_processor, sample_pdf_paths, mock_grobid_client, mock_metadata_extractor):
        mock_grobid_client.process_pdfs.return_value = {
            sample_pdf_paths[0]: "<xml>content1</xml>",
            sample_pdf_paths[1]: "<xml>content2</xml>"
        }
        metadata1 = PDFMetadata(filename="paper1.pdf", title="Paper 1")
        metadata2 = PDFMetadata(filename="paper2.pdf", title="Paper 2")
        mock_metadata_extractor.extract.side_effect = [metadata1, metadata2]
        results = pdf_processor.process_pdfs(sample_pdf_paths)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].metadata.title == "Paper 1"
        assert results[1].metadata.title == "Paper 2"
    
    def test_process_pdfs_grobid_fails_one_pdf(self, pdf_processor, sample_pdf_paths, mock_grobid_client, mock_metadata_extractor):
        mock_grobid_client.process_pdfs.return_value = {
            sample_pdf_paths[0]: "<xml>content1</xml>"
        }
        metadata1 = PDFMetadata(filename="paper1.pdf", title="Paper 1")
        mock_metadata_extractor.extract.return_value = metadata1
        results = pdf_processor.process_pdfs(sample_pdf_paths)
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert results[1].error_message == "GROBID did not produce XML output"
    
    def test_process_pdfs_metadata_extraction_fails(self, pdf_processor, sample_pdf_paths, mock_grobid_client, mock_metadata_extractor):
        mock_grobid_client.process_pdfs.return_value = {
            sample_pdf_paths[0]: "<xml>content1</xml>",
            sample_pdf_paths[1]: "<xml>content2</xml>"
        }
        mock_metadata_extractor.extract.side_effect = [None, PDFMetadata(filename="paper2.pdf", title="Paper 2")]
        results = pdf_processor.process_pdfs(sample_pdf_paths)
        assert len(results) == 2
        assert results[0].success is False
        assert results[0].error_message == "Failed to extract metadata from XML"
        assert results[1].success is True