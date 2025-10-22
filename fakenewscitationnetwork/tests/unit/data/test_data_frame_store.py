import pytest
import pandas as pd
import numpy as np
from ArticleCrawler.data.data_frame_store import DataFrameStore


@pytest.mark.unit
class TestDataFrameStore:
    
    def test_initialization_creates_empty_dataframes(self, mock_logger):
        store = DataFrameStore(logger=mock_logger)
        assert isinstance(store.df_paper_metadata, pd.DataFrame)
        assert isinstance(store.df_abstract, pd.DataFrame)
        assert len(store.df_paper_metadata) == 0
        assert len(store.df_abstract) == 0
    
    def test_paper_metadata_has_correct_columns(self, empty_data_frame_store):
        expected_columns = [
            'paperId', 'doi', 'venue', 'year', 'title',
            'processed', 'isSeed', 'isKeyAuthor', 'selected', 'retracted'
        ]
        assert all(col in empty_data_frame_store.df_paper_metadata.columns for col in expected_columns)
    
    def test_get_dataframes_shapes(self, populated_data_frame_store):
        shapes_df = populated_data_frame_store.get_dataframes_shapes()
        assert isinstance(shapes_df, pd.DataFrame)
        assert 'frame' in shapes_df.columns
        assert 'shape' in shapes_df.columns
        assert len(shapes_df) > 0
    
    def test_get_num_processed_papers(self, populated_data_frame_store):
        n_processed, n_unprocessed = populated_data_frame_store.get_num_processed_papers()
        assert isinstance(n_processed, (int, np.integer))
        assert isinstance(n_unprocessed, (int, np.integer))
        assert n_processed + n_unprocessed == len(populated_data_frame_store.df_paper_metadata)
    
    def test_dataframes_are_independent(self, mock_logger):
        store1 = DataFrameStore(logger=mock_logger)
        store2 = DataFrameStore(logger=mock_logger)
        
        store1.df_paper_metadata = pd.DataFrame({'paperId': ['W1']})
        assert len(store1.df_paper_metadata) == 1
        assert len(store2.df_paper_metadata) == 0