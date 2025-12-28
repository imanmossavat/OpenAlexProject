from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

class BaseAPIProvider(ABC):
    """Abstract base class for API providers (Semantic Scholar, OpenAlex, etc.)"""
    
    @abstractmethod
    def get_paper(self, paper_id: str):
        """
        Retrieve a single paper by ID.
        
        Args:
            paper_id (str): The ID of the paper to retrieve
            
        Returns:
            Paper object or None if retrieval fails
        """
        pass
    
    @abstractmethod
    def get_papers(self, paper_ids: List[str]):
        """
        Retrieve multiple papers by IDs.
        
        Args:
            paper_ids (List[str]): List of paper IDs to retrieve
            
        Returns:
            List of paper objects (None for failed retrievals)
        """
        pass
    
    @abstractmethod
    def get_author_papers(
        self,
        author_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        """
        Retrieve papers for an author.
        
        Args:
            author_id (str): The ID of the author
            page (int): Page number (1-indexed)
            page_size (int): Number of papers per page
            
        Returns:
            Tuple of (paper objects list, paper IDs list, total available count)
        """
        pass

    @abstractmethod
    def get_venue_papers(
        self,
        venue_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        """
        Retrieve papers for a venue/journal host.

        Args:
            venue_id (str): The OpenAlex venue identifier
            page (int): Page number (1-indexed)
            page_size (int): Number of papers per page

        Returns:
            Tuple of (paper objects list, paper IDs list, total available count)
        """
        pass
    
    @abstractmethod
    def get_failed_and_inconsistent_papers(self) -> Dict:
        """
        Get failed and inconsistent paper retrievals.
        
        Returns:
            Dict with 'failed' and 'inconsistent' keys containing lists
        """
        pass
    
    @property
    @abstractmethod
    def failed_paper_ids(self) -> List[str]:
        """List of failed paper IDs"""
        pass
    
    @property
    @abstractmethod
    def inconsistent_api_response_paper_ids(self) -> List[tuple]:
        """List of inconsistent paper ID responses"""
        pass
