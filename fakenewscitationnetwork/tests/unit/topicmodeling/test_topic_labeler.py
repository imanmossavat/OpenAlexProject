
import pytest
from unittest.mock import Mock
from ArticleCrawler.text_processing.topic_labeler import TopicLabeler
from ArticleCrawler.library.models import PaperData, TopicCluster


@pytest.mark.unit
class TestTopicLabeler:
    
    @pytest.fixture
    def mock_strategy(self):
        strategy = Mock()
        strategy.label_cluster = Mock()
        return strategy
    
    @pytest.fixture
    def topic_labeler(self, mock_strategy, mock_logger):
        return TopicLabeler(strategy=mock_strategy, logger=mock_logger)
    
    @pytest.fixture
    def sample_clusters(self):
        return {
            0: [
                PaperData(paper_id="W123", title="Paper 1", authors=[]),
                PaperData(paper_id="W456", title="Paper 2", authors=[])
            ],
            1: [
                PaperData(paper_id="W789", title="Paper 3", authors=[])
            ]
        }
    
    @pytest.fixture
    def sample_top_words(self):
        return {
            0: ["word1", "word2", "word3"],
            1: ["word4", "word5"]
        }
    
    def test_label_clusters(self, topic_labeler, mock_strategy, sample_clusters, sample_top_words):
        mock_strategy.label_cluster.return_value = TopicCluster(
            cluster_id=0,
            label="Test Cluster",
            paper_ids=["W123", "W456"]
        )
        
        labeled_clusters = topic_labeler.label_clusters(
            clusters=sample_clusters,
            top_words_per_cluster=sample_top_words
        )
        
        assert len(labeled_clusters) == 2
        assert mock_strategy.label_cluster.call_count == 2
    
    def test_label_clusters_without_top_words(self, topic_labeler, mock_strategy, sample_clusters):
        mock_strategy.label_cluster.return_value = TopicCluster(
            cluster_id=0,
            label="Cluster",
            paper_ids=[]
        )
        
        labeled_clusters = topic_labeler.label_clusters(clusters=sample_clusters)
        
        assert len(labeled_clusters) == 2
    
    def test_label_clusters_empty(self, topic_labeler, mock_strategy):
        labeled_clusters = topic_labeler.label_clusters(clusters={})
        
        assert labeled_clusters == []
        mock_strategy.label_cluster.assert_not_called()