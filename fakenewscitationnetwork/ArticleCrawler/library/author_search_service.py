from typing import List, Optional
import logging
from ArticleCrawler.api.base_api import BaseAPIProvider
from ArticleCrawler.library.models import AuthorInfo


class AuthorSearchService:
    """
    Handles author search and selection via OpenAlex API.
    
    This service provides functionality to:
    - Search for authors by name
    - Present search results to users
    - Handle author disambiguation
    """
    
    def __init__(
        self, 
        api_provider: BaseAPIProvider,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize author search service.
        
        Args:
            api_provider: API provider with search_authors method
            logger: Logger instance
        """
        self.api_provider = api_provider
        self.logger = logger or logging.getLogger(__name__)
    
    def search_authors(
        self, 
        author_name: str, 
        limit: int = 10
    ) -> List[AuthorInfo]:
        """
        Search for authors by name.
        
        Args:
            author_name: Author name to search for
            limit: Maximum number of results to return
            
        Returns:
            List of AuthorInfo objects matching the search
        """
        self.logger.info(f"Searching for authors matching: {author_name}")
        
        authors = self.api_provider.search_authors(author_name, limit=limit)
        
        if not authors:
            self.logger.warning(f"No authors found for: {author_name}")
        else:
            self.logger.info(f"Found {len(authors)} authors")
        
        return authors
    
    def get_author_by_id(self, author_id: str) -> Optional[AuthorInfo]:
        """
        Get a specific author by their OpenAlex ID.
        
        Args:
            author_id: OpenAlex author ID
            
        Returns:
            AuthorInfo object or None if not found
        """
        authors = self.api_provider.search_authors(author_id, limit=1)
        
        if authors and authors[0].id == author_id:
            return authors[0]
        
        self.logger.warning(f"Author not found: {author_id}")
        return None
    
    def select_best_match(
        self, 
        authors: List[AuthorInfo],
        criteria: str = "works_count"
    ) -> Optional[AuthorInfo]:
        """
        Automatically select the best matching author based on criteria.
        
        Args:
            authors: List of author candidates
            criteria: Selection criteria ('works_count', 'cited_by_count')
            
        Returns:
            Best matching AuthorInfo or None if list is empty
        """
        if not authors:
            return None
        
        if criteria == "works_count":
            return max(authors, key=lambda a: a.works_count)
        elif criteria == "cited_by_count":
            return max(authors, key=lambda a: a.cited_by_count)
        else:
            return authors[0]