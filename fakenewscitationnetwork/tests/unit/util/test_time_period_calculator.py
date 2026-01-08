import pytest
from ArticleCrawler.utils.time_period_calculator import TimePeriodCalculator
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
from ArticleCrawler.library.models import TimePeriod, PaperData


class TestTimePeriodCalculator:
    
    @pytest.fixture
    def config(self):
        return TemporalAnalysisConfig(time_period_years=3, min_papers_per_period=2)
    
    @pytest.fixture
    def calculator(self, config):
        return TimePeriodCalculator(config)
    
    @pytest.fixture
    def sample_papers(self):
        papers = []
        for year in [2020, 2020, 2021, 2022, 2023, 2024, 2025]:
            papers.append(PaperData(
                paper_id=f"W{year}",
                title=f"Paper {year}",
                year=year,
                authors=[]
            ))
        return papers
    
    def test_extract_years(self, calculator, sample_papers):
        years = calculator._extract_years(sample_papers)
        assert years == [2020, 2020, 2021, 2022, 2023, 2024, 2025]
    
    def test_extract_years_filters_invalid(self, calculator):
        papers = [
            PaperData(paper_id="W1", title="P1", year=2020, authors=[]),
            PaperData(paper_id="W2", title="P2", year=None, authors=[]),
            PaperData(paper_id="W3", title="P3", year=0, authors=[]),
            PaperData(paper_id="W4", title="P4", year=-1, authors=[])
        ]
        years = calculator._extract_years(papers)
        assert years == [2020]
    
    def test_calculate_fixed_periods(self, calculator, sample_papers):
        periods = calculator.calculate_periods(sample_papers)
        assert len(periods) == 2
        assert periods[0].start_year == 2020
        assert periods[0].end_year == 2022
        assert periods[1].start_year == 2023
        assert periods[1].end_year == 2025
    
    def test_calculate_fixed_periods_exclude_partial(self):
        config = TemporalAnalysisConfig(
            time_period_years=3,
            include_partial_periods=False
        )
        calculator = TimePeriodCalculator(config)
        papers = [PaperData(paper_id=f"W{y}", title="P", year=y, authors=[]) 
                  for y in [2020, 2021, 2022, 2023, 2024]]
        periods = calculator.calculate_periods(papers)
        assert len(periods) == 1
        assert periods[0].end_year == 2022
    
    def test_calculate_adaptive_periods(self):
        config = TemporalAnalysisConfig(
            period_strategy="adaptive",
            time_period_years=2,
            min_papers_per_period=3
        )
        calculator = TimePeriodCalculator(config)
        papers = [PaperData(paper_id=f"W{i}", title="P", year=y, authors=[])
                  for i, y in enumerate([2020, 2020, 2021, 2022, 2023, 2024])]
        periods = calculator.calculate_periods(papers)
        assert len(periods) > 0
        for period in periods:
            papers_in_period = [p for p in papers if period.start_year <= p.year <= period.end_year]
            assert len(papers_in_period) >= config.min_papers_per_period
    
    def test_calculate_custom_periods(self):
        config = TemporalAnalysisConfig(
            period_strategy="custom",
            custom_periods=[(2020, 2022), (2023, 2025)]
        )
        calculator = TimePeriodCalculator(config)
        periods = calculator._calculate_custom_periods()
        assert len(periods) == 2
        assert periods[0].start_year == 2020
        assert periods[0].end_year == 2022
    
    def test_calculate_periods_no_valid_years(self, calculator):
        papers = [PaperData(paper_id="W1", title="P", year=None, authors=[])]
        with pytest.raises(ValueError, match="No papers with valid year information"):
            calculator.calculate_periods(papers)
    
    def test_calculate_periods_unknown_strategy(self):
        config = TemporalAnalysisConfig(period_strategy="unknown")
        calculator = TimePeriodCalculator(config)
        papers = [PaperData(paper_id="W1", title="P", year=2020, authors=[])]
        with pytest.raises(ValueError, match="Unknown period strategy"):
            calculator.calculate_periods(papers)
    
    def test_assign_papers_to_periods(self, calculator, sample_papers):
        periods = calculator.calculate_periods(sample_papers)
        papers_by_period = calculator.assign_papers_to_periods(sample_papers, periods)
        
        assert len(papers_by_period) == len(periods)
        total_assigned = sum(len(papers) for papers in papers_by_period.values())
        assert total_assigned == len(sample_papers)