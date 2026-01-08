import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from ArticleCrawler.sampling.sampler import Sampler


@pytest.mark.unit
class TestSampler:
    
    @pytest.fixture
    def sampler(
        self,
        sample_keywords,
        mock_frame_manager,
        sample_sampling_config,
        sample_storage_config,
        mock_logger
    ):
        mock_data_coordinator = Mock()
        mock_data_coordinator.frames = mock_frame_manager
        mock_data_coordinator.graph = Mock()
        mock_data_coordinator.graph.get_paper_centralities = Mock(
            return_value=pd.DataFrame({
                'paperId': ['W1', 'W2', 'W3'],
                'centrality (in)': [0.5, 0.3, 0.7],
                'centrality (out)': [0.4, 0.6, 0.2]
            })
        )
        mock_data_coordinator.update_graph_and_calculate_centrality = Mock()
        
        return Sampler(
            keywords=sample_keywords,
            data_manager=mock_data_coordinator,
            sampling_options=sample_sampling_config,
            logger=mock_logger,
            data_storage_options=sample_storage_config
        )
    
    def test_initialization(self, sampler):
        assert sampler.num_papers == 5
        assert sampler.keywords is not None
        assert sampler.sampled_papers == []
    
    def test_calculate_centrality_threshold_returns_thresholds(self, sampler):
        sampler.potential_future_sample_ids = pd.Series(['W1', 'W2', 'W3'])
        
        sampler.data_coordinator.graph.get_paper_centralities.return_value = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'centrality (in)': [0.5, 0.3, 0.7],
            'centrality (out)': [0.4, 0.6, 0.2]
        })
        
        thresholds = sampler.calculate_centrality_threshold()
        assert isinstance(thresholds, list)
        assert len(thresholds) > 0
    
    def test_prepare_initial_sample_excludes_selected_papers(self, sampler, sample_paper_metadata_df):
        sampler.data_coordinator.frames.df_paper_metadata = sample_paper_metadata_df.copy()
        sampler.data_coordinator.frames.df_forbidden_entries = pd.DataFrame(columns=['paperId', 'sampler'])
        sampler.prepare_initial_sample()
        
        assert 'W2134567890' not in sampler.potential_future_sample_ids.values
    
    def test_normalize_probabilities_sums_to_one(self, sampler):
        probabilities = np.array([0.1, 0.2, 0.3, 0.4])
        normalized = sampler.normalize_probabilities(probabilities)
        assert np.isclose(np.sum(normalized), 1.0)
    
    def test_normalize_probabilities_handles_negative_values(self, sampler):
        probabilities = np.array([0.1, -0.2, 0.3])
        normalized = sampler.normalize_probabilities(probabilities)
        assert np.all(normalized >= 0)
        assert np.isclose(np.sum(normalized), 1.0)
    
    def test_compute_year_probability(self, sampler):
        years = pd.Series([2024, 2023, 2020, 2015])
        probabilities = sampler._compute_year_probability(years)
        assert len(probabilities) == len(years)
        assert np.all(probabilities > 0)
    
    def test_filter_papers_by_venues(self, sampler, sample_paper_metadata_df):
        sampler.data_coordinator.frames.df_paper_metadata = sample_paper_metadata_df.copy()
        sampler.potential_future_sample_ids = sample_paper_metadata_df['paperId']
        sampler._filter_papers_by_venues()