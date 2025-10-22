from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class VisualizationConfig:
    """Configuration for topic evolution visualizations."""
    
    figure_width: int = 12
    """Figure width in inches"""
    
    figure_height: int = 8
    """Figure height in inches"""
    
    dpi: int = 300
    """Resolution for saved images"""
    
    style: str = "seaborn-v0_8-darkgrid"
    """Matplotlib style to use"""
    
    color_palette: str = "tab10"
    """Color palette for topics (matplotlib colormap name)"""
    
    custom_colors: Optional[List[str]] = None
    """Custom color list (overrides color_palette if provided)"""
    
    line_width: float = 2.5
    """Width of lines in line charts"""
    
    marker_size: float = 8
    """Size of markers on lines"""
    
    marker_style: str = "o"
    """Marker style (o, s, ^, etc.)"""
    
    show_markers: bool = True
    """Whether to show markers on line charts"""
    
    title_fontsize: int = 16
    """Font size for main title"""
    
    axis_label_fontsize: int = 12
    """Font size for axis labels"""
    
    tick_fontsize: int = 10
    """Font size for tick labels"""
    
    legend_fontsize: int = 10
    """Font size for legend"""
    
    show_grid: bool = True
    """Whether to show grid"""
    
    grid_alpha: float = 0.3
    """Transparency of grid lines"""
    
    legend_location: str = "best"
    """Location of legend"""
    
    tight_layout: bool = True
    """Use tight layout to prevent label cutoff"""
    
    show_values: bool = False
    """Whether to show values on data points"""
    
    value_format: str = ".2f"
    """Format string for displayed values"""
    
    top_n_topics: Optional[int] = None
    """Show only top N topics (by average proportion)"""
    
    min_topic_proportion: float = 0.0
    """Minimum average proportion for a topic to be displayed"""
    
    def get_colors(self, n_topics: int) -> List[str]:
        """
        Get color list for topics.
        
        Args:
            n_topics: Number of topics to color
            
        Returns:
            List of color strings
        """
        if self.custom_colors and len(self.custom_colors) >= n_topics:
            return self.custom_colors[:n_topics]
        
        import matplotlib.pyplot as plt
        cmap = plt.get_cmap(self.color_palette)
        return [cmap(i / n_topics) for i in range(n_topics)]