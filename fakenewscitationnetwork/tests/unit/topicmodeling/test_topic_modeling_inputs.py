
import pytest
from pathlib import Path
from ArticleCrawler.cli.models.topic_modeling_inputs import TopicModelingInputs


@pytest.mark.unit
class TestTopicModelingInputs:
    
    def test_topic_modeling_inputs_basic(self, temp_dir):
        inputs = TopicModelingInputs(
            library_path=temp_dir,
            model_type="NMF",
            num_topics=5
        )
        
        assert inputs.library_path == temp_dir
        assert inputs.model_type == "NMF"
        assert inputs.num_topics == 5
    
    def test_topic_modeling_inputs_with_num_topics(self, temp_dir):
        inputs = TopicModelingInputs(
            library_path=temp_dir,
            model_type="LDA",
            num_topics=10
        )
        
        assert inputs.model_type == "LDA"
        assert inputs.num_topics == 10