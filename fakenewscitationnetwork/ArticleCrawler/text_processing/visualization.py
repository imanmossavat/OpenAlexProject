import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import ceil
from wordcloud import WordCloud
from typing import Dict, List, Optional

class TopicVisualization:
    """
    Topic visualization component for generating charts and plots.
    
    This class handles all visualization logic for topic modeling results,
    separated from the main topic modeling logic for better maintainability.
    """
    
    def __init__(self, config):
        """
        Initialize visualization component.
        
        Args:
            config: Configuration object with visualization parameters
        """
        self.config = config
        
        # Calculate subplot layout based on configuration
        self.subplot_layout, self.num_figures = self.calculate_subplot_layout(
            self.config.num_topics, 
            self.config.max_rows, 
            self.config.max_columns
        )

    def calculate_subplot_layout(self, num_topics: int, max_rows: int = 4, max_columns: int = 5):
        """
        Calculate how many figures and subplots are needed based on the number of topics.
        
        Args:
            num_topics: Total number of topics
            max_rows: Maximum rows per figure
            max_columns: Maximum columns per figure
            
        Returns:
            Tuple of (subplot_layout, num_figures)
        """
        max_subplots_per_figure = max_rows * max_columns
        num_figures = ceil(num_topics / max_subplots_per_figure)
        
        subplot_layout = []
        for fig_idx in range(num_figures):
            start_topic_idx = fig_idx * max_subplots_per_figure
            end_topic_idx = min((fig_idx + 1) * max_subplots_per_figure, num_topics)
            num_topics_in_fig = end_topic_idx - start_topic_idx
            
            n_rows = min(max_rows, ceil(num_topics_in_fig / max_columns))
            n_cols = min(max_columns, num_topics_in_fig)
            
            subplot_layout.append((n_rows, n_cols))
        
        return subplot_layout, num_figures

    def word_cloud(self, words: Dict[int, List[str]], topic_weights: np.ndarray, 
                   model_type: str, logger, save_dir: Optional[str] = None):
        """
        Generate and display or save word clouds for each topic.

        Args:
            words: Dictionary of top words for each topic
            topic_weights: Topic weights/probabilities for each topic
            model_type: Model type ('NMF' or 'LDA')
            logger: Logger for status messages
            save_dir: Directory to save figures (if None, plots will be displayed)
        """
        for fig_idx, (n_rows, n_cols) in enumerate(self.subplot_layout):
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10), 
                                   num=f'Model Type ({model_type})')

            for i in range(len(topic_weights)):
                try:
                    # Validate input lengths
                    if len(words[i]) != len(topic_weights[i]):
                        raise ValueError(f"Length mismatch: words[{i}] has {len(words[i])} elements, "
                                      f"but topic_weights[{i}] has {len(topic_weights[i])} elements.")

                    # Filter invalid or NaN values
                    valid_data = [
                        (word, weight) for word, weight in zip(words[i], topic_weights[i])
                        if pd.notna(weight) and weight > 0
                    ]
                    if not valid_data:
                        raise ValueError(f"No valid data for Topic {i}.")

                    # Generate word cloud
                    wordcloud = WordCloud(background_color="white").generate_from_frequencies(dict(valid_data))

                    # Display the word cloud
                    ax = axes[i // n_cols, i % n_cols]
                    ax.imshow(wordcloud, interpolation="bilinear")
                    ax.axis("off")
                    ax.set_title(f"Topic {i} ({model_type})")

                except Exception as e:
                    # Log the error and data for troubleshooting
                    logger.error(f"Error generating word cloud for topic {i}: {e}", exc_info=True)
                    logger.error(f"Offending words[{i}]: {words[i]}")
                    logger.error(f"Offending topic_weights[{i}]: {topic_weights[i]}")
                    
                    # Handle subplot for error
                    if n_rows * n_cols > i:
                        ax = axes[i // n_cols, i % n_cols]
                        ax.axis("off")
                        ax.set_title(f"Topic {i} - Error")

            # Turn off unused axes
            for j in range(len(topic_weights), n_rows * n_cols):
                ax = axes[j // n_cols, j % n_cols]
                ax.axis("off")

            # Save or show the figure
            if save_dir:
                fig_path = save_dir / f"wordcloud_model_{model_type}_figure_{fig_idx}.png"
                plt.savefig(fig_path, bbox_inches='tight')
                logger.info(f"Word cloud figure saved to {fig_path}")
            else:
                plt.show()

            plt.close(fig)

    def top_words_barplot(self, words: Dict[int, List[str]], topic_weights: np.ndarray, 
                         model_type: str, logger, save_dir: Optional[str] = None):
        """
        Generate a grid plot showing the top words for each topic.
        
        Args:
            words: Dictionary of top words for each topic
            topic_weights: Topic weights or probabilities for each topic
            model_type: Model type ('NMF' or 'LDA')
            logger: Logger for status messages
            save_dir: Directory to save figure (if None, plot will be displayed)
        """
        n_topics = topic_weights.shape[0]

        for fig_idx, (n_rows, n_cols) in enumerate(self.subplot_layout):
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), 
                                   num=f'Model Type ({model_type})')

            axes = axes.flatten()

            for topic_idx, topic in enumerate(topic_weights):
                ax = axes[topic_idx]
                top_terms = words[topic_idx]
                top_weights = topic
                ax.barh(top_terms, top_weights, color='skyblue')
                ax.set_title(f"Topic {topic_idx + 1} ({model_type})")
                ax.set_xlabel('Weight')
                ax.set_ylabel('Words')

            # Delete extra subplots if any
            for i in range(n_topics, len(axes)):
                fig.delaxes(axes[i])

            plt.tight_layout()

            if save_dir:
                save_path = os.path.join(save_dir, f"top_words_{model_type}_fig_{fig_idx + 1}.png")
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
                logger.info(f"Figure saved to {save_path}")
                plt.close(fig)
            else:
                plt.show()

    def temporal_topic_area_chart(self, df: pd.DataFrame, model_type: str, logger, 
                                 save_dir: Optional[str] = None):
        """
        Visualize the evolution of topics over time using area charts.

        Args:
            df: DataFrame containing topic assignments over time
            model_type: Model type ('NMF' or 'LDA')
            logger: Logger for status messages
            save_dir: Directory to save figure (if None, plot will be displayed)
        """
        # Filter relevant columns
        filtered_data = df[['year', f'{model_type.lower()}_topic']].copy()
        filtered_data = filtered_data.dropna()
        filtered_data = filtered_data[filtered_data[f'{model_type.lower()}_topic'] != -1]
        filtered_data[f'{model_type.lower()}_topic'] = filtered_data[f'{model_type.lower()}_topic'].astype(int)

        # Group by year and topic to get topic counts
        topic_counts = filtered_data.groupby(['year', f'{model_type.lower()}_topic']).size().unstack(fill_value=0)

        # Normalize topic counts to get proportions over time
        topic_proportions = topic_counts.div(topic_counts.sum(axis=1), axis=0)

        # Plot area chart
        fig, ax = plt.subplots(figsize=(10, 6), num=f'Model Type ({model_type})')

        topic_proportions.plot.area(ax=ax, cmap="tab20", stacked=True)

        ax.set_title(f"Evolution of Topics Over Time ({model_type})")
        ax.set_xlabel("Year")
        ax.set_ylabel("Proportion of Documents")
        ax.legend(title="Topics", bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()

        if save_dir:
            save_path = os.path.join(save_dir, f"temporal_topic_evolution_{model_type}.png")
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved temporal topic evolution figure at {save_path}")
            plt.close(fig)
        else:
            plt.show()