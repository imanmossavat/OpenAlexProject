import pytest
import pandas as pd
from ArticleCrawler.data.frame_manager import FrameManager, AcademicFeatureComputer


@pytest.mark.unit
class TestFrameManager:
    
    @pytest.fixture
    def frame_manager(self, sample_storage_config, mock_logger):
        return FrameManager(data_storage_options=sample_storage_config, logger=mock_logger)
    
    def test_initialization_creates_empty_dataframes(self, frame_manager):
        assert isinstance(frame_manager.df_paper_metadata, pd.DataFrame)
        assert len(frame_manager.df_paper_metadata) == 0
    
    def test_set_paper_id_seed_flag(self, frame_manager, sample_paper_metadata_df):
        frame_manager.df_paper_metadata = sample_paper_metadata_df.copy()
        seed_ids = ['W2134567890']
        frame_manager.set_paper_id_seed_flag(seed_ids)
        
        is_seed = frame_manager.df_paper_metadata[
            frame_manager.df_paper_metadata['paperId'] == 'W2134567890'
        ]['isSeed'].iloc[0]
        assert is_seed == True
    
    def test_set_key_author_flag(self, frame_manager, sample_paper_metadata_df):
        frame_manager.df_paper_metadata = sample_paper_metadata_df.copy()
        key_author_ids = ['W9876543210']
        frame_manager.set_key_author_flag(key_author_ids)
        
        is_key_author = frame_manager.df_paper_metadata[
            frame_manager.df_paper_metadata['paperId'] == 'W9876543210'
        ]['isKeyAuthor'].iloc[0]
        assert is_key_author == True
    
    def test_process_data_calls_parser_methods(self, frame_manager, sample_paper_object):
        frame_manager.process_data([sample_paper_object], processed=True)
        assert len(frame_manager.df_paper_metadata) > 0
    
    def test_update_failed_papers(self, frame_manager, sample_paper_metadata_df):
        frame_manager.df_paper_metadata = sample_paper_metadata_df.copy()
        failed_ids = ['W1111111111']
        frame_manager.update_failed_papers(failed_ids)
        
        processed_status = frame_manager.df_paper_metadata[
            frame_manager.df_paper_metadata['paperId'] == 'W1111111111'
        ]['processed'].iloc[0]
        assert processed_status == False
    
    def test_get_dataframes_shapes(self, frame_manager):
        shapes = frame_manager.get_dataframes_shapes()
        assert isinstance(shapes, pd.DataFrame)
        assert 'frame' in shapes.columns
    
    def test_get_num_processed_papers(self, frame_manager, sample_paper_metadata_df):
        frame_manager.df_paper_metadata = sample_paper_metadata_df.copy()
        n_processed, n_unprocessed = frame_manager.get_num_processed_papers()
        assert n_processed + n_unprocessed == len(sample_paper_metadata_df)
    
    def test_remove_unwanted_papers(self, frame_manager, sample_paper_metadata_df):
        frame_manager.df_paper_metadata = sample_paper_metadata_df.copy()
        unwanted = pd.DataFrame({'paperId': ['W1111111111']})
        initial_count = len(frame_manager.df_paper_metadata)
        frame_manager.remove_unwanted_papers(unwanted)
        assert len(frame_manager.df_paper_metadata) == initial_count - 1


@pytest.mark.unit
class TestAcademicFeatureComputer:
    
    @pytest.fixture
    def feature_computer(self):
        return AcademicFeatureComputer()
    
    def test_compute_paper_features_adds_has_abstract_column(
        self, feature_computer, sample_paper_metadata_df, sample_abstracts_df
    ):
        result = feature_computer.compute_paper_features(
            sample_paper_metadata_df.copy(), sample_abstracts_df.copy()
        )
        assert 'has_abstract' in result.columns
    
    def test_compute_paper_features_adds_is_preprint_column(
        self, feature_computer, sample_paper_metadata_df, sample_abstracts_df
    ):
        result = feature_computer.compute_paper_features(
            sample_paper_metadata_df.copy(), sample_abstracts_df.copy()
        )
        assert 'is_preprint' in result.columns
    
    def test_compute_author_features_adds_num_papers(self, feature_computer):
        df_paper_author = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'authorId': ['A1', 'A1', 'A2']
        })
        df_author = pd.DataFrame({'authorId': ['A1', 'A2'], 'authorName': ['Author 1', 'Author 2']})
        df_paper_metadata = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'year': [2024, 2023, 2022]
        })
        df_citations = pd.DataFrame({
            'paperId': ['W1', 'W2'],
            'referencePaperId': ['W3', 'W1']
        })
        
        result = feature_computer.compute_author_features(
            df_paper_author, df_author, df_paper_metadata, df_citations
        )
        assert 'num_papers' in result.columns
        assert result[result['authorId'] == 'A1']['num_papers'].iloc[0] == 2
    
    def test_compute_venue_features(self, feature_computer):
        df_paper_metadata = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'venue': ['Venue A', 'Venue B', 'Venue A']
        })
        df_citations = pd.DataFrame({
            'paperId': ['W1', 'W2'],
            'referencePaperId': ['W3', 'W1']
        })
        
        result = feature_computer.compute_venue_features(df_paper_metadata, df_citations)
        assert 'venue' in result.columns
        assert 'total_papers' in result.columns 
