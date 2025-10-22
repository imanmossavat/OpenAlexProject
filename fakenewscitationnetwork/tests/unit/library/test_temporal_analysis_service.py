import pytest
from unittest.mock import Mock
from ArticleCrawler.library.temporal_analysis_service import TemporalAnalysisService
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
from ArticleCrawler.library.models import PaperData, AuthorInfo, TimePeriod


class TestTemporalAnalysisService:
    
    @pytest.fixture
    def config(self):
        return TemporalAnalysisConfig(
            time_period_years=3,
            min_papers_per_period=2,
            min_papers_total=5
        )
    
    @pytest.fixture
    def service(self, config, mock_logger):
        return TemporalAnalysisService(config, mock_logger)
    
    @pytest.fixture
    def author(self):
        return AuthorInfo(id="A123", name="Test Author", works_count=10, cited_by_count=100)
    
    @pytest.fixture
    def sample_papers_with_topics(self):
        papers = []
        data = [
            (2020, "Machine Learning"),
            (2020, "Deep Learning"),
            (2021, "Machine Learning"),
            (2022, "Deep Learning"),
            (2023, "Neural Networks"),
            (2024, "Neural Networks"),
            (2025, "Neural Networks")
        ]
        for i, (year, topic) in enumerate(data):
            papers.append(PaperData(
                paper_id=f"W{i}",
                title=f"Paper {i}",
                year=year,
                authors=[],
                topic_label=topic
            ))
        return papers
    
    def test_analyze_evolution_success(self, service, author, sample_papers_with_topics):
        result = service.analyze_evolution(author, sample_papers_with_topics)
        
        assert result.author_id == author.id
        assert result.author_name == author.name
        assert result.total_papers == len(sample_papers_with_topics)
        assert len(result.topic_labels) > 0
        assert len(result.time_periods) > 0
    
    def test_validate_papers_insufficient_total(self, service, author):
        papers = [PaperData(paper_id=f"W{i}", title="P", year=2020, authors=[], topic_label="T1") 
                  for i in range(3)]
        with pytest.raises(ValueError, match="Need at least 5 papers"):
            service.analyze_evolution(author, papers)
    
    def test_validate_papers_no_topics(self, service, author):
        papers = [PaperData(paper_id=f"W{i}", title="P", year=2020, authors=[]) 
                  for i in range(6)]
        with pytest.raises(ValueError, match="No papers have topic assignments"):
            service.analyze_evolution(author, papers)
    
    def test_validate_papers_no_years(self, service, author):
        papers = [PaperData(paper_id=f"W{i}", title="P", year=None, authors=[], topic_label="T1") 
                  for i in range(6)]
        with pytest.raises(ValueError, match="papers with year information"):
            service.analyze_evolution(author, papers)
    
    def test_extract_topic_labels(self, service, sample_papers_with_topics):
        labels = service._extract_topic_labels(sample_papers_with_topics)
        assert isinstance(labels, list)
        assert "Machine Learning" in labels
        assert "Deep Learning" in labels
        assert "Neural Networks" in labels
        assert len(labels) == 3
    
    def test_filter_periods_by_paper_count(self, service, sample_papers_with_topics):
        periods = [
            TimePeriod(start_year=2020, end_year=2022),
            TimePeriod(start_year=2023, end_year=2025)
        ]
        papers_by_period = {
            periods[0].label: sample_papers_with_topics[:4],
            periods[1].label: sample_papers_with_topics[4:]
        }
        
        valid = service._filter_periods_by_paper_count(periods, papers_by_period)
        assert len(valid) == 2
    
    def test_filter_periods_excludes_insufficient(self, service):
        periods = [
            TimePeriod(start_year=2020, end_year=2022),
            TimePeriod(start_year=2023, end_year=2025)
        ]
        papers = [PaperData(paper_id="W1", title="P", year=2020, authors=[], topic_label="T1")]
        papers_by_period = {
            periods[0].label: papers,
            periods[1].label: []
        }
        
        valid = service._filter_periods_by_paper_count(periods, papers_by_period)
        assert len(valid) == 0
    
    def test_calculate_topic_distributions(self, service, sample_papers_with_topics):
        periods = [TimePeriod(start_year=2020, end_year=2025)]
        papers_by_period = {periods[0].label: sample_papers_with_topics}
        topic_labels = ["Machine Learning", "Deep Learning", "Neural Networks"]
        
        distributions = service._calculate_topic_distributions(periods, papers_by_period, topic_labels)
        
        assert len(distributions) == 1
        assert len(distributions[0]) == 3
        assert sum(distributions[0]) == pytest.approx(1.0, abs=0.01)