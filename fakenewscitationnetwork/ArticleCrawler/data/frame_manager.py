"""
Frame Manager - Refactored with Separation of Concerns

This module orchestrates data processing operations by delegating to
specialized components:
- DataFrameStore: Pure DataFrame storage
- MetadataParser: Parsing operations
- PaperValidator: Validation logic
- AcademicFeatureComputer: Feature computation

All existing functionality is preserved with improved maintainability.
"""

import pandas as pd
import logging
from .data_frame_store import DataFrameStore
from .metadata_parser import MetadataParser
from .paper_validator import PaperValidator


class FrameManager:
    """
    Orchestrates data processing operations.
    
    This class maintains backward compatibility while delegating
    responsibilities to focused components.
    """
    
    def __init__(self, reporting_options=None, graph_options=None, data_storage_options=None, logger=None):
        """
        Initialize Frame Manager.
        
        Args:
            reporting_options: Legacy parameter (kept for compatibility)
            graph_options: Legacy parameter (kept for compatibility)
            data_storage_options: Storage configuration
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        self.store = DataFrameStore(logger=self.logger)
        self.feature_computer = AcademicFeatureComputer()
        self.parser = MetadataParser(self.store, self.feature_computer, self.logger)
        self.validator = PaperValidator(self.logger)
        
        # Legacy configuration storage
        self.reporting_options = reporting_options
        self.graph_options = graph_options
        self.data_storage_options = data_storage_options
    
    # Expose DataFrames directly for backward compatibility
    
    @property
    def df_paper_metadata(self):
        return self.store.df_paper_metadata
    
    @df_paper_metadata.setter
    def df_paper_metadata(self, value):
        self.store.df_paper_metadata = value
    
    @property
    def df_paper_author(self):
        return self.store.df_paper_author
    
    @df_paper_author.setter
    def df_paper_author(self, value):
        self.store.df_paper_author = value
    
    @property
    def df_author(self):
        return self.store.df_author
    
    @df_author.setter
    def df_author(self, value):
        self.store.df_author = value
    
    @property
    def df_paper_citations(self):
        return self.store.df_paper_citations
    
    @df_paper_citations.setter
    def df_paper_citations(self, value):
        self.store.df_paper_citations = value
    
    @property
    def df_paper_references(self):
        return self.store.df_paper_references
    
    @df_paper_references.setter
    def df_paper_references(self, value):
        self.store.df_paper_references = value
    
    @property
    def df_citations(self):
        return self.store.df_citations
    
    @df_citations.setter
    def df_citations(self, value):
        self.store.df_citations = value
    
    @property
    def df_abstract(self):
        return self.store.df_abstract
    
    @df_abstract.setter
    def df_abstract(self, value):
        self.store.df_abstract = value
    
    @property
    def df_derived_features(self):
        return self.store.df_derived_features
    
    @df_derived_features.setter
    def df_derived_features(self, value):
        self.store.df_derived_features = value
    
    @property
    def df_forbidden_entries(self):
        return self.store.df_forbidden_entries
    
    @df_forbidden_entries.setter
    def df_forbidden_entries(self, value):
        self.store.df_forbidden_entries = value
    
    @property
    def df_venue_features(self):
        return self.store.df_venue_features
    
    @df_venue_features.setter
    def df_venue_features(self, value):
        self.store.df_venue_features = value
    
    
    def set_paper_id_seed_flag(self, paper_id_seed):
        """Set the isSeed column for the given seed paper IDs."""
        if not isinstance(paper_id_seed, list):
            self.logger.error("Input paper_id_seed must be a list.")
            return

        self.store.df_paper_metadata.loc[
            self.store.df_paper_metadata['paperId'].isin(paper_id_seed), 'isSeed'
        ] = True
        self.store.df_paper_metadata.loc[
            self.store.df_paper_metadata['paperId'].isin(paper_id_seed), 'selected'
        ] = True

        self.store.df_paper_metadata['selected'] = (
            self.store.df_paper_metadata['selected'].fillna(False).astype(bool)
        )

        self.logger.info(f"Set isSeed flag for {len(paper_id_seed)} paper IDs.")
    
    def set_key_author_flag(self, paper_id):
        """Set the isKeyAuthor column for the given paper IDs."""
        if not isinstance(paper_id, list):
            self.logger.error("Input paper_id must be a list.")
            return

        self.store.df_paper_metadata.loc[
            self.store.df_paper_metadata['paperId'].isin(paper_id), 'isKeyAuthor'
        ] = True
        self.store.df_paper_metadata.loc[
            self.store.df_paper_metadata['paperId'].isin(paper_id), 'selected'
        ] = True

        self.store.df_paper_metadata['selected'] = (
            self.store.df_paper_metadata['selected'].fillna(False).astype(bool)
        )

        self.logger.info(f"Set isKeyAuthor flag for {len(paper_id)} paper IDs.")
    
    def process_data(self, papers, processed=True):
        """
        Process papers data through all processing steps.
        
        This is the main entry point for processing retrieved papers.
        
        Args:
            papers: List of paper objects from API
            processed: Whether papers are fully processed
        """
        papers = self.validator.checkPapersOpenAlex(papers, processed)

        self.parser.parse_metadata(papers, processed)

        num_missing = self.store.df_paper_metadata["paperId"].isna().sum()
        num_empty = (self.store.df_paper_metadata["paperId"] == "").sum()
        if num_missing > 0 or num_empty > 0:
            self.logger.warning(f"Missing (None/NaN): {num_missing}, Empty Strings: {num_empty}")
            missing_rows = self.store.df_paper_metadata[self.store.df_paper_metadata["paperId"].isna()]
            self.logger.warning(f"Missing rows: {missing_rows}")

        self.parser.parse_author(papers)

        self.parser.parse_citations(papers, self.validator)

        self.parser.parse_references(papers, self.validator)

        self.parser.parse_abstracts(papers)

        self.parser.compute_features()
    
    def update_failed_papers(self, failed_paper_ids):
        """Update the processed status for failed paper IDs."""
        if not failed_paper_ids:
            return

        for paper_id in failed_paper_ids:
            if paper_id in self.store.df_paper_metadata['paperId'].values:
                self.store.df_paper_metadata.loc[
                    self.store.df_paper_metadata['paperId'] == paper_id, 'processed'
                ] = False
                self.logger.info(
                    f"Updated paper ID {paper_id} to processed=False due to retrieval failure."
                )
            else:
                self.logger.warning(f"Paper ID {paper_id} not found in metadata DataFrame.")
    
    def get_dataframes_shapes(self):
        """Get shapes of all DataFrames."""
        return self.store.get_dataframes_shapes()
    
    def get_num_processed_papers(self):
        """Get count of processed and unprocessed papers."""
        return self.store.get_num_processed_papers()
    
    # Backward Compatibility Methods
    
    def checkPapers(self, papers, processed):
        """
        Legacy paper validation method (kept for compatibility).
        Delegates to validator.
        """
        return self.validator.checkPapers(papers, processed)
    
    def checkPapersOpenAlex(self, papers, processed):
        """
        Enhanced paper validation for OpenAlex data.
        Delegates to validator.
        """
        return self.validator.checkPapersOpenAlex(papers, processed)
    
    # Data Cleaning Methods
    
    def remove_unwanted_papers(self, unwanted_papers):
        """Remove rows where paperId is in unwanted_papers."""
        self.store.df_paper_metadata = self.store.df_paper_metadata[
            ~self.store.df_paper_metadata['paperId'].isin(unwanted_papers['paperId'])
        ]
        
        self.store.df_paper_citations = self.store.df_paper_citations[
            ~(self.store.df_paper_citations['paperId'].isin(unwanted_papers['paperId']) | 
              self.store.df_paper_citations['citedPaperId'].isin(unwanted_papers['paperId']))
        ]

        self.store.df_paper_references = self.store.df_paper_references[
            ~(self.store.df_paper_references['paperId'].isin(unwanted_papers['paperId']) | 
              self.store.df_paper_references['referencePaperId'].isin(unwanted_papers['paperId']))
        ]
    
    def remove_unwanted_authors(self, removed_paper_ids):
        """Remove authors associated with removed papers."""
        self.store.df_paper_author = self.store.df_paper_author[
            ~self.store.df_paper_author['paperId'].isin(removed_paper_ids)
        ]

        author_ids_to_remove = (
            set(self.store.df_author['authorId']) - set(self.store.df_paper_author['authorId'])
        )
        self.store.df_author = self.store.df_author[
            ~self.store.df_author['authorId'].isin(author_ids_to_remove)
        ]
    
    def remove_orphan_papers(self):
        """Remove papers with no citations or references."""
        paper_ids_with_citations_or_references = set(self.store.df_paper_metadata['paperId']).intersection(
            set(self.store.df_paper_citations['paperId']).union(
                self.store.df_paper_references['paperId']
            ).union(
                self.store.df_paper_citations['citedPaperId']
            ).union(
                self.store.df_paper_references['referencePaperId']
            )
        ).copy()

        paper_ids_to_remove = (
            set(self.store.df_paper_metadata['paperId']) - paper_ids_with_citations_or_references
        )

        self.store.df_paper_metadata = self.store.df_paper_metadata[
            ~self.store.df_paper_metadata['paperId'].isin(paper_ids_to_remove)
        ]
    
    def remove_abstracts(self, removed_paper_ids):
        """Remove abstracts for removed papers."""
        self.store.df_abstract = self.store.df_abstract[
            ~self.store.df_abstract['paperId'].isin(removed_paper_ids)
        ]
    
    def clean_data_frames(self, unwanted_papers, print_flag=True):
        """
        Clean data frames based on unwanted papers.
        
        Args:
            unwanted_papers: DataFrame of papers to remove
            print_flag: Whether to print before/after statistics
            
        Returns:
            List of removed paper IDs
        """
        if print_flag:
            print("Number of rows before cleaning:")
            print(f"df_paper_metadata: {len(self.store.df_paper_metadata)}")
            print(f"df_paper_citations: {len(self.store.df_paper_citations)}")
            print(f"df_paper_references: {len(self.store.df_paper_references)}")
            print(f"df_author: {len(self.store.df_author)}")
            print(f"df_paper_author: {len(self.store.df_paper_author)}")
            print(f"df_abstract: {len(self.store.df_abstract)}")
        
        original_paperId = set(self.store.df_paper_metadata['paperId']).copy()

        self.remove_unwanted_papers(unwanted_papers)
        
        self.remove_orphan_papers()
        
        removed_paper_ids = list(original_paperId - set(self.store.df_paper_metadata['paperId']))
        
        self.remove_unwanted_authors(removed_paper_ids)
        
        self.remove_abstracts(removed_paper_ids)
        
        if print_flag:
            print("Number of rows after cleaning:")
            print(f"df_paper_metadata: {len(self.store.df_paper_metadata)}")
            print(f"df_paper_citations: {len(self.store.df_paper_citations)}")
            print(f"df_paper_references: {len(self.store.df_paper_references)}")
            print(f"df_author: {len(self.store.df_author)}")
            print(f"df_paper_author: {len(self.store.df_paper_author)}")
            print(f"df_abstract: {len(self.store.df_abstract)}")
        
        return removed_paper_ids


class AcademicFeatureComputer:
    """
    Compute academic features for papers, authors, and venues.
    
    """
    
    def __init__(self, preprint_repo_file="preprint_repo.txt"):
        self.preprint_repositories = self.load_preprint_repositories(preprint_repo_file)
        self.venue_features = None
        self.cleaned_venues = None

    def load_preprint_repositories(self, filename):
        """Load preprint repository names from a file into a list."""
        try:
            with open(filename, 'r') as f:
                preprints = [line.strip() for line in f.readlines()]
            return preprints
        except FileNotFoundError:
            print(f"Error: The file {filename} was not found.")
            return []

    def compute_paper_features(self, df_paper_metadata, df_abstract, 
                              indicators=['review', 'survey', 'tutorial', 'benchmark', 'dataset']):
        """Compute metadata-related features for papers."""
        df_paper_metadata['has_abstract'] = df_paper_metadata['paperId'].isin(df_abstract['paperId'])

        df_paper_metadata['is_preprint'] = df_paper_metadata['venue'].apply(
            lambda x: 1 if str(x).lower() in self.preprint_repositories else 0
        )

        for indicator in indicators:
            df_paper_metadata[f'tc_{indicator}'] = df_paper_metadata['title'].str.contains(
                indicator, case=False, na=False
            )
        
        return df_paper_metadata

    def compute_author_features(self, df_paper_author, df_author, df_paper_metadata, df_citations):
        """Compute citation and co-authorship statistics for authors."""
        with pd.option_context('future.no_silent_downcasting', True):
            num_papers = df_paper_author.groupby('authorId').size().reindex(df_author['authorId']).fillna(0)
            df_author['num_papers'] = num_papers.values

            paper_citations_count = df_citations.groupby('paperId').size().reindex(
                df_paper_metadata['paperId']
            ).fillna(0)
            df_paper_author = df_paper_author.merge(
                paper_citations_count.rename('citation_count'), 
                left_on='paperId', right_index=True, how='left'
            )
            df_paper_author['citation_count'] = df_paper_author['citation_count'].fillna(0)

            author_citations = df_paper_author.groupby('authorId')['citation_count'].sum().reindex(
                df_author['authorId']
            ).fillna(0)
            avg_citations = (author_citations / (df_author['num_papers'].values + 1E-8)).fillna(0)
            max_citations = df_paper_author.groupby('authorId')['citation_count'].max().reindex(
                df_author['authorId']
            ).fillna(0)
            df_author['avg_citations'] = avg_citations.values
            df_author['max_citations'] = max_citations.values
            df_author['num_citations'] = author_citations.values

            co_authors = df_paper_author.groupby('authorId')['paperId'].nunique().reindex(
                df_author['authorId']
            ).fillna(0)
            df_author['num_coauthors'] = co_authors.values

            num_authors = df_paper_author.groupby('paperId')['authorId'].nunique().reindex(
                df_paper_metadata['paperId']
            )
            df_paper_metadata['num_authors'] = num_authors.values
            df_paper_metadata['citation_count'] = paper_citations_count.values

            publication_years = df_paper_metadata.set_index('paperId').reindex(
                df_paper_author['paperId']
            )['year'].fillna(0)
            df_paper_author = df_paper_author.merge(
                publication_years.rename('publication_years'), 
                left_on='paperId', right_index=True, how='left'
            )

            min_py = df_paper_author.groupby('authorId')['publication_years'].min().rename(
                'year_first_publication'
            )
            max_py = df_paper_author.groupby('authorId')['publication_years'].max().rename(
                'year_last_publication'
            )

            df_author = df_author.merge(min_py, on='authorId', how='left', suffixes=('', '_new'))
            if 'year_first_publication_new' in df_author.columns:
                df_author['year_first_publication'] = df_author.pop('year_first_publication_new')

            df_author = df_author.merge(max_py, on='authorId', how='left', suffixes=('', '_new'))
            if 'year_last_publication_new' in df_author.columns:
                df_author['year_last_publication'] = df_author.pop('year_last_publication_new')

        return df_author

    def compute_venue_features(self, df_paper_metadata, df_citations, filter_list=[]):
        """
        Compute citation-related features for venues.
        
        Calculates metrics such as self-citations, citations by other venues, and how often
        a venue's papers are cited by others.
        """
        df_paper_metadata['venue'] = df_paper_metadata['venue'].apply(
            lambda x: None if str(x).lower() in filter_list else x
        )

        self.cleaned_venues = df_paper_metadata['venue'].dropna().unique()
        venue_id_map = {}
        if 'venue_id' in df_paper_metadata.columns:
            venue_id_series = df_paper_metadata[['venue', 'venue_id']].dropna(subset=['venue'])
            for venue_name, group in venue_id_series.groupby('venue'):
                ids = group['venue_id'].dropna()
                if not ids.empty:
                    venue_id_map[venue_name] = ids.iloc[0]

        df_citing = df_paper_metadata[['paperId', 'venue']].rename(
            columns={'paperId': 'paperId', 'venue': 'venue_citing'}
        )
        
        df_cited = df_paper_metadata[['paperId', 'venue']].rename(
            columns={'paperId': 'referencePaperId', 'venue': 'venue_cited'}
        )

        citations_with_venues = df_citations \
            .merge(df_citing, on='paperId', how='left') \
            .merge(df_cited, on='referencePaperId', how='left')

        self_citations = citations_with_venues[
            citations_with_venues['venue_cited'] == citations_with_venues['venue_citing']
        ]
        self_citation_counts = self_citations.groupby('venue_cited').size().rename('self_citations')
        
        citations_by_others = citations_with_venues[
            citations_with_venues['venue_cited'] != citations_with_venues['venue_citing']
        ]
        citations_by_others_counts = citations_by_others.groupby('venue_cited').size().rename('citing_others')

        citations_to_others = citations_with_venues[
            citations_with_venues['venue_cited'] != citations_with_venues['venue_citing']
        ]
        citations_to_others_counts = citations_to_others.groupby('venue_citing').size().rename('being_cited_by_others')

        total_papers_per_venue = df_paper_metadata['venue'].value_counts().rename('total_papers')

        venue_summary = pd.concat([
            total_papers_per_venue,
            self_citation_counts,
            citations_by_others_counts,
            citations_to_others_counts
        ], axis=1).fillna(0)

        venue_summary.columns = ['total_papers', 'self_citations', 'citing_others', 'being_cited_by_others']
        
        venue_summary = venue_summary.reset_index().rename(columns={'index': 'venue'})
        if venue_id_map:
            venue_summary['venue_id'] = venue_summary['venue'].map(venue_id_map).where(
                pd.notna, None
            )
        else:
            venue_summary['venue_id'] = None

        return venue_summary
