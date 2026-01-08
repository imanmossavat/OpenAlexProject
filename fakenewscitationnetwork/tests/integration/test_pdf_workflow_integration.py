import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from ArticleCrawler.cli.ui.pdf_workflow import PDFSeedWorkflow
from ArticleCrawler.pdf_processing import PDFProcessor
from ArticleCrawler.pdf_processing.models import PDFMetadata, PDFProcessingResult, APIMatchResult


@pytest.mark.integration
class TestPDFSeedWorkflowIntegration:
    
    @pytest.fixture
    def mock_components(self, mock_prompter, mock_rich_console):
        file_selector = Mock()
        metadata_reviewer = Mock()
        results_presenter = Mock()
        pdf_processor = Mock()
        return {
            'prompter': mock_prompter,
            'file_selector': file_selector,
            'metadata_reviewer': metadata_reviewer,
            'results_presenter': results_presenter,
            'pdf_processor': pdf_processor,
            'console': mock_rich_console
        }
    
    @pytest.fixture
    def workflow(self, mock_components):
        return PDFSeedWorkflow(
            prompter=mock_components['prompter'],
            api_provider_type='openalex',
            pdf_processor=mock_components['pdf_processor'],
            file_selector=mock_components['file_selector'],
            metadata_reviewer=mock_components['metadata_reviewer'],
            results_presenter=mock_components['results_presenter']
        )
    
    def test_execute_full_workflow_success(self, workflow, mock_components, temp_dir):
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()
        mock_components['file_selector'].select_files.return_value = [pdf_path]
        metadata = PDFMetadata(filename="test.pdf", title="Test Paper", doi="10.1234/test")
        processing_result = PDFProcessingResult(pdf_path=pdf_path, metadata=metadata, success=True)
        mock_components['pdf_processor'].process_pdfs.return_value = [processing_result]
        mock_components['metadata_reviewer'].review_and_edit.return_value = [metadata]
        match_result = APIMatchResult(metadata=metadata, matched=True, paper_id="W123", confidence=0.95, match_method="DOI")
        with patch.object(workflow, '_match_with_api', return_value=[match_result]):
            mock_components['results_presenter'].show_and_confirm.return_value = ["W123"]
            paper_ids = workflow.execute()
            assert paper_ids == ["W123"]
            mock_components['file_selector'].select_files.assert_called_once()
            mock_components['pdf_processor'].process_pdfs.assert_called_once_with([pdf_path])
            mock_components['metadata_reviewer'].review_and_edit.assert_called_once()
            mock_components['results_presenter'].show_and_confirm.assert_called_once()
    
    def test_execute_no_files_selected(self, workflow, mock_components):
        mock_components['file_selector'].select_files.return_value = []
        paper_ids = workflow.execute()
        assert paper_ids == []
        mock_components['pdf_processor'].process_pdfs.assert_not_called()
    
    def test_execute_no_valid_metadata(self, workflow, mock_components, temp_dir):
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()
        mock_components['file_selector'].select_files.return_value = [pdf_path]
        processing_result = PDFProcessingResult(pdf_path=pdf_path, success=False, error_message="Failed")
        mock_components['pdf_processor'].process_pdfs.return_value = [processing_result]
        mock_components['metadata_reviewer'].review_and_edit.return_value = []
        paper_ids = workflow.execute()
        assert paper_ids == []
        mock_components['results_presenter'].show_and_confirm.assert_not_called()
    
    def test_execute_no_matches_found(self, workflow, mock_components, temp_dir):
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()
        mock_components['file_selector'].select_files.return_value = [pdf_path]
        metadata = PDFMetadata(filename="test.pdf", title="Test Paper")
        processing_result = PDFProcessingResult(pdf_path=pdf_path, metadata=metadata, success=True)
        mock_components['pdf_processor'].process_pdfs.return_value = [processing_result]
        mock_components['metadata_reviewer'].review_and_edit.return_value = [metadata]
        match_result = APIMatchResult(metadata=metadata, matched=False)
        with patch.object(workflow, '_match_with_api', return_value=[match_result]):
            mock_components['results_presenter'].show_and_confirm.return_value = []
            paper_ids = workflow.execute()
            assert paper_ids == []
    
    @patch('ArticleCrawler.cli.ui.pdf_workflow.pyalex')
    @patch('ArticleCrawler.cli.ui.pdf_workflow.load_dotenv')
    @patch('os.getenv')
    def test_configure_openalex_with_email(self, mock_getenv, mock_load_dotenv, mock_pyalex, workflow):
        mock_getenv.return_value = "test@example.com"
        workflow._configure_openalex()
        mock_load_dotenv.assert_called_once()
        assert mock_pyalex.config.email == "test@example.com"
    
    @patch('ArticleCrawler.cli.ui.pdf_workflow.pyalex')
    @patch('ArticleCrawler.cli.ui.pdf_workflow.load_dotenv')
    @patch('os.getenv')
    def test_configure_openalex_without_email(self, mock_getenv, mock_load_dotenv, mock_pyalex, workflow):
        mock_getenv.return_value = None
        workflow._configure_openalex()
        mock_load_dotenv.assert_called_once()