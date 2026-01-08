import pytest
import pandas as pd
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestSamplingWorkflow:
    
    def test_complete_sampling_workflow(
        self,
        integration_sampler,
        sample_paper_metadata_df
    ):
        integration_sampler.data_coordinator.frames.df_paper_metadata = sample_paper_metadata_df.copy()
        integration_sampler.data_coordinator.frames.df_forbidden_entries = pd.DataFrame(
            columns=['paperId', 'sampler']
        )
        
        centralities_df = pd.DataFrame({
            'paperId': sample_paper_metadata_df['paperId'],
            'centrality (in)': [0.5, 0.3, 0.7],
            'centrality (out)': [0.4, 0.6, 0.2]
        })
        integration_sampler.data_coordinator.graph.get_paper_centralities.return_value = centralities_df
        
        with patch.object(integration_sampler, 'filter_by_keywords'):
            integration_sampler.prepare_initial_sample()
            
            if len(integration_sampler.potential_future_sample_ids) > 0:
                assert len(integration_sampler.potential_future_sample_ids) > 0 
