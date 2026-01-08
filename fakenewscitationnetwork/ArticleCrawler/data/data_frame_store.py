"""
DataFrame Storage Layer

Pure data storage without business logic. Handles initialization
and basic access to all DataFrames used in the crawler.
"""

import pandas as pd
import logging


class DataFrameStore:
    """
    Manages all DataFrame storage for the crawler.
    
    This class is responsible only for DataFrame initialization and storage.
    All business logic (parsing, validation, computation) is handled elsewhere.
    """
    
    def __init__(self, logger=None):
        """
        Initialize all DataFrames with proper schemas.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        self.df_paper_metadata = pd.DataFrame({
            'paperId': pd.Series(dtype='str'),
            'doi': pd.Series(dtype='str'),   
            'venue': pd.Series(dtype='str'),
            'year': pd.Series(dtype='int'),
            'title': pd.Series(dtype='str'),
            'url': pd.Series(dtype='str'),
            'concepts': pd.Series(dtype='object'),
            'topics': pd.Series(dtype='object'),
            'subfields': pd.Series(dtype='object'),
            'fields': pd.Series(dtype='object'),
            'domains': pd.Series(dtype='object'),
            'processed': pd.Series(dtype='bool'),
            'isSeed': pd.Series(dtype='bool'),
            'isKeyAuthor': pd.Series(dtype='bool'),
            'selected': pd.Series(dtype='bool'),
            'retracted': pd.Series(dtype='bool')
        })
        
        self.df_paper_author = pd.DataFrame(columns=['paperId', 'authorId'])
        self.df_author = pd.DataFrame(columns=['authorName', 'authorId'])
        self.df_paper_citations = pd.DataFrame(columns=['paperId', 'citedPaperId'])
        self.df_paper_references = pd.DataFrame(columns=['paperId', 'referencePaperId'])
        self.df_citations = pd.DataFrame(columns=['paperId', 'referencePaperId'])
        
        self.df_abstract = pd.DataFrame(columns=['paperId', 'abstract'])
        
        self.df_derived_features = pd.DataFrame(
            columns=['nodeId', 'centrality (in)', 'centrality (out)', 'attribute', 'nodeType']
        )
        self.df_venue_features = pd.DataFrame(columns=['venue', 'num_papers'])
        
        self.df_forbidden_entries = pd.DataFrame({
            'paperId': pd.Series(dtype='str'),
            'doi': pd.Series(dtype='str'),
            'reason': pd.Series(dtype='str'),
            'sampler': pd.Series(dtype='bool'),
            'textProcessing': pd.Series(dtype='bool'),
        })
    
    def get_dataframes_shapes(self) -> pd.DataFrame:
        """
        Get shapes of all DataFrames for debugging/monitoring.
        
        Returns:
            DataFrame with frame names and their shapes
        """
        data = [
            {'frame': 'df_paper_metadata', 'shape': self.df_paper_metadata.shape},
            {'frame': 'df_author', 'shape': self.df_author.shape},
            {'frame': 'df_paper_citations', 'shape': self.df_paper_citations.shape},
            {'frame': 'df_paper_references', 'shape': self.df_paper_references.shape},
            {'frame': 'df_derived_features', 'shape': self.df_derived_features.shape},
            {'frame': 'df_abstract', 'shape': self.df_abstract.shape}
        ]
        return pd.DataFrame(data)
    
    def get_num_processed_papers(self) -> tuple:
        """
        Get count of processed and unprocessed papers.
        
        Returns:
            Tuple of (processed_count, unprocessed_count)
        """
        n_processed = self.df_paper_metadata.processed.values.sum()
        total = self.df_paper_metadata.shape[0]
        return n_processed, total - n_processed
