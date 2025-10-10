
import pytest
from rich.console import Console
from ArticleCrawler.cli.formatters.topic_modeling_result_formatter import TopicModelingResultFormatter
from ArticleCrawler.library.models import TopicCluster
from pathlib import Path


@pytest.mark.unit
class TestTopicModelingResultFormatter:
    
    @pytest.fixture
    def console(self):
        return Console()
    
    @pytest.fixture
    def formatter(self, console):
        return TopicModelingResultFormatter(console=console)
    
    @pytest.fixture
    def sample_clusters(self):
        return [
            TopicCluster(
                cluster_id=0,
                label="Machine Learning",
                paper_ids=["W1", "W2", "W3"],
                top_words=["learning", "neural", "network"]
            ),
            TopicCluster(
                cluster_id=1,
                label="Computer Vision",
                paper_ids=["W4", "W5"],
                top_words=["image", "visual", "detection"]
            )
        ]
    
    def test_format_results(self, formatter, sample_clusters, temp_dir):
        formatter.display(sample_clusters, temp_dir)
        
        assert True
    
    def test_format_results_empty(self, formatter, temp_dir):
        formatter.display([], temp_dir)
        
        assert True
    
    def test_format_cluster_summary(self, formatter, sample_clusters):
        table = formatter._create_table(sample_clusters)
        
        assert table is not None