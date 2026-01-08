"""
Paper Validation Operations

Handles validation of paper objects from API responses to ensure
they have required attributes and valid data.
"""

import logging


class PaperValidator:
    """
    Validates paper objects from API responses.
    
    Different validation methods for different API providers
    (e.g., OpenAlex vs Semantic Scholar).
    """
    
    def __init__(self, logger=None):
        """
        Initialize the validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def checkPapers(self, papers, processed):
        """
        Legacy paper validation method (kept for compatibility).
        
        Use checkPapersOpenAlex for better OpenAlex compatibility.
        
        Args:
            papers: List of paper objects
            processed: Whether to check for abstract requirement
            
        Returns:
            List of validated paper objects
        """
        if processed:
            condition = lambda paper: (
                hasattr(paper, 'abstract') and 
                hasattr(paper, 'title') and 
                hasattr(paper, 'paperId') and 
                paper.paperId is not None and 
                isinstance(paper.paperId, str) and 
                paper.paperId.strip() != "" and
                not isinstance(paper.paperId, float)
            )
        else:
            condition = lambda paper: (
                hasattr(paper, 'title') and 
                hasattr(paper, 'paperId') and 
                paper.paperId is not None and 
                isinstance(paper.paperId, str) and 
                paper.paperId.strip() != "" and
                not isinstance(paper.paperId, float)
            )

        qualified_papers = []

        for paper in papers:
            if condition(paper):
                qualified_papers.append(paper)
            else:
                if paper is not None:
                    self.logger.info(
                        f"Warning: Discarding paper due to missing attributes (paperId: {paper.paperId})"
                    )
                else:
                    self.logger.info(
                        "Warning: Discarding paper due to missing attributes (paperId not available)"
                    )

        return qualified_papers
    
    def checkPapersOpenAlex(self, papers, processed):
        """
        Enhanced paper validation for OpenAlex data.
        
        OpenAlex has more missing abstracts and different data patterns than S2.
        This method handles those differences gracefully.
        
        Args:
            papers: List of paper objects
            processed: Whether to check for abstract requirement
            
        Returns:
            List of validated paper objects
        """
        if processed:
            condition = lambda paper: (
                hasattr(paper, 'title') and 
                hasattr(paper, 'paperId') and 
                paper.paperId is not None and 
                isinstance(paper.paperId, str) and 
                paper.paperId.strip() != "" and
                not isinstance(paper.paperId, float) and
                # Made abstract optional for OpenAlex since many papers lack abstracts
                (not hasattr(paper, 'abstract') or paper.abstract is None or 
                isinstance(paper.abstract, str))
            )
        else:
            condition = lambda paper: (
                hasattr(paper, 'title') and 
                hasattr(paper, 'paperId') and 
                paper.paperId is not None and 
                isinstance(paper.paperId, str) and 
                paper.paperId.strip() != "" and
                not isinstance(paper.paperId, float)
            )

        qualified_papers = []
        for paper in papers:
            if condition(paper):
                qualified_papers.append(paper)
            else:
                paper_id = getattr(paper, 'paperId', 'Unknown') if paper else 'None'
                self.logger.info(
                    f"Warning: Discarding OpenAlex paper due to missing attributes (paperId: {paper_id})"
                )

        return qualified_papers