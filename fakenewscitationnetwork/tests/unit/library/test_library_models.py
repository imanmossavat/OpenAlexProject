
import pytest
from datetime import datetime
from pathlib import Path
from ArticleCrawler.library.models import LibraryConfig, PaperData, TopicCluster


@pytest.mark.unit
class TestLibraryConfig:
    
    def test_library_config_creation(self):
        config = LibraryConfig(
            name="test_library",
            base_path=Path("/test/path"),
            description="Test description"
        )
        
        assert config.name == "test_library"
        assert config.base_path == Path("/test/path")
        assert config.description == "Test description"
        assert config.api_provider == "openalex"
        assert isinstance(config.created_at, datetime)
    
    def test_library_config_to_dict(self):
        config = LibraryConfig(
            name="test_library",
            base_path=Path("/test/path")
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['name'] == "test_library"
        assert str(Path(config_dict['base_path'])) == str(Path("/test/path"))
        assert 'created_at' in config_dict
        assert config_dict['api_provider'] == "openalex"
    
    def test_library_config_from_dict(self):
        data = {
            'name': 'test_library',
            'base_path': '/test/path',
            'description': 'Test',
            'created_at': '2024-01-01T00:00:00',
            'api_provider': 'openalex'
        }
        
        config = LibraryConfig.from_dict(data)
        
        assert config.name == 'test_library'
        assert config.base_path == Path('/test/path')
        assert config.description == 'Test'
        assert isinstance(config.created_at, datetime)
        assert config.api_provider == 'openalex'
    
    def test_library_config_from_dict_minimal(self):
        data = {
            'name': 'minimal',
            'base_path': '/path'
        }
        
        config = LibraryConfig.from_dict(data)
        
        assert config.name == 'minimal'
        assert config.api_provider == 'openalex'
        assert isinstance(config.created_at, datetime)


@pytest.mark.unit
class TestPaperData:
    
    def test_paper_data_creation_minimal(self):
        paper = PaperData(
            paper_id="W123",
            title="Test Paper",
            authors=[]
        )
        
        assert paper.paper_id == "W123"
        assert paper.title == "Test Paper"
        assert paper.authors == []
        assert paper.year is None
        assert paper.concepts == []
        assert paper.assigned_topic is None
    
    def test_paper_data_creation_complete(self):
        authors = [
            {'authorId': 'A123', 'name': 'John Doe'}
        ]
        concepts = [
            {'id': 'C123', 'display_name': 'AI', 'level': 2, 'score': 0.9}
        ]
        
        paper = PaperData(
            paper_id="W456",
            title="Complete Paper",
            authors=authors,
            year=2024,
            venue="Test Venue",
            doi="10.1234/test",
            abstract="Test abstract",
            url="https://test.com",
            concepts=concepts,
            assigned_topic=5,
            topic_label="Machine Learning"
        )
        
        assert paper.paper_id == "W456"
        assert paper.title == "Complete Paper"
        assert len(paper.authors) == 1
        assert paper.year == 2024
        assert paper.venue == "Test Venue"
        assert paper.doi == "10.1234/test"
        assert paper.abstract == "Test abstract"
        assert len(paper.concepts) == 1
        assert paper.assigned_topic == 5
        assert paper.topic_label == "Machine Learning"
    
    def test_paper_data_with_hierarchy(self):
        paper = PaperData(
            paper_id="W789",
            title="Hierarchy Paper",
            authors=[],
            topics=[{'id': 'T1', 'display_name': 'Topic1'}],
            subfields=[{'id': 'S1', 'display_name': 'Subfield1'}],
            fields=[{'id': 'F1', 'display_name': 'Field1'}],
            domains=[{'id': 'D1', 'display_name': 'Domain1'}]
        )
        
        assert len(paper.topics) == 1
        assert len(paper.subfields) == 1
        assert len(paper.fields) == 1
        assert len(paper.domains) == 1


@pytest.mark.unit
class TestTopicCluster:
    
    def test_topic_cluster_creation_minimal(self):
        cluster = TopicCluster(
            cluster_id=0,
            label="Test Cluster",
            paper_ids=["W123", "W456"]
        )
        
        assert cluster.cluster_id == 0
        assert cluster.label == "Test Cluster"
        assert len(cluster.paper_ids) == 2
        assert cluster.representative_concepts == []
        assert cluster.top_words == []
    
    def test_topic_cluster_creation_complete(self):
        cluster = TopicCluster(
            cluster_id=1,
            label="Machine Learning",
            paper_ids=["W123", "W456", "W789"],
            representative_concepts=[
                {'display_name': 'Neural Network', 'score': 0.95}
            ],
            top_words=["learning", "neural", "network"]
        )
        
        assert cluster.cluster_id == 1
        assert cluster.label == "Machine Learning"
        assert len(cluster.paper_ids) == 3
        assert len(cluster.representative_concepts) == 1
        assert len(cluster.top_words) == 3