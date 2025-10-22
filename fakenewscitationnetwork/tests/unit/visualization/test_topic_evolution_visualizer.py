import pytest
from unittest.mock import Mock
from pathlib import Path
import numpy as np
from ArticleCrawler.visualization.topic_evolution_visualizer import (
    LineChartVisualizer,
    HeatmapVisualizer,
    StackedAreaVisualizer
)
from ArticleCrawler.visualization.visualization_config import VisualizationConfig
from ArticleCrawler.library.models import TemporalTopicData, TimePeriod


class TestTopicEvolutionVisualizers:
    
    @pytest.fixture
    def config(self):
        return VisualizationConfig(figure_width=10, figure_height=6)
    
    @pytest.fixture
    def temporal_data(self):
        periods = [
            TimePeriod(start_year=2020, end_year=2022),
            TimePeriod(start_year=2023, end_year=2025)
        ]
        return TemporalTopicData(
            author_id="A123",
            author_name="Test Author",
            time_periods=periods,
            topic_labels=["ML", "DL", "NLP"],
            topic_distributions=[[0.5, 0.3, 0.2], [0.3, 0.4, 0.3]],
            paper_counts_per_period=[10, 8],
            total_papers=18,
            papers_by_period={}
        )
    
    def test_line_chart_visualizer(self, config, temporal_data, temp_dir, mock_logger):
        visualizer = LineChartVisualizer(config, mock_logger)
        output_path = temp_dir / "line_chart.png"
        
        visualizer.visualize(temporal_data, output_path)
        
        assert output_path.exists()
    
    def test_heatmap_visualizer(self, config, temporal_data, temp_dir, mock_logger):
        visualizer = HeatmapVisualizer(config, mock_logger)
        output_path = temp_dir / "heatmap.png"
        
        visualizer.visualize(temporal_data, output_path)
        
        assert output_path.exists()
    
    def test_stacked_area_visualizer(self, config, temporal_data, temp_dir, mock_logger):
        visualizer = StackedAreaVisualizer(config, mock_logger)
        output_path = temp_dir / "stacked.png"
        
        visualizer.visualize(temporal_data, output_path)
        
        assert output_path.exists()
    
    def test_visualize_with_custom_title(self, config, temporal_data, temp_dir, mock_logger):
        visualizer = LineChartVisualizer(config, mock_logger)
        output_path = temp_dir / "custom_title.png"
        
        visualizer.visualize(temporal_data, output_path, title="Custom Title")
        
        assert output_path.exists()
    
    def test_filter_topics_min_proportion(self, temporal_data, mock_logger):
        config = VisualizationConfig(min_topic_proportion=0.4)
        visualizer = LineChartVisualizer(config, mock_logger)
        
        labels, distributions = visualizer._filter_topics(temporal_data)
        
        assert len(labels) < len(temporal_data.topic_labels)
    
    def test_filter_topics_top_n(self, temporal_data, mock_logger):
        config = VisualizationConfig(top_n_topics=2)
        visualizer = LineChartVisualizer(config, mock_logger)
        
        labels, distributions = visualizer._filter_topics(temporal_data)
        
        assert len(labels) == 2