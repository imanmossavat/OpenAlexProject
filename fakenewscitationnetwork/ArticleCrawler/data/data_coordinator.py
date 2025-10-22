import logging
import pandas as pd
from .retrieval_service import PaperRetrievalService
from .validation_service import DataValidationService
from .frame_manager import FrameManager
from ArticleCrawler.papervalidation.retraction_watch_manager import RetractionWatchManager

class DataCoordinator:
    """
    Orchestrates data retrieval, validation, and processing.
    
    This class replaces the original DataManager but with clear separation of concerns.
    It coordinates between different services while maintaining all existing functionality.
    """
    
    def __init__(self, 
                 retrieval_service: PaperRetrievalService,
                 validation_service: DataValidationService, 
                 frame_manager: FrameManager,
                 retraction_manager: RetractionWatchManager,
                 graph_manager,
                 graph_processing,
                 crawl_initial_condition=None,
                 logger=None):
        self.retrieval = retrieval_service
        self.validation = validation_service
        self.frames = frame_manager
        self.retraction_manager = retraction_manager
        self.graph = graph_manager
        self.graph_processing = graph_processing
        self.logger = logger or logging.getLogger(__name__)
        
        self.crawl_initial_condition = crawl_initial_condition
        self.no_papers_retrieved = True
        
        if crawl_initial_condition and crawl_initial_condition.seed_paperid:
            self.retrieve_and_process_papers(crawl_initial_condition.seed_paperid)
            self.frames.set_paper_id_seed_flag(crawl_initial_condition.seed_paperid)
            
        self.frames.df_paper_metadata['selected'] = (
            self.frames.df_paper_metadata['selected'].fillna(False).astype(bool)
        )

    def retrieve_and_process_papers(self, paper_ids, paperIDs_are_sampled=False):
        """
        Main orchestration method for retrieving and processing papers.
        
        This method maintains the exact same flow as the original DataManager method
        but delegates responsibilities to appropriate services.
        
        Args:
            paper_ids: List of paper IDs to retrieve
            paperIDs_are_sampled: Whether the paper IDs were selected by sampler
        """
        if not paper_ids:
            self.logger.info("No paper IDs provided for retrieval.")
            return

        papers = self.retrieval.retrieve_papers(paper_ids)
        
        failed_papers = self.retrieval.get_failed_papers()
        self.frames.update_failed_papers(failed_papers)

        if not papers:
            self.logger.info("No papers retrieved from API.")
            return

        self.no_papers_retrieved = False

        retrieved_ids = [paper.paperId for paper in papers if paper is not None]
        inconsistent_papers = self.retrieval.get_inconsistent_papers()
        
        self.validation.log_inconsistent_retrievals(
            requested_paper_ids=paper_ids,
            papers=papers,
            failed_paper_ids=failed_papers,
            inconsistent_paper_ids=inconsistent_papers
        )

        self.logger.info("Data processing started.")
        self.frames.process_data(papers)
        
        self.mark_retracted_papers()

        self.validation.validate_processed_status(retrieved_ids, self.frames.df_paper_metadata)
            
        self.validation.check_sampler_consistency(
            retrieved_ids, self.frames.df_paper_metadata, paperIDs_are_sampled
        )

        self.logger.info("Data processing completed.")

    
    def add_seed_papers(self, paper_ids):
        if not paper_ids:
            self.logger.info("No paper IDs provided to add as seeds.")
            return
        
        self.logger.info(f"Adding {len(paper_ids)} papers as additional seeds")
        self.retrieve_and_process_papers(paper_ids)
        self.frames.set_paper_id_seed_flag(paper_ids)

    def add_user_papers(self, paper_ids):
        """Allow users to update the crawler with a new set of paper IDs."""
        if not paper_ids:
            self.logger.info("No new paper IDs provided for update.")
            return
        
        self.logger.info(f"Updating papers with new IDs: {paper_ids}")
        self.retrieve_and_process_papers(paper_ids)
        self.logger.info(f"Successfully updated with {len(paper_ids)} new papers.")
        self.check_and_log_inconsistent_papers()

    def update_graph(self):
        """Update the graph with new nodes from current frames."""
        self.graph.update_graph_with_new_nodes(self.frames)

    def update_graph_and_calculate_centrality(self):
        """Update graph and calculate centralities."""
        self.graph.update_graph_with_new_nodes(self.frames)
        self.graph_processing.calculate_centrality()

    def extract_text(self):
        """Extract text data (abstracts and titles) for all papers."""
        all_paper_ids = self.frames.df_paper_metadata['paperId'].values
        abstracts, titles = self.get_text(all_paper_ids)
        return abstracts, titles
    
    def get_text(self, paper_ids):
        """
        Retrieve text data (abstract and title) for the given paper_ids.
        
        Args:
            paper_ids: List of paper IDs to get text for
            
        Returns:
            Tuple: (abstracts Series, titles Series)
        """
        abstracts = self.frames.df_abstract.loc[
            self.frames.df_abstract['paperId'].isin(paper_ids), 'abstract'
        ].copy()
        
        titles = self.frames.df_paper_metadata.loc[
            self.frames.df_paper_metadata['paperId'].isin(paper_ids), 'title'
        ].copy()
        
        return abstracts, titles
    
    def get_all_paper_centralities(self):
        """Get centralities for all papers."""
        return self.graph.get_all_paper_centralities(self)

    def mark_retracted_papers(self):
        """Gets retraction data from RetractionWatchManager and integrates it into frames."""
        self.logger.info("Checking for retractions")

        if self.frames.df_paper_metadata.empty:
            self.logger.info("No papers to check for retractions.")
            return

        doi_list = self.frames.df_paper_metadata["doi"].tolist()

        retracted_papers_df, forbidden_entries_df = (
            self.retraction_manager.process_retracted_papers(doi_list=doi_list)
        )

        if not retracted_papers_df.empty:
            self.frames.df_paper_metadata.loc[
                self.frames.df_paper_metadata["doi"].isin(retracted_papers_df["doi"]),
                "retracted"
            ] = True

        if not forbidden_entries_df.empty:
            self.frames.df_forbidden_entries = pd.concat(
                [self.frames.df_forbidden_entries, forbidden_entries_df], 
                ignore_index=True
            )

        self.logger.info("Retraction processing completed.")

    def check_and_log_inconsistent_papers(self):
        """
        Checks and logs inconsistent papers retrieved from the API.
        
        Returns:
            Dict: Summary of inconsistencies found
        """
        inconsistent_papers = self.retrieval.get_inconsistent_papers()
        if not inconsistent_papers:
            self.logger.info("No inconsistent papers detected.")
            return {"total_inconsistencies": 0, "details": []}

        self.logger.warning(
            f"Inconsistent papers detected: {len(inconsistent_papers)} mismatches found."
        )
        
        for requested_id, returned_id in inconsistent_papers:
            self.logger.warning(
                f"Inconsistent paper: Requested {requested_id}, but retrieved {returned_id}"
            )

        return {
            "total_inconsistencies": len(inconsistent_papers),
            "details": inconsistent_papers,
        }

    @property
    def frames(self):
        """Access to frame manager for backward compatibility."""
        return self._frames
    
    @frames.setter  
    def frames(self, value):
        """Set frame manager."""
        self._frames = value