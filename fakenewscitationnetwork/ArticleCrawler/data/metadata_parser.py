"""
Metadata Parsing Operations

Handles parsing of paper metadata, authors, citations, references,
and abstracts from API responses into DataFrames.
"""

import pandas as pd
import numpy as np
from pandas.api import types as pd_types
import logging
from itertools import chain
import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="Setting an item of incompatible dtype is deprecated",
)


class MetadataParser:
    """
    Parses paper data from API responses into DataFrames.
    
    This class handles all parsing operations including metadata extraction,
    author processing, citation/reference parsing, and feature computation.
    """
    
    def __init__(self, store, feature_computer, logger=None):
        """
        Initialize the parser.
        
        Args:
            store: DataFrameStore instance for data access
            feature_computer: AcademicFeatureComputer instance
            logger: Optional logger instance
        """
        self.store = store
        self.feature_computer = feature_computer
        self.logger = logger or logging.getLogger(__name__)
    def _coerce_value_for_column(self, column, value):
        series = self.store.df_paper_metadata[column]
        if pd_types.is_object_dtype(series.dtype):
            return value if value is not None else ""
        if pd_types.is_bool_dtype(series.dtype):
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in ('', '0', 'false', 'no', 'n', 'none'):
                    return False
                if normalized in ('true', '1', 'yes', 'y'):
                    return True
            if pd.isna(value) or value in (None, '', 0):
                return False
            return bool(value)
        if pd_types.is_numeric_dtype(series.dtype):
            if value in (None, '') or (isinstance(value, str) and value.strip() == ''):
                return 0 if pd_types.is_integer_dtype(series.dtype) else np.nan
            try:
                return int(value) if pd_types.is_integer_dtype(series.dtype) else float(value)
            except (TypeError, ValueError):
                return 0 if pd_types.is_integer_dtype(series.dtype) else np.nan
        return value
    
    def parse_metadata(self, papers, processed=True):
        """
        Parse paper metadata and add to DataFrame.
        
        Args:
            papers: List of paper objects from API
            processed: Whether papers are fully processed
        """
        existing_paper_ids = set(self.store.df_paper_metadata['paperId'].values)
        data = []

        for paper in papers:
            paper_id = paper.paperId
            paper_dict = paper2dict(paper, processed=processed, columns=self.store.df_paper_metadata.columns)

            if paper_id not in existing_paper_ids:
                data.append(paper_dict)
                existing_paper_ids.add(paper_id)
            else:
                # update existing row with refreshed metadata
                mask = self.store.df_paper_metadata['paperId'] == paper_id
                target_index = self.store.df_paper_metadata.index[mask]
                if target_index.empty:
                    continue
                for column, value in paper_dict.items():
                    if column == 'paperId':
                        continue
                    coerced_value = self._coerce_value_for_column(column, value)
                    if len(target_index) == 1:
                        self.store.df_paper_metadata.at[target_index[0], column] = coerced_value
                    else:
                        self.store.df_paper_metadata.loc[mask, column] = [coerced_value] * len(target_index)

        if data:
            df = pd.DataFrame(data)
            self.store.df_paper_metadata = pd.concat(
                [self.store.df_paper_metadata, df], ignore_index=True
            )
            self.store.df_paper_metadata = self.store.df_paper_metadata.astype({'processed': bool})
    
    def parse_author(self, papers):
        """
        Parse author information from papers.
        
        Args:
            papers: List of paper objects from API
        """
        def _process_authors(paper_id, authors):
            return [{'paperId': paper_id, 'authorId': author.authorId} 
                   for author in authors if author.authorId]
        
        self.logger.info('Parsing authors')

        data_paper_author = []

        for paper in papers:
            data_paper_author.extend(_process_authors(paper_id=paper.paperId, authors=paper.authors))

            for citation in paper.citations:
                data_paper_author = data_paper_author + _process_authors(
                    paper_id=citation.paperId, authors=citation.authors
                )
            
            for reference in paper.references:
                data_paper_author = data_paper_author + _process_authors(
                    paper_id=reference.paperId, authors=reference.authors
                )

        data_author = [
            {'authorId': author.authorId, 'authorName': author.name}
            for paper in papers
            for author in chain(paper.authors, *(c.authors for c in chain(paper.references, paper.citations)))
            if author.authorId
        ]

        self.store.df_paper_author = pd.concat(
            [self.store.df_paper_author, pd.DataFrame(data_paper_author)], ignore_index=True
        )
        self.store.df_paper_author.drop_duplicates(inplace=True)
        self.store.df_paper_author.reset_index(drop=True, inplace=True)

        self.store.df_author = pd.concat(
            [self.store.df_author, pd.DataFrame(data_author)], ignore_index=True
        )
        self.store.df_author.drop_duplicates(inplace=True)
        self.store.df_author.reset_index(drop=True, inplace=True)
    
    def parse_citations(self, papers, validator):
        """
        Parse citation information from papers.
        
        Args:
            papers: List of paper objects from API
            validator: PaperValidator instance for validation
        """
        self.logger.info('Parsing citations')

        data = []
        for paper in papers:
            paperId = paper.paperId

            citations = validator.checkPapersOpenAlex(paper.citations, processed=False)

            for c in citations:
                data.append({
                    'paperId': paperId,
                    'citedPaperId': c.paperId
                })

            self.parse_metadata(citations, processed=False)

        self.store.df_paper_citations = pd.concat(
            [self.store.df_paper_citations, pd.DataFrame(data)], ignore_index=True
        )
        self.store.df_paper_citations.drop_duplicates(inplace=True)
        self.store.df_paper_citations.reset_index(drop=True, inplace=True)
    
    def parse_references(self, papers, validator):
        """
        Parse reference information from papers.
        
        Args:
            papers: List of paper objects from API
            validator: PaperValidator instance for validation
        """
        self.logger.info('Parsing references')
        data = []
        for paper in papers:
            paperId = paper.paperId

            references = validator.checkPapersOpenAlex(paper.references, processed=False)

            for c in references:
                data.append({
                    'paperId': paperId,
                    'referencePaperId': c.paperId
                })

            self.parse_metadata(references, processed=False)

        self.store.df_paper_references = pd.concat(
            [self.store.df_paper_references, pd.DataFrame(data)], ignore_index=True
        )
        self.store.df_paper_references.drop_duplicates(inplace=True)
        self.store.df_paper_references.reset_index(drop=True, inplace=True)
    
    def parse_abstracts(self, papers):
        """
        Parse abstracts from papers - OpenAlex compatible version.
        
        This version handles None abstracts from OpenAlex gracefully.
        
        Args:
            papers: List of paper objects from API
        """
        initial_shape = self.store.df_abstract.shape[0]
        
        data = []
        for paper in papers:
            abstract = paper.abstract if hasattr(paper, 'abstract') else None
            if abstract is not None and abstract.strip():
                data.append({'paperId': paper.paperId, 'abstract': abstract})
    
        if data:
            self.store.df_abstract = pd.concat(
                [self.store.df_abstract, pd.DataFrame(data)], ignore_index=True
            ) 
            self.store.df_abstract.drop_duplicates(inplace=True)
            self.store.df_abstract.reset_index(drop=True, inplace=True)
        
        self.logger.info(
            f'Parsing abstracts ended. Change in number of rows: {self.store.df_abstract.shape[0] - initial_shape}'
        )
    
    def compute_features(self):
        """
        Compute and update features for papers, authors, and venues.
        """
        self.store.df_paper_metadata = self.feature_computer.compute_paper_features(
            df_paper_metadata=self.store.df_paper_metadata, 
            df_abstract=self.store.df_abstract
        )

        df_paper_citations_reversed = self.store.df_paper_citations.rename(
            columns={'paperId': 'referencePaperId', 'citedPaperId': 'paperId'}
        )

        self.store.df_citations = pd.concat(
            [self.store.df_paper_references, df_paper_citations_reversed], ignore_index=True
        )

        self.store.df_author = self.feature_computer.compute_author_features(
            df_paper_author=self.store.df_paper_author, 
            df_author=self.store.df_author,
            df_paper_metadata=self.store.df_paper_metadata,
            df_citations=self.store.df_citations
        )

        self.store.df_venue_features = self.feature_computer.compute_venue_features(
            self.store.df_paper_metadata,
            self.store.df_citations
        )


def paper2dict(paper, processed, columns):
    """
    Convert paper object to dictionary for DataFrame insertion.
    
    Args:
        paper: Paper object with attributes
        processed: Boolean indicating if paper is processed
        columns: List of column names for the DataFrame
        
    Returns:
        Dictionary with paper data
    """
    paper_dict = dict(paper.__dict__)
    paper_dict['processed'] = processed
    
    return {col: _normalize_paper_value(paper_dict.get(col, '')) for col in columns}


def _normalize_paper_value(value):
    """
    Convert nested PaperObject/list structures into plain Python types.
    """
    if isinstance(value, list):
        return [_normalize_paper_value(item) for item in value]
    if hasattr(value, '__dict__'):
        return {key: _normalize_paper_value(val) for key, val in value.__dict__.items()}
    return value
