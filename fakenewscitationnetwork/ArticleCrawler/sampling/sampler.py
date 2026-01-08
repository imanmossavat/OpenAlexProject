"""
Sampler for Selecting Research Papers (paperIds) Based on Title Keywords and Citation Network Node Centrality

MINIMAL CHANGES: Only updated to work with DataCoordinator instead of DataManager.
All sampling algorithms and business logic PRESERVED.

This module defines the `Sampler` class, which samples paper IDs using a mix of 
centrality-based and keyword-based criteria, without relying on API calls. The 
sampling logic incorporates both structural centrality from a citation graph 
and relevance to specific keywords, producing a candidate list of papers for further processing.

The class interacts with a data coordinator, updating its records directly, while also 
logging each step of the process for improved traceability.

*Note*: 
The sampler modifies only the 'selected' column of the paper metadata, indicating 
the sampled status. The 'processed' column remains controlled by the data coordinator, 
as it tracks API interactions and cannot be directly modified here.

frames.df_forbidden_entries controls what to sample 
"""

import pandas as pd
import numpy as np
import logging
from typing import List

# For type hinting compatibility with both old and new architecture
try:
    from ArticleCrawler.config import SamplingConfig
except ImportError:
    # Fallback for backward compatibility
    SamplingConfig = None


class Sampler:
    """
    A class to sample research papers based on title keywords and citation centrality metrics.

    MINIMAL CHANGES: Only parameter names updated to work with DataCoordinator.
    All existing sampling logic PRESERVED.

    The `Sampler` class performs multi-step filtering and sampling on a dataset of research papers, 
    considering both structural centrality in the citation network and keyword relevance in the 
    paper metadata. The resulting paper IDs are further filtered by publication venue, and a 
    final selection is made based on calculated sampling probabilities.

    Attributes:
        keywords (list): Keywords for title-based filtering.
        data_coordinator: Coordinator providing data and graph access (replaces data_manager)
        sampling_options: Configurable options for sampling thresholds and parameters.
        logger (Logger): Logger instance for capturing process information.
    
    Key Methods:
        - `prepare_initial_sample()`: Initializes potential sample IDs and excludes already selected/processed papers.
        - `filter_by_keywords()`: Applies keyword-based filtering to refine potential sample candidates.
        - `filter_by_centrality()`: Applies a centrality threshold to include highly central papers.
        - `filter_by_venues()`: Removes papers from venues specified in the ignored venues list.
        - `sample_and_update()`: Finalizes the sampling by selecting papers based on computed probabilities and marking them as sampled in the metadata.
    """
    
    def __init__(self, keywords, data_manager, sampling_options=None, logger=None, 
                 data_storage_options=None, retraction_watch_manager=None):
        """
        Initialize the Sampler instance.
        
        MINIMAL CHANGE: Parameter 'data_manager' now works with both DataManager and DataCoordinator
        through duck typing. All other logic UNCHANGED.

        Args:
            keywords (list): A list of keywords for filtering papers.
            data_manager: The data manager/coordinator instance containing data and graph.
            sampling_options: Options for sampling (SamplingOptions or SamplingConfig).
            logger: Logger instance for logging events.
            data_storage_options: Storage configuration (for logger creation if needed)
            retraction_watch_manager: Manager for retraction checking
        """
        # Set up logger
        if logger is not None:
            self.logger = logger
        elif data_storage_options is not None:
            from ArticleCrawler import CrawlerLogger
            self.logger = CrawlerLogger(data_storage_options)
        else:
            self.logger = logging.getLogger("SamplerLogger")
            logging.basicConfig(level=logging.INFO)

        self.keywords = keywords
        
        # MINIMAL CHANGE: Use data_coordinator internally but accept any name for compatibility
        # This works with both DataManager and DataCoordinator through duck typing
        self.data_coordinator = data_manager
        
        # Handle both old SamplingOptions and new SamplingConfig
        if sampling_options is None:
            # Create default configuration
            if SamplingConfig:
                from ArticleCrawler.config import SamplingConfig
                self.sampling_options = SamplingConfig(num_papers=1, hyper_params={'year': 0.1, 'centrality': 1})
            else:
                # Fallback for backward compatibility
                from ArticleCrawler.config.crawler_initialization import SamplingOptions
                self.sampling_options = SamplingOptions(num_papers=1, hyper_params={'year': 0.1, 'centrality': 1})
        else:
            self.sampling_options = sampling_options
        
        self.no_papers_available = None
        self.num_papers = self.sampling_options.num_papers
        self.hyper_params = self.sampling_options.hyper_params

        self.selected_by_centrality_ids = []
        self.potential_future_sample_ids = []
        self.existing_ids = []
        self.sampled_papers = []

    def calculate_centrality_threshold(self):
        """
        Calculate threshold values based on centrality scores for the potential sample IDs.

        ALL LOGIC UNCHANGED - works with data_coordinator.graph
        """
        df_paper_centrality = self.data_coordinator.graph.get_paper_centralities(self.potential_future_sample_ids)
        df_paper_centrality.fillna(1E-50, inplace=True)

        threshold_out = self._compute_threshold(len(df_paper_centrality))
        threshold_in = self._compute_threshold(len(df_paper_centrality))

        thresholds_df = pd.DataFrame({'threshold_in': threshold_in, 'threshold_out': threshold_out})
        return thresholds_df.max(axis=1).tolist()

    def _compute_threshold(self, size):
        """
        Compute exponential thresholds for given size.
        
        ALL LOGIC UNCHANGED
        """
        return np.exp(-self.sampling_options.no_key_word_lambda * np.arange(size))

    def filter_by_keywords(self):
        """
        Filter the potential sample papers using a keyword-based approach.

        ALL LOGIC UNCHANGED - works with data_coordinator.frames
        """
        # Import here to avoid circular dependencies
        import ArticleCrawler.DataProcessing.data_frame_filter as data_frame_filter

        papers = self.data_coordinator.frames.df_paper_metadata
        papers = papers[papers['paperId'].isin(self.potential_future_sample_ids)]
        filter = data_frame_filter.DataFrameFilter(papers, keywords=self.keywords, logger=self.logger)
        self.potential_future_sample_ids = filter.filter_by_keywords_and_expression('title')

        if len(self.potential_future_sample_ids) != 0:
            self.logger.info(f"Filtered papers by keywords. Count: {self.potential_future_sample_ids.shape[0]}")

    def filter_by_centrality(self, random_samples, threshold):
        """
        Select papers from the potential sample based on centrality thresholds.

        ALL LOGIC UNCHANGED
        """
        self.selected_by_centrality_ids = self.potential_future_sample_ids[random_samples < threshold]
        self.potential_future_sample_ids = self.potential_future_sample_ids[random_samples >= threshold]

    def sample_papers(self):
        """
        Execute the full sampling pipeline based on centrality and keyword filtering.

        ALL LOGIC UNCHANGED - only access through data_coordinator instead of data_manager
        """
        self.potential_future_sample_ids = []

        self.logger.info('Graph calculations started.')
        self.data_coordinator.update_graph_and_calculate_centrality()

        self.prepare_initial_sample()

        threshold = self.calculate_centrality_threshold()
        random_samples = np.random.uniform(size=len(self.potential_future_sample_ids))
        self.filter_by_centrality(random_samples, threshold)
        self.logger.info(f'Bypassed keywords for {len(self.selected_by_centrality_ids)} papers.')

        # Apply stochastic filter by keyword
        self.filter_by_keywords()        
        self.potential_future_sample_ids = pd.concat([self.potential_future_sample_ids, self.selected_by_centrality_ids])

        self.logger.info(f"Count of potential papers after keyword filtering: {len(self.potential_future_sample_ids)}")

        # Filter papers by venues
        self._filter_papers_by_venues()
        self.logger.info(f"Count of unselected papers after filtering by venues: {len(self.potential_future_sample_ids)}")

        if len(self.potential_future_sample_ids) == 0:
            self.no_papers_available = True
            self.logger.info("Not enough papers available for sampling.")

        self._compute_probabilities()

        # Sample papers based on computed probabilities
        self.sample_papers_by_probability()

        # Retrieve and mark sampled papers as selected
        self.update_metadata_with_selection()

    def prepare_initial_sample(self):
        """
        Prepare the initial sample space by identifying papers that are:
        - Unselected (not sampled yet)
        - Unprocessed (not queried via API)
        - Not in the forbidden list
        
        ALL LOGIC UNCHANGED - works with data_coordinator.frames
        """
        if hasattr(self.data_coordinator, 'frames') and hasattr(self.data_coordinator.frames, 'df_paper_metadata'):
            if 'selected' in self.data_coordinator.frames.df_paper_metadata.columns:
                
                papers = self.data_coordinator.frames.df_paper_metadata
                
                # Retrieve forbidden entries safely
                df_forbidden_entries = getattr(self.data_coordinator.frames, 'df_forbidden_entries', None)
                forbidden_ids = []
                if df_forbidden_entries is not None and 'paperId' in df_forbidden_entries.columns:
                    forbidden_ids = df_forbidden_entries[df_forbidden_entries['sampler'] == True]['paperId'].tolist()
                    
                    if forbidden_ids:
                        self.logger.info(f"Found {len(forbidden_ids)} forbidden entries. They will be excluded from sampling.")
                    else:
                        self.logger.info("No forbidden entries found.")
                else:
                    self.logger.warning("df_forbidden_entries is missing or does not contain 'paperId'.")

                # Exclude selected, processed, and forbidden papers
                self.existing_ids = papers[
                    (papers['selected'] == True) | 
                    (papers['processed'] == True) | 
                    (papers['paperId'].isin(forbidden_ids))
                ]['paperId']

                self.potential_future_sample_ids = papers[~papers['paperId'].isin(self.existing_ids)]['paperId']

                self.logger.info(f"Count of unselected and non-forbidden papers: {len(self.potential_future_sample_ids)}")

            else:
                self.logger.error("'selected' column does not exist in df_paper_metadata.")
        else:
            self.logger.error("Data coordinator does not have the required frames or df_paper_metadata.")

    def sample_papers_by_probability(self):
        """
        Select the final paper samples based on computed probabilities.

        ALL LOGIC UNCHANGED
        """
        paperIds, probabilities = self.potential_future_sample_ids, self.probabilities
        self.logger.info("Sampling papers...")
        self.potential_future_sample_ids = np.random.choice(
            paperIds, size=min(self.num_papers, len(paperIds)), replace=False, p=probabilities
        )
        self.logger.info(f"Papers sampled. Count: {len(self.potential_future_sample_ids)}")

    def update_metadata_with_selection(self):
        """
        Update the paper metadata DataFrame to mark sampled papers as selected.

        ALL LOGIC UNCHANGED - works with data_coordinator.frames
        """
        self.sampled_papers = self.potential_future_sample_ids

        self.data_coordinator.frames.df_paper_metadata.loc[
            self.data_coordinator.frames.df_paper_metadata['paperId'].isin(self.sampled_papers), 'selected'
        ] = True

    def _filter_papers_by_venues(self):         
        """
        Enhanced venue filtering for OpenAlex data.
        
        ALL LOGIC UNCHANGED - works with data_coordinator.frames
        """
        papers = self.data_coordinator.frames.df_paper_metadata
        
        if self.sampling_options.ignored_venues:
            # Enhanced filtering to handle missing/empty venues
            filtered_ids = papers[
                papers['paperId'].isin(self.potential_future_sample_ids) &
                papers['venue'].notna() &
                (papers['venue'] != '') &
                (papers['venue'].str.len() > 0) &
                ~papers['venue'].isin(self.sampling_options.ignored_venues)
            ]['paperId'].tolist()

            self.potential_future_sample_ids = filtered_ids
            self.logger.info("Venue filtering removed papers with missing venues or ignored venues")

    def _compute_probabilities(self):
        """
        Compute probabilities for unselected papers based on centrality.

        ALL LOGIC UNCHANGED - works with data_coordinator.graph and data_coordinator.frames
        """
        self.logger.info("Computing probabilities for unselected papers...")
        df_paper_centrality = self.data_coordinator.graph.get_paper_centralities(self.potential_future_sample_ids)

        none_count = df_paper_centrality.isnull().sum().sum()
        if none_count:
            self.logger.info("Number of entries with None centrality values: %d", none_count)
            small_number = 10E-6 / (df_paper_centrality.shape[0] + 1)
            df_paper_centrality.fillna(small_number, inplace=True)

        papers_years = self.data_coordinator.frames.df_paper_metadata[
            self.data_coordinator.frames.df_paper_metadata['paperId'].isin(self.potential_future_sample_ids)
        ][['paperId', 'year']]

        merged_df = pd.merge(df_paper_centrality, papers_years, on='paperId', how='left')
        self.logger.info(f"Probabilities computed for unselected papers. Count: {len(merged_df)}")

        year = merged_df['year']
        centrality_column_names = [col for col in merged_df.columns if 'centrality' in col]
        centrality_values = merged_df[centrality_column_names].values

        probabilities = self._compute_paper_probability(year=year, centrality_values=centrality_values)
        self.potential_future_sample_ids = merged_df.paperId
        self.probabilities = probabilities

    def _compute_paper_probability(self, year, centrality_values):
        """
        Compute the final probabilities for papers based on year and centrality values.

        ALL LOGIC UNCHANGED
        """
        year_prob = self._compute_year_probability(year)
        centrality_prob = self._compute_centrality_probability(centrality_values)
        probabilities = year_prob * centrality_prob
        return self.normalize_probabilities(probabilities)

    def _compute_year_probability(self, year):
        """
        Compute the probability based on publication year.

        ALL LOGIC UNCHANGED
        """
        current_year = pd.to_datetime('today').year
        diff = current_year - year
        return np.exp(-self.hyper_params['year'] * diff.values.astype(float))

    def _compute_centrality_probability(self, centrality):
        """
        Compute probabilities based on centrality values.

        ALL LOGIC UNCHANGED
        """
        if centrality is None or np.all(centrality == None):
            self.logger.info("All centrality values are None.")
            return None
        max_centrality = np.nanmax(centrality, axis=1)
        return max_centrality

    def normalize_probabilities(self, probabilities):
        """
        Normalize the input probabilities to ensure they sum to 1.

        ALL LOGIC UNCHANGED
        """
        if np.any(probabilities <= 0):
            self.logger.info(f'Warning: negative values detected in probabilities. Count: {np.sum(probabilities <= 0)}')
            probabilities[probabilities <= 0] = 1E-50
        nan_indices = np.isnan(probabilities)
        if np.any(nan_indices):
            self.logger.info(f'Warning: NaN values detected in probabilities. Count: {np.sum(nan_indices)}')
            probabilities[nan_indices] = 1E-50

        return probabilities / np.sum(probabilities)