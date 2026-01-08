
import pytest
from unittest.mock import Mock
from ArticleCrawler.text_processing.topic_labeling_strategy import TopicLabelingStrategy
from ArticleCrawler.library.models import PaperData, TopicCluster


@pytest.mark.unit
class TestTopicLabelingStrategy:
    
    def test_strategy_is_abstract(self):
        with pytest.raises(TypeError):
            TopicLabelingStrategy()
    
    def test_strategy_requires_label_cluster_implementation(self):
        class IncompleteStrategy(TopicLabelingStrategy):
            pass
        
        with pytest.raises(TypeError):
            IncompleteStrategy()