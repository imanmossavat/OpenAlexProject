import os
from math import ceil
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from wordcloud import WordCloud

from .topic_companion_writer import TopicCompanionWriter, TopicVisualizationMetadata

class TopicVisualization:
    """
    Topic visualization component for generating charts and plots.
    
    This class handles all visualization logic for topic modeling results,
    separated from the main topic modeling logic for better maintainability.
    """
    
    def __init__(self, config, companion_writer: Optional[TopicCompanionWriter] = None):
        """
        Initialize visualization component.
        
        Args:
            config: Configuration object with visualization parameters
        """
        self.config = config
        self._companion_writer = companion_writer
        
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

    def set_companion_writer(self, writer: Optional[TopicCompanionWriter]):
        self._companion_writer = writer

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
        total_topics = len(topic_weights)
        for fig_idx, (n_rows, n_cols) in enumerate(self.subplot_layout):
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10), 
                                   num=f'Model Type ({model_type})')
            axes = np.array(axes, dtype=object).reshape(n_rows, n_cols)
            topic_indices = self._topic_indices_for_figure(fig_idx, n_rows, n_cols, total_topics)
            if not topic_indices:
                plt.close(fig)
                continue

            for position, topic_idx in enumerate(topic_indices):
                try:
                    # Validate input lengths
                    topic_terms = self._get_topic_terms(words, topic_idx)
                    topic_distribution = self._get_topic_weights(topic_weights, topic_idx)
                    if len(topic_terms) != len(topic_distribution):
                        raise ValueError(
                            f"Length mismatch: words[{topic_idx}] has {len(topic_terms)} elements, "
                            f"but topic_weights[{topic_idx}] has {len(topic_distribution)} elements."
                        )

                    # Filter invalid or NaN values
                    valid_data = [
                        (word, weight) for word, weight in zip(topic_terms, topic_distribution)
                        if pd.notna(weight) and weight > 0
                    ]
                    if not valid_data:
                        raise ValueError(f"No valid data for Topic {topic_idx}.")

                    # Generate word cloud
                    wordcloud = WordCloud(background_color="white").generate_from_frequencies(dict(valid_data))

                    # Display the word cloud
                    ax = axes[position // n_cols, position % n_cols]
                    ax.imshow(wordcloud, interpolation="bilinear")
                    ax.axis("off")
                    ax.set_title(f"Topic {topic_idx + 1} ({model_type})")

                except Exception as e:
                    # Log the error and data for troubleshooting
                    logger.error(f"Error generating word cloud for topic {topic_idx}: {e}", exc_info=True)
                    logger.error(f"Offending words[{topic_idx}]: {self._get_topic_terms(words, topic_idx)}")
                    logger.error(f"Offending topic_weights[{topic_idx}]: {topic_weights[topic_idx]}")
                    
                    # Handle subplot for error
                    max_slots = n_rows * n_cols
                    if max_slots > position:
                        ax = axes[position // n_cols, position % n_cols]
                        ax.axis("off")
                        ax.set_title(f"Topic {topic_idx + 1} - Error")

            # Turn off unused axes
            max_slots = n_rows * n_cols
            for j in range(len(topic_indices), max_slots):
                ax = axes[j // n_cols, j % n_cols]
                ax.axis("off")

            # Save or show the figure
            if save_dir:
                fig_path = Path(save_dir) / f"wordcloud_model_{model_type}_figure_{fig_idx}.png"
                plt.savefig(fig_path, bbox_inches='tight')
                logger.info(f"Word cloud figure saved to {fig_path}")
                description = self._build_topic_highlights(
                    topic_indices=topic_indices,
                    words=words,
                    topic_weights=topic_weights,
                )
                self._emit_companion_note(
                    image_path=fig_path,
                    title=f"{model_type} Word Clouds (Figure {fig_idx + 1})",
                    metadata=TopicVisualizationMetadata(
                        model_type=model_type,
                        figure_kind="word_cloud",
                        description=description
                        or f"Word clouds highlighting the most important terms for {model_type} topics.",
                        note_id=f"topic_wordcloud_{model_type.lower()}_{fig_idx + 1}",
                    ),
                )
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
            axes = np.array(axes, dtype=object).reshape(n_rows, n_cols)
            topic_indices = self._topic_indices_for_figure(fig_idx, n_rows, n_cols, n_topics)
            if not topic_indices:
                plt.close(fig)
                continue

            for position, topic_idx in enumerate(topic_indices):
                ax = axes[position // n_cols, position % n_cols]
                top_terms = self._get_topic_terms(words, topic_idx)
                top_weights = self._get_topic_weights(topic_weights, topic_idx)
                ax.barh(top_terms, top_weights, color='skyblue')
                ax.set_title(f"Topic {topic_idx + 1} ({model_type})")
                ax.set_xlabel('Weight')
                ax.set_ylabel('Words')

            # Delete extra subplots if any
            max_slots = n_rows * n_cols
            for i in range(len(topic_indices), max_slots):
                ax = axes[i // n_cols, i % n_cols]
                fig.delaxes(ax)

            plt.tight_layout()

            if save_dir:
                save_path = Path(save_dir) / f"top_words_{model_type}_fig_{fig_idx + 1}.png"
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
                logger.info(f"Figure saved to {save_path}")
                description = self._build_topic_highlights(
                    topic_indices=topic_indices,
                    words=words,
                    topic_weights=topic_weights,
                )
                self._emit_companion_note(
                    image_path=save_path,
                    title=f"{model_type} Top Words (Figure {fig_idx + 1})",
                    metadata=TopicVisualizationMetadata(
                        model_type=model_type,
                        figure_kind="top_words",
                        description=description
                        or f"Top contributing words for {model_type} topics (figure {fig_idx + 1}).",
                        note_id=f"topic_topwords_{model_type.lower()}_{fig_idx + 1}",
                    ),
                )
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
            save_path = Path(save_dir) / f"temporal_topic_evolution_{model_type}.png"
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved temporal topic evolution figure at {save_path}")
            description = self._build_temporal_summary(topic_counts, model_type)
            self._emit_companion_note(
                image_path=save_path,
                title=f"{model_type} Topic Evolution",
                metadata=TopicVisualizationMetadata(
                    model_type=model_type,
                    figure_kind="temporal_evolution",
                    description=description
                    or f"Temporal evolution of topics detected by the {model_type} model.",
                    note_id=f"topic_temporal_{model_type.lower()}",
                ),
            )
            plt.close(fig)
        else:
            plt.show()

    def _emit_companion_note(self, image_path: Path, title: str, metadata: TopicVisualizationMetadata):
        if not self._companion_writer:
            return
        try:
            self._companion_writer.write_topic_note(
                title=title,
                image_path=image_path,
                metadata=metadata,
            )
        except Exception:
            pass

    def _topic_indices_for_figure(self, fig_idx: int, n_rows: int, n_cols: int, total_topics: int) -> List[int]:
        capacity = n_rows * n_cols
        start = fig_idx * capacity
        end = min(start + capacity, total_topics)
        if start >= end:
            return []
        return list(range(start, end))

    def _get_topic_terms(self, words: Dict[int, List[str]], topic_idx: int) -> List[str]:
        if isinstance(words, dict):
            return words.get(topic_idx, [])
        try:
            return words[topic_idx]
        except (IndexError, KeyError):
            return []

    def _get_topic_weights(self, topic_weights: np.ndarray, topic_idx: int) -> np.ndarray:
        try:
            return topic_weights[topic_idx]
        except (IndexError, KeyError):
            return np.array([])

    def _build_topic_highlights(
        self,
        topic_indices: List[int],
        words: Dict[int, List[str]],
        topic_weights: np.ndarray,
        max_terms: int = 8,
    ) -> Optional[str]:
        sections: List[str] = []
        for topic_idx in topic_indices:
            topic_terms = self._get_topic_terms(words, topic_idx)
            topic_distribution = self._get_topic_weights(topic_weights, topic_idx)
            pairs = [
                (word, weight)
                for word, weight in zip(topic_terms, topic_distribution)
                if pd.notna(weight) and weight > 0
            ]
            if not pairs:
                continue
            formatted_pairs = ", ".join(
                f"{word} ({weight:.3f})" for word, weight in pairs[:max_terms]
            )
            sections.append(f"- Topic {topic_idx + 1}: {formatted_pairs}")
        if not sections:
            return None
        return "## Top Terms Used\n" + "\n".join(sections)

    def _build_temporal_summary(self, topic_counts: pd.DataFrame, model_type: str) -> Optional[str]:
        if topic_counts.empty:
            return None
        years = topic_counts.index.astype(int)
        start_year = int(years.min())
        end_year = int(years.max())
        num_topics = topic_counts.shape[1]
        topic_lines: List[str] = []
        for topic_idx, series in topic_counts.items():
            active = series[series > 0]
            if active.empty:
                continue
            total = int(active.sum())
            first_year = int(active.index.min())
            last_year = int(active.index.max())
            peak_year = int(active.idxmax())
            peak_count = int(active.max())
            per_year = ", ".join(
                f"{int(year)} ({int(count)})" for year, count in active.items()
            )
            topic_lines.append(
                f"- Topic {topic_idx + 1}: {total} papers | Active {first_year}–{last_year} | "
                f"Peak {peak_year} ({peak_count}) | Year counts: {per_year}"
            )
        if not topic_lines:
            return None
        header = (
            "## Topic Evolution Summary\n"
            f"- Model: {model_type}\n"
            f"- Years covered: {start_year}–{end_year}\n"
            f"- Topics tracked: {num_topics}\n"
            "\n### Topic Activity\n"
        )
        return header + "\n".join(topic_lines)
