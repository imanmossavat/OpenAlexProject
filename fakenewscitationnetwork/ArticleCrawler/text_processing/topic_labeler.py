
import logging
from typing import List, Optional, Dict

from .topic_labeling_strategy import TopicLabelingStrategy
from .refined_method_b_strategy import RefinedMethodBStrategy
from ..library.models import PaperData, TopicCluster


class TopicLabeler:
    """
    Labels topic clusters using a configurable strategy.
    
    By default uses Refined Method B (OpenAlex metadata).
    Can be extended with other strategies in the future.
    """
    
    def __init__(
        self,
        strategy: Optional[TopicLabelingStrategy] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize topic labeler.
        
        Args:
            strategy: Labeling strategy (defaults to Refined Method B)
            logger: Optional logger instance
        """
        self.strategy = strategy or RefinedMethodBStrategy(logger=logger)
        self.logger = logger or logging.getLogger(__name__)
    
    def label_clusters(
        self,
        clusters: Dict[int, List[PaperData]],
        top_words_per_cluster: Optional[Dict[int, List[str]]] = None
    ) -> List[TopicCluster]:
        """
        Label all clusters.
        
        Args:
            clusters: Dictionary mapping cluster_id to list of papers
            top_words_per_cluster: Optional top words from topic modeling
            
        Returns:
            List of labeled TopicCluster objects
        """
        labeled_clusters = []
        
        for cluster_id, papers in clusters.items():
            top_words = top_words_per_cluster.get(cluster_id, []) if top_words_per_cluster else []
            
            labeled_cluster = self.strategy.label_cluster(
                cluster_papers=papers,
                cluster_id=cluster_id,
                top_words=top_words
            )
            
            labeled_clusters.append(labeled_cluster)
            self.logger.info(f"Labeled cluster {cluster_id}: {labeled_cluster.label}")
        
        return labeled_clusters
    
    def set_strategy(self, strategy: TopicLabelingStrategy) -> None:
        """
        Change the labeling strategy.
        
        Args:
            strategy: New labeling strategy
        """
        self.strategy = strategy