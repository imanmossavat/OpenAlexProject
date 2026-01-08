import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from ArticleCrawler.papervalidation.retraction_watch_manager import (
    RetractionWatchManager, RetractionWatchFetcher, RetractedPapersProcessing
)


@pytest.mark.unit
class TestRetractionWatchManager:
    
    @pytest.fixture
    def retraction_manager(self, sample_retraction_config, sample_storage_config, mock_logger):
        with patch('ArticleCrawler.papervalidation.retraction_watch_manager.RetractionWatchFetcher'):
            manager = RetractionWatchManager(
                retraction_options=sample_retraction_config,
                storage_and_logging_options=sample_storage_config,
                logger=mock_logger
            )
            manager.retraction_data = pd.DataFrame({
                'RetractionDOI': ['10.1234/ret1', '10.1234/ret2'],
                'OriginalPaperDOI': ['10.1234/orig1', '10.1234/orig2']
            })
            return manager
    
    def test_initialization_with_enabled_retraction_watch(self, retraction_manager):
        assert retraction_manager.retraction_options is not None
        assert hasattr(retraction_manager, 'retraction_data')
    
    def test_process_retracted_papers_returns_dataframes(self, retraction_manager):
        doi_list = ['10.1234/orig1', '10.1234/test']
        retracted_df, forbidden_df = retraction_manager.process_retracted_papers(doi_list)
        assert isinstance(retracted_df, pd.DataFrame)
        assert isinstance(forbidden_df, pd.DataFrame)


@pytest.mark.unit
class TestRetractedPapersProcessing:
    
    @pytest.fixture
    def processor(self, sample_retraction_config, mock_logger):
        return RetractedPapersProcessing(
            retraction_options=sample_retraction_config,
            logger=mock_logger
        )
    
    def test_get_retracted_papers_finds_matches(self, processor):
        retraction_data = pd.DataFrame({
            'RetractionDOI': ['10.1234/ret1'],
            'OriginalPaperDOI': ['10.1234/orig1']
        })
        doi_list = ['10.1234/orig1', '10.1234/other']
        
        result = processor.get_retracted_papers(retraction_data, doi_list)
        assert '10.1234/orig1' in result
    
    def test_get_retracted_papers_returns_none_for_empty_data(self, processor):
        result = processor.get_retracted_papers(None, ['10.1234/test'])
        assert result is None
    
    def test_process_retracted_papers_creates_forbidden_entries(self, processor):
        retraction_data = pd.DataFrame({
            'RetractionDOI': ['10.1234/ret1'],
            'OriginalPaperDOI': ['10.1234/orig1']
        })
        doi_list = ['10.1234/orig1']
        
        retracted_df, forbidden_df = processor.process_retracted_papers(retraction_data, doi_list)
        assert len(retracted_df) > 0
        assert len(forbidden_df) > 0 
