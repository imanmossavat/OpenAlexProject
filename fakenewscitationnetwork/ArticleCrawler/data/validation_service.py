import logging
from typing import List

class DataValidationService:
    """
    Handles data validation and consistency checking.
    
    This service is responsible for:
    - Validating retrieved paper data
    - Checking for inconsistencies between requested and returned papers
    - Logging validation issues and inconsistencies
    - Providing validation statistics
    """
    
    def __init__(self, logger=None):
        """
        Initialize the data validation service.
        
        Args:
            logger: Logger instance for logging validation events
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def log_inconsistent_retrievals(self, requested_paper_ids: List[str], papers: List, 
                                  failed_paper_ids: List[str], inconsistent_paper_ids: List[tuple]):
        """
        Double check for inconsistencies not captured by the API class.
        
        This method identifies instances where papers should have been retrieved but weren't,
        beyond what the API provider already tracks.
        
        Args:
            requested_paper_ids: List of paper IDs that were requested
            papers: List of paper objects that were retrieved
            failed_paper_ids: List of paper IDs that the API reported as failed
            inconsistent_paper_ids: List of (requested, returned) ID tuples from API
        """
        retrieved_ids = [paper.paperId for paper in papers if paper is not None]
        
        delta_failed_papers = list(set(requested_paper_ids) 
                                  - set(retrieved_ids) 
                                  - set([pair[0] for pair in inconsistent_paper_ids])
                                  - set(failed_paper_ids))
        
        if delta_failed_papers:
            self.logger.warning(
                f"Found {len(delta_failed_papers)} failed papers not captured by API class. "
                "This should ideally be zero - investigate if this number is high."
            )
            for paper_id in delta_failed_papers:
                self.logger.warning(f"Untracked failed paper ID: {paper_id}")
        else:
            self.logger.info("All failed papers properly tracked by API provider.")
    
    def validate_paper_objects(self, papers: List) -> tuple:
        """
        Validate that paper objects have required attributes.
        
        Args:
            papers: List of paper objects to validate
            
        Returns:
            Tuple: (valid_papers, invalid_count)
        """
        valid_papers = []
        invalid_count = 0
        
        for paper in papers:
            if paper is None:
                invalid_count += 1
                continue
                
            if (hasattr(paper, 'paperId') and 
                hasattr(paper, 'title') and 
                paper.paperId is not None and
                paper.title is not None):
                valid_papers.append(paper)
            else:
                invalid_count += 1
                paper_id = getattr(paper, 'paperId', 'Unknown')
                self.logger.warning(f"Invalid paper object: {paper_id}")
        
        if invalid_count > 0:
            self.logger.warning(f"Found {invalid_count} invalid paper objects")
        
        return valid_papers, invalid_count
    
    def check_sampler_consistency(self, retrieved_ids: List[str], 
                                 df_paper_metadata, paperIDs_are_sampled: bool):
        """
        Check consistency between sampler selections and retrieved papers.
        
        Args:
            retrieved_ids: List of paper IDs that were retrieved
            df_paper_metadata: DataFrame containing paper metadata
            paperIDs_are_sampled: Whether the paper IDs were selected by sampler
        """
        if not paperIDs_are_sampled:
            return
            
        selected_flags = df_paper_metadata.loc[
            df_paper_metadata['paperId'].isin(retrieved_ids), 'selected'
        ].values

        incorrect_flags = [
            paper_id for paper_id, flag in zip(retrieved_ids, selected_flags) 
            if not flag
        ]
        
        if incorrect_flags:
            self.logger.warning(
                f"Sampler inconsistency: {len(incorrect_flags)} papers retrieved "
                "were not marked as selected by the sampler."
            )
            for paper_id in incorrect_flags:
                self.logger.warning(f"Sampler inconsistency for paper ID: {paper_id}")
        else:
            self.logger.info("All retrieved papers correctly marked as selected.")
    
    def validate_processed_status(self, retrieved_ids: List[str], df_paper_metadata):
        """
        Validate that retrieved papers are marked as processed.
        
        Args:
            retrieved_ids: List of paper IDs that were retrieved
            df_paper_metadata: DataFrame containing paper metadata
        """
        should_be_processed = df_paper_metadata.loc[
            df_paper_metadata['paperId'].isin(retrieved_ids), 'processed'
        ]
        
        if any(should_be_processed != True):
            unprocessed_count = sum(should_be_processed != True)
            self.logger.warning(
                f"{unprocessed_count} papers not marked as processed correctly"
            )
            return False
        
        return True