from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from ArticleCrawler.library.models import TemporalTopicData
from ArticleCrawler.visualization.visualization_config import VisualizationConfig


class TopicEvolutionVisualizer(ABC):
    """
    Abstract base class for topic evolution visualizations.
    
    Concrete implementations must implement the visualize method.
    """
    
    def __init__(
        self,
        config: Optional[VisualizationConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize visualizer.
        
        Args:
            config: Visualization configuration
            logger: Logger instance
        """
        self.config = config or VisualizationConfig()
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def visualize(
        self,
        temporal_data: TemporalTopicData,
        output_path: Path,
        title: Optional[str] = None
    ):
        """
        Generate and save visualization.
        
        Args:
            temporal_data: Temporal topic data to visualize
            output_path: Path where image should be saved
            title: Optional custom title
        """
        pass
    
    def _setup_figure(self):
        """Create and configure figure."""
        plt.style.use(self.config.style)
        fig, ax = plt.subplots(
            figsize=(self.config.figure_width, self.config.figure_height)
        )
        return fig, ax
    
    def _filter_topics(
        self, 
        temporal_data: TemporalTopicData
    ) -> tuple[list[str], list[list[float]]]:
        """
        Filter topics based on configuration.
        
        Args:
            temporal_data: Temporal topic data
            
        Returns:
            Tuple of (filtered_labels, filtered_distributions)
        """
        avg_proportions = []
        for i in range(len(temporal_data.topic_labels)):
            proportions = [dist[i] for dist in temporal_data.topic_distributions]
            avg_proportions.append(np.mean(proportions))
        
        topic_info = list(zip(
            temporal_data.topic_labels,
            avg_proportions,
            range(len(temporal_data.topic_labels))
        ))
        
        topic_info = [
            (label, avg, idx) 
            for label, avg, idx in topic_info 
            if avg >= self.config.min_topic_proportion
        ]
        
        topic_info.sort(key=lambda x: x[1], reverse=True)
        
        if self.config.top_n_topics:
            topic_info = topic_info[:self.config.top_n_topics]
        
        filtered_labels = [label for label, _, _ in topic_info]
        filtered_indices = [idx for _, _, idx in topic_info]
        
        filtered_distributions = [
            [dist[idx] for idx in filtered_indices]
            for dist in temporal_data.topic_distributions
        ]
        
        return filtered_labels, filtered_distributions
    
    def _save_figure(self, fig, output_path: Path):
        """Save figure to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        fig.savefig(output_path, dpi=self.config.dpi, bbox_inches='tight')
        plt.close(fig)
        
        self.logger.info(f"Saved visualization to: {output_path}")


class LineChartVisualizer(TopicEvolutionVisualizer):
    """
    Line chart visualization showing topic proportions over time.
    
    Each topic is represented by a line showing its proportion
    in each time period.
    """
    
    def visualize(
        self,
        temporal_data: TemporalTopicData,
        output_path: Path,
        title: Optional[str] = None
    ):
        """Generate line chart visualization."""
        self.logger.info("Generating line chart visualization")
        
        topic_labels, distributions = self._filter_topics(temporal_data)
        
        if not topic_labels:
            raise ValueError("No topics to visualize after filtering")
        
        fig, ax = self._setup_figure()
        
        colors = self.config.get_colors(len(topic_labels))
        
        period_labels = [p.label for p in temporal_data.time_periods]
        x_positions = np.arange(len(period_labels))
        
        for i, topic in enumerate(topic_labels):
            values = [dist[i] for dist in distributions]
            
            line_kwargs = {
                'linewidth': self.config.line_width,
                'color': colors[i],
                'label': topic
            }
            
            if self.config.show_markers:
                line_kwargs['marker'] = self.config.marker_style
                line_kwargs['markersize'] = self.config.marker_size
            
            ax.plot(x_positions, values, **line_kwargs)
            
            if self.config.show_values:
                for x, y in zip(x_positions, values):
                    ax.annotate(
                        f'{y:{self.config.value_format}}',
                        (x, y),
                        textcoords="offset points",
                        xytext=(0, 5),
                        ha='center',
                        fontsize=self.config.tick_fontsize - 2
                    )
        
        ax.set_xlabel('Time Period', fontsize=self.config.axis_label_fontsize)
        ax.set_ylabel('Topic Proportion', fontsize=self.config.axis_label_fontsize)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(period_labels, fontsize=self.config.tick_fontsize)
        ax.tick_params(axis='y', labelsize=self.config.tick_fontsize)
        
        if self.config.show_grid:
            ax.grid(True, alpha=self.config.grid_alpha)
        
        ax.legend(
            loc=self.config.legend_location,
            fontsize=self.config.legend_fontsize
        )
        
        if title is None:
            title = f"Topic Evolution: {temporal_data.author_name}"
        ax.set_title(title, fontsize=self.config.title_fontsize, pad=20)
        
        self._save_figure(fig, output_path)


class HeatmapVisualizer(TopicEvolutionVisualizer):
    """
    Heatmap visualization showing topic intensity over time.
    
    Topics are shown as rows, time periods as columns,
    with color intensity representing proportion.
    """
    
    def visualize(
        self,
        temporal_data: TemporalTopicData,
        output_path: Path,
        title: Optional[str] = None
    ):
        """Generate heatmap visualization."""
        self.logger.info("Generating heatmap visualization")
        
        topic_labels, distributions = self._filter_topics(temporal_data)
        
        if not topic_labels:
            raise ValueError("No topics to visualize after filtering")
        
        fig, ax = self._setup_figure()
        
        data_matrix = np.array(distributions).T
        
        im = ax.imshow(data_matrix, cmap='YlOrRd', aspect='auto')
        
        period_labels = [p.label for p in temporal_data.time_periods]
        ax.set_xticks(np.arange(len(period_labels)))
        ax.set_yticks(np.arange(len(topic_labels)))
        ax.set_xticklabels(period_labels, fontsize=self.config.tick_fontsize)
        ax.set_yticklabels(topic_labels, fontsize=self.config.tick_fontsize)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Topic Proportion', fontsize=self.config.axis_label_fontsize)
        
        if self.config.show_values:
            for i in range(len(topic_labels)):
                for j in range(len(period_labels)):
                    text = ax.text(
                        j, i, f'{data_matrix[i, j]:{self.config.value_format}}',
                        ha="center", va="center",
                        color="black" if data_matrix[i, j] < 0.5 else "white",
                        fontsize=self.config.tick_fontsize - 2
                    )
        
        ax.set_xlabel('Time Period', fontsize=self.config.axis_label_fontsize)
        ax.set_ylabel('Topic', fontsize=self.config.axis_label_fontsize)
        
        if title is None:
            title = f"Topic Evolution Heatmap: {temporal_data.author_name}"
        ax.set_title(title, fontsize=self.config.title_fontsize, pad=20)
        
        self._save_figure(fig, output_path)


class StackedAreaVisualizer(TopicEvolutionVisualizer):
    """
    Stacked area chart showing topic composition over time.
    
    Shows how the total "research space" is divided among topics,
    with areas stacked to show the full composition at each time point.
    """
    
    def visualize(
        self,
        temporal_data: TemporalTopicData,
        output_path: Path,
        title: Optional[str] = None
    ):
        """Generate stacked area visualization."""
        self.logger.info("Generating stacked area visualization")
        
        topic_labels, distributions = self._filter_topics(temporal_data)
        
        if not topic_labels:
            raise ValueError("No topics to visualize after filtering")
        
        fig, ax = self._setup_figure()
        
        colors = self.config.get_colors(len(topic_labels))
        
        period_labels = [p.label for p in temporal_data.time_periods]
        x_positions = np.arange(len(period_labels))
        
        data_by_topic = []
        for i in range(len(topic_labels)):
            data_by_topic.append([dist[i] for dist in distributions])
        
        ax.stackplot(
            x_positions,
            *data_by_topic,
            labels=topic_labels,
            colors=colors,
            alpha=0.8
        )
        
        ax.set_xlabel('Time Period', fontsize=self.config.axis_label_fontsize)
        ax.set_ylabel('Topic Proportion', fontsize=self.config.axis_label_fontsize)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(period_labels, fontsize=self.config.tick_fontsize)
        ax.tick_params(axis='y', labelsize=self.config.tick_fontsize)
        
        if self.config.show_grid:
            ax.grid(True, alpha=self.config.grid_alpha, zorder=0)
        
        ax.legend(
            loc=self.config.legend_location,
            fontsize=self.config.legend_fontsize
        )
        
        if title is None:
            title = f"Topic Composition Over Time: {temporal_data.author_name}"
        ax.set_title(title, fontsize=self.config.title_fontsize, pad=20)
        
        ax.set_ylim(0, 1)
        
        self._save_figure(fig, output_path)