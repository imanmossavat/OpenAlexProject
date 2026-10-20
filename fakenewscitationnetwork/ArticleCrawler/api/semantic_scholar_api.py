"""Semantic Scholar provider (LEGACY / DEPRECATED).

The project moved to OpenAlex because Semantic Scholar became rate limited and
API-key requests went unanswered. See docs/decisions/semantic-scholar-to-openalex.md.

This provider needs the PyS2 library, which is NOT the package called ``s2`` on
PyPI (that one is unrelated and has no ``s2.api``). Install PyS2 from GitHub if
you really need this provider:

    pip install git+https://github.com/mirandrom/PyS2

It is no longer a dependency of this project and is not used by the backend or UI.
"""

import logging
from typing import Dict, List, Optional, Tuple
from .base_api import BaseAPIProvider

try:
    import s2  # https://github.com/mirandrom/PyS2 (not the unrelated 's2' on PyPI)
except ImportError:  # PyS2 is no longer installed by default
    s2 = None


def _require_pys2_api():
    """Return ``s2.api`` or raise a clear error if PyS2 is not installed.

    Called before the provider's try/except blocks, which otherwise swallow the
    failure and make every lookup look like "paper not found".
    """
    api = getattr(s2, "api", None)
    if api is None:
        raise ImportError(
            "The Semantic Scholar provider requires the PyS2 library, which is not installed "
            "(the 's2' package on PyPI is a different, unrelated project).\n"
            "Install it with: pip install git+https://github.com/mirandrom/PyS2\n"
            "Note: this provider is deprecated; use the OpenAlex provider instead."
        )
    return api

class SemanticScholarAPIProvider(BaseAPIProvider):
    """
    Semantic Scholar API provider implementation.
    
    A class responsible for retrieving papers using the PyS2 API and handling inconsistencies 
    and errors during the retrieval process. This class allows for managing failed paper retrievals 
    and logging mismatches in paper IDs returned by the API.

    Attributes:
        wait (int): The time (in seconds) to wait between retries. Default is 150.
        retries (int): The number of retries allowed for paper retrieval. Default is 2.
        failed_paper_ids (list): A list to keep track of paper IDs that failed to retrieve.
        inconsistent_api_response_paper_ids (list): A list to store pairs of requested and returned paper IDs 
                                                      where the retrieved paper does not match the requested one.
        logger (logging.Logger): Logger instance used to log events and errors.
    """

    def __init__(self, wait=150, retries=2, logger=None):
        """
        Initializes the SemanticScholarAPIProvider instance with the provided configuration.

        Args:
            wait (int): The time (in seconds) to wait between retries. Default is 150 seconds.
            retries (int): The number of retries for retrieving papers. Default is 2 retries.
            logger (logging.Logger or None): A custom logger instance. If None, a default logger is created.
        """
        self.wait = wait
        self.retries = retries

        # Use the provided logger, or fall back to a default logger
        if logger is not None:
            self.logger = logger
        else:
            print("WARNING API Caller does not receive a logger! Is this intentional...")
            self.logger = logging.getLogger("SemanticScholarAPIProvider")
            logging.basicConfig(level=logging.INFO)  # Default log level is INFO if no logger is provided

        # List to track failed paper IDs
        self._failed_paper_ids = []
        self._inconsistent_api_response_paper_ids = []

    @property
    def failed_paper_ids(self) -> List[str]:
        """List of failed paper IDs"""
        return self._failed_paper_ids

    @property
    def inconsistent_api_response_paper_ids(self) -> List[tuple]:
        """List of inconsistent paper ID responses"""
        return self._inconsistent_api_response_paper_ids

    def get_paper(self, paper_id: str):
        """
        Retrieves a paper using the provided paper ID. If successful, it checks if the returned paper's 
        ID matches the requested paper ID. If there's a mismatch, it logs the inconsistency and tracks it.

        Args:
            paper_id (str): The ID of the paper to retrieve.

        Returns:
            paper (object or None): The paper retrieved from the API or None if retrieval fails.
        """
        s2_api = _require_pys2_api()
        try:
            paper = s2_api.get_paper(paperId=paper_id, wait=self.wait, retries=self.retries)     
        except Exception as e:
            error_message = f"Error retrieving paper with ID {paper_id}: {str(e)}"
            self.logger.error(error_message)
            
            # Register the failed paper ID if not already present
            if paper_id not in self._failed_paper_ids:
                self._failed_paper_ids.append(paper_id)
            return None
        
        # If paper retrieval is successful, check and remove from failed list
        if paper is not None:
            # Check if the paper returned has the expected paperId
            if paper.paperId != paper_id:
                # Update the inconsistent API response flag
                self._inconsistent_api_response_paper_ids.append((paper_id, paper.paperId))

                # Log the mismatch
                self.logger.warning(f"Mismatch: Retrieved paperId {paper.paperId} does not match requested paperId {paper_id}.")
            
            # If paper_id is in the failed list, remove it
            elif paper_id in self._failed_paper_ids:
                self._failed_paper_ids.remove(paper_id)  # Remove from failed list

        return paper

    def get_papers(self, paper_id_list: List[str]):
        """
        Retrieves multiple papers by their paper IDs using the get_paper method.

        Args:
            paper_id_list (list): A list of paper IDs to retrieve.

        Returns:
            list: A list of papers retrieved from the API (or None if retrieval fails for any).
        """
        results = list(map(self.get_paper, paper_id_list))
        return results

    def get_failed_and_inconsistent_papers(self) -> Dict:
        """
        Returns a dictionary containing two lists:
        - 'failed': List of paper IDs that failed to retrieve.
        - 'inconsistent': List of tuples where the first element is the requested paper ID 
                           and the second element is the retrieved paper ID in case of a mismatch.

        Returns:
            dict: A dictionary with two keys:
                - 'failed': A list of paper IDs that failed to retrieve.
                - 'inconsistent': A list of tuples, each containing the requested paper ID and 
                                  the retrieved paper ID in case of a mismatch.
        """
        return {
            'failed': self._failed_paper_ids,
            'inconsistent': self._inconsistent_api_response_paper_ids
        }

    def get_author_papers(
        self,
        author_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        """
        Retrieves all papers for a given author ID using the Semantic Scholar API.

        Args:
            author_id (str): The ID of the author whose papers need to be retrieved.

        Returns:
            tuple: A tuple containing two lists:
                - A list of paper objects retrieved from the API.
                - A list of paperId values for the retrieved papers.
        """
        s2_api = _require_pys2_api()
        try:
            # Fetch the author data
            author = s2_api.get_author(authorId=author_id)
            
            if author is None:
                self.logger.error(f"Failed to retrieve author with ID {author_id}.")
                return [], [], None

            # Extract the list of papers
            papers = author.papers if hasattr(author, 'papers') else []
            paper_ids = [paper.paperId for paper in papers if hasattr(paper, 'paperId')]
            total = len(papers)

            normalized_page = max(1, int(page or 1))
            normalized_page_size = max(1, int(page_size or 25))
            start = (normalized_page - 1) * normalized_page_size
            end = start + normalized_page_size
            paged_papers = papers[start:end]
            paged_ids = paper_ids[start:end]

            self.logger.info(f"Successfully retrieved {len(paged_papers)} papers for author ID {author_id}.")
            return paged_papers, paged_ids, total

        except Exception as e:
            self.logger.error(f"Error retrieving papers for author ID {author_id}: {str(e)}")
            return [], [], None

    def get_venue_papers(
        self,
        venue_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, List[str], Optional[int]]:
        raise NotImplementedError("Semantic Scholar provider does not support venue-based retrieval.")
