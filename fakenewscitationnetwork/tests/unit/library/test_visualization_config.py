import pytest
from ArticleCrawler.visualization.visualization_config import VisualizationConfig


class TestVisualizationConfig:
    
    def test_default_initialization(self):
        config = VisualizationConfig()
        assert config.figure_width == 12
        assert config.figure_height == 8
        assert config.dpi == 300
        assert config.line_width == 2.5
        assert config.marker_size == 8
        assert config.show_markers is True
        assert config.show_grid is True
        assert config.top_n_topics is None
    
    def test_custom_initialization(self):
        config = VisualizationConfig(
            figure_width=14,
            figure_height=10,
            dpi=150,
            show_grid=False,
            top_n_topics=5
        )
        assert config.figure_width == 14
        assert config.figure_height == 10
        assert config.dpi == 150
        assert config.show_grid is False
        assert config.top_n_topics == 5
    
    def test_get_colors_from_colormap(self):
        config = VisualizationConfig(color_palette="tab10")
        colors = config.get_colors(5)
        assert len(colors) == 5
    
    def test_get_colors_from_custom_colors(self):
        custom = ["#FF0000", "#00FF00", "#0000FF"]
        config = VisualizationConfig(custom_colors=custom)
        colors = config.get_colors(3)
        assert colors == custom
    
    def test_get_colors_custom_colors_take_precedence(self):
        custom = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
        config = VisualizationConfig(custom_colors=custom, color_palette="viridis")
        colors = config.get_colors(3)
        assert colors == custom[:3]