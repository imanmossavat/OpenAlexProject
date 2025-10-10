
from typing import List, Dict, Optional
from collections import Counter
import logging

from .topic_labeling_strategy import TopicLabelingStrategy
from ..library.models import PaperData, TopicCluster


class RefinedMethodBStrategy(TopicLabelingStrategy):
    """
    Labels topics using OpenAlex concept metadata from papers in cluster.
    
    Strategy:
    1. Extract concepts from all papers in cluster
    2. Filter by concept level (≥2 for specificity)
    3. Find most common concepts
    4. Handle duplicates by combining with parent concepts
    5. Generate human-readable label
    """
    
    MIN_CONCEPT_LEVEL = 2
    
    def __init__(
        self, 
        min_concept_level: int = 2,
        top_n_concepts: int = 2,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Refined Method B strategy.
        
        Args:
            min_concept_level: Minimum concept level to consider
            top_n_concepts: Number of top concepts to use in label
            logger: Optional logger instance
        """
        self.min_concept_level = min_concept_level
        self.top_n_concepts = top_n_concepts
        self.logger = logger or logging.getLogger(__name__)
    
    def label_cluster(
        self,
        cluster_papers: List[PaperData],
        cluster_id: int,
        top_words: List[str] = None
    ) -> TopicCluster:
        """
        Label cluster using paper concepts.
        
        Args:
            cluster_papers: Papers in the cluster
            cluster_id: Cluster identifier
            top_words: Optional top words from topic model (kept for compatibility)
            
        Returns:
            TopicCluster with label
        """
        if not cluster_papers:
            return TopicCluster(
                cluster_id=cluster_id,
                label=f"Cluster_{cluster_id}",
                paper_ids=[],
                top_words=top_words or []
            )
        
        all_concepts = self._extract_concepts_from_papers(cluster_papers)
        
        if not all_concepts:
            return self._fallback_labeling(cluster_papers, cluster_id, top_words)
        
        representative_concepts = self._find_representative_concepts(all_concepts)
        
        label = self._generate_label(representative_concepts)
        
        return TopicCluster(
            cluster_id=cluster_id,
            label=label,
            paper_ids=[p.paper_id for p in cluster_papers],
            representative_concepts=representative_concepts,
            top_words=top_words or []
        )
    
    def _extract_concepts_from_papers(self, papers: List[PaperData]) -> List[Dict]:
        """
        Extract concepts from papers, filtering by level.
        
        Args:
            papers: List of papers
            
        Returns:
            List of concept dictionaries
        """
        all_concepts = []
        
        for paper in papers:
            for concept in paper.concepts:
                level = concept.get('level', 0)
                if level >= self.min_concept_level:
                    all_concepts.append(concept)
        
        return all_concepts
    
    def _find_representative_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """
        Find most representative concepts by frequency.
        
        Args:
            concepts: List of concept dictionaries
            
        Returns:
            List of top N representative concepts with frequency
        """
        concept_counter = Counter()
        concept_details = {}
        
        for concept in concepts:
            concept_id = concept.get('id', '')
            display_name = concept.get('display_name', '')
            
            if display_name:
                concept_counter[display_name] += 1
                if display_name not in concept_details:
                    concept_details[display_name] = concept
        
        top_concepts = []
        for name, count in concept_counter.most_common(self.top_n_concepts):
            concept = concept_details[name].copy()
            concept['frequency'] = count
            top_concepts.append(concept)
        
        return top_concepts
    
    def _generate_label(self, concepts: List[Dict]) -> str:
        """
        Generate human-readable label from concepts.
        
        Handles duplicates by combining with parent concepts.
        
        Args:
            concepts: List of representative concepts
            
        Returns:
            Human-readable label
        """
        if not concepts:
            return "Unlabeled"
        
        names = []
        seen_names = set()
        
        for concept in concepts:
            name = concept.get('display_name', '')
            
            if name in seen_names:
                ancestors = concept.get('ancestors', [])
                if ancestors:
                    parent_name = ancestors[0].get('display_name', '')
                    if parent_name:
                        name = f"{parent_name} — {name}"
            
            names.append(name)
            seen_names.add(concept.get('display_name', ''))
        
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} & {names[1]}"
        else:
            return " & ".join(names[:2])
    
    def _fallback_labeling(
        self,
        cluster_papers: List[PaperData],
        cluster_id: int,
        top_words: Optional[List[str]]
    ) -> TopicCluster:
        """
        Fallback labeling when concepts unavailable.
        
        Try topics → fields → top words → generic label
        
        Args:
            cluster_papers: Papers in cluster
            cluster_id: Cluster ID
            top_words: Top words from topic model
            
        Returns:
            TopicCluster with fallback label
        """
        all_topics = []
        for paper in cluster_papers:
            all_topics.extend(paper.topics)
        
        if all_topics:
            topic_counter = Counter(
                t.get('display_name', '') 
                for t in all_topics 
                if t.get('display_name')
            )
            if topic_counter:
                top_topic = topic_counter.most_common(1)[0][0]
                return TopicCluster(
                    cluster_id=cluster_id,
                    label=top_topic,
                    paper_ids=[p.paper_id for p in cluster_papers],
                    top_words=top_words or []
                )
        
        all_fields = []
        for paper in cluster_papers:
            all_fields.extend(paper.fields)
        
        if all_fields:
            field_counter = Counter(
                f.get('display_name', '') 
                for f in all_fields 
                if f.get('display_name')
            )
            if field_counter:
                top_field = field_counter.most_common(1)[0][0]
                return TopicCluster(
                    cluster_id=cluster_id,
                    label=top_field,
                    paper_ids=[p.paper_id for p in cluster_papers],
                    top_words=top_words or []
                )
        
        if top_words and len(top_words) >= 2:
            label = f"{top_words[0].title()} & {top_words[1].title()}"
            return TopicCluster(
                cluster_id=cluster_id,
                label=label,
                paper_ids=[p.paper_id for p in cluster_papers],
                top_words=top_words
            )
        
        return TopicCluster(
            cluster_id=cluster_id,
            label=f"Cluster_{cluster_id}",
            paper_ids=[p.paper_id for p in cluster_papers],
            top_words=top_words or []
        )