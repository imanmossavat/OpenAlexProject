import logging
from typing import List
from ..api.base_api import BaseAPIProvider

class PaperRetrievalService:
    """
    Handles paper retrieval through API providers.
    
    This service is responsible for:
    - Making API calls to retrieve papers
    - Managing retry logic and error handling
    - Tracking failed retrievals
    - Providing access to API provider statistics
    """
    
    def __init__(self, api_provider: BaseAPIProvider, logger=None):
        """
        Initialize the paper retrieval service.
        
        Args:
            api_provider (BaseAPIProvider): The API provider to use for retrievals
            logger: Logger instance for logging events
        """
        self.api = api_provider
        self.logger = logger or logging.getLogger(__name__)
    
    def retrieve_papers(self, paper_ids: List[str]):
        """
        Retrieve papers using the configured API provider.
        
        Args:
            paper_ids (List[str]): List of paper IDs to retrieve
            
        Returns:
            List: List of paper objects (None for failed retrievals)
        """
        if not paper_ids:
            self.logger.info("No paper IDs provided for retrieval.")
            return []

        self.logger.info(f"Retrieving papers for IDs: {paper_ids}")
        papers = self.api.get_papers(paper_ids)
        
        if not papers:
            self.logger.info("No papers retrieved from API.")
            return []
            
        return papers
    
    def retrieve_author_papers(self, author_id: str, *, page: int = 1, page_size: int = 20):
        """
        Retrieve papers for a specific author.
        
        Args:
            author_id (str): The author ID to retrieve papers for
            page (int): Page number
            page_size (int): Page size

        Returns:
            Tuple: (papers list, paper_ids list, total count)
        """
        return self.api.get_author_papers(author_id, page=page, page_size=page_size)
    
    def get_failed_papers(self) -> List[str]:
        """
        Get list of failed paper retrievals.
        
        Returns:
            List[str]: List of paper IDs that failed to retrieve
        """
        return self.api.failed_paper_ids
    
    def get_inconsistent_papers(self) -> List[tuple]:
        """
        Get list of inconsistent paper ID responses.
        
        Returns:
            List[tuple]: List of (requested_id, returned_id) tuples
        """
        return self.api.inconsistent_api_response_paper_ids
    
    def get_retrieval_statistics(self) -> dict:
        """
        Get comprehensive retrieval statistics.
        
        Returns:
            dict: Statistics about failed and inconsistent retrievals
        """
        return self.api.get_failed_and_inconsistent_papers()
