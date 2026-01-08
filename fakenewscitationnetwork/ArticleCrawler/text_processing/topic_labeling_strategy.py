
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..library.models import PaperData, TopicCluster


class TopicLabelingStrategy(ABC):
    """
    Abstract base class for topic labeling strategies.
    
    This interface allows for different approaches to labeling topics:
    - Refined Method B (OpenAlex metadata)
    - Method A (API queries - future)
    - Keyword-based labeling (future)
    - LLM-based labeling (future)
    """
    
    @abstractmethod
    def label_cluster(
        self, 
        cluster_papers: List[PaperData],
        cluster_id: int,
        top_words: List[str] = None
    ) -> TopicCluster:
        """
        Label a topic cluster.
        
        Args:
            cluster_papers: Papers in the cluster
            cluster_id: Cluster identifier
            top_words: Optional top words from topic model
            
        Returns:
            TopicCluster with label and metadata
        """
        pass