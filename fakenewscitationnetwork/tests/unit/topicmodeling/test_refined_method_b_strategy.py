
import pytest
from unittest.mock import Mock
from ArticleCrawler.text_processing.refined_method_b_strategy import RefinedMethodBStrategy
from ArticleCrawler.library.models import PaperData, TopicCluster


@pytest.mark.unit
class TestRefinedMethodBStrategy:
    
    @pytest.fixture
    def strategy(self, mock_logger):
        return RefinedMethodBStrategy(logger=mock_logger)
    
    @pytest.fixture
    def sample_papers(self):
        return [
            PaperData(
                paper_id="W123",
                title="Paper 1",
                authors=[],
                concepts=[
                    {'id': 'C1', 'display_name': 'Machine Learning', 'level': 2, 'score': 0.95},
                    {'id': 'C2', 'display_name': 'Neural Networks', 'level': 3, 'score': 0.85}
                ]
            ),
            PaperData(
                paper_id="W456",
                title="Paper 2",
                authors=[],
                concepts=[
                    {'id': 'C1', 'display_name': 'Machine Learning', 'level': 2, 'score': 0.9},
                    {'id': 'C3', 'display_name': 'Deep Learning', 'level': 3, 'score': 0.8}
                ]
            )
        ]
    
    def test_label_cluster(self, strategy, sample_papers):
        cluster = strategy.label_cluster(
            cluster_papers=sample_papers,
            cluster_id=0,
            top_words=["learning", "neural"]
        )
        
        assert isinstance(cluster, TopicCluster)
        assert cluster.cluster_id == 0
        assert cluster.label is not None
        assert len(cluster.paper_ids) == 2
    
    def test_label_cluster_no_concepts(self, strategy):
        papers = [
            PaperData(paper_id="W1", title="P1", authors=[], concepts=[]),
            PaperData(paper_id="W2", title="P2", authors=[], concepts=[])
        ]
        
        cluster = strategy.label_cluster(papers, cluster_id=0)
        
        assert cluster.label == "Cluster_0"
    
    def test_extract_concepts_from_papers(self, strategy, sample_papers):
        concepts = strategy._extract_concepts_from_papers(sample_papers)
        
        assert len(concepts) > 0
        assert all(c.get('level', 0) >= strategy.min_concept_level for c in concepts)
    
    def test_find_representative_concepts(self, strategy, sample_papers):
        concepts = strategy._extract_concepts_from_papers(sample_papers)
        
        representative = strategy._find_representative_concepts(concepts)
        
        assert len(representative) <= strategy.top_n_concepts
    
    def test_generate_label_single_concept(self, strategy):
        concepts = [{'display_name': 'Machine Learning', 'frequency': 5}]
        
        label = strategy._generate_label(concepts)
        
        assert label == 'Machine Learning'
    
    def test_generate_label_multiple_concepts(self, strategy):
        concepts = [
            {'display_name': 'Machine Learning', 'frequency': 5},
            {'display_name': 'Computer Vision', 'frequency': 3}
        ]
        
        label = strategy._generate_label(concepts)
        
        assert '&' in label or 'Machine Learning' in label
    
    def test_generate_label_empty(self, strategy):
        label = strategy._generate_label([])
        
        assert label == "Unlabeled"