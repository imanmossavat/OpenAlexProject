
from pathlib import Path
from typing import List
from datetime import datetime

from .models import TopicCluster


class TopicOverviewWriter:
    """
    Creates markdown overview files for topic modeling results.
    
    Responsibilities:
    - Generate markdown overview of all topics
    - Format topic statistics
    - Create summary tables
    
    Does NOT:
    - Run topic modeling (that's TopicModelingOrchestrator)
    - Organize individual papers (that's TopicModelingOrchestrator)
    - Display results to console (that's CLI commands)
    """
    
    def __init__(self):
        """Initialize the writer."""
        pass
    
    def create_overview(
        self,
        clusters: List[TopicCluster],
        library_path: Path,
        model_type: str,
        num_topics: int
    ) -> Path:
        """
        Create a topic overview markdown file.
        
        Args:
            clusters: List of labeled topic clusters
            library_path: Path to library
            model_type: Type of model used (NMF/LDA)
            num_topics: Number of topics
            
        Returns:
            Path to created overview file
        """
        topics_dir = library_path / "topics"
        topics_dir.mkdir(parents=True, exist_ok=True)
        
        overview_path = topics_dir / "00_TOPIC_OVERVIEW.md"
        
        content = self._generate_content(clusters, model_type, num_topics)
        
        with open(overview_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return overview_path
    
    def _generate_content(
        self,
        clusters: List[TopicCluster],
        model_type: str,
        num_topics: int
    ) -> str:
        """
        Generate the markdown content for the overview.
        
        Args:
            clusters: List of topic clusters
            model_type: Model type used
            num_topics: Number of topics
            
        Returns:
            Markdown content as string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_papers = sum(len(c.paper_ids) for c in clusters)
        
        # Header
        content = f"""# Topic Modeling Overview

**Generated:** {timestamp}  
**Algorithm:** {model_type}  
**Number of Topics:** {num_topics}  
**Total Papers:** {total_papers}

---

## Topics Summary

"""
        
        # Add table
        content += self._create_markdown_table(clusters)
        
        # Add detailed sections for each topic
        content += "\n\n---\n\n## Detailed Topic Information\n\n"
        
        for cluster in sorted(clusters, key=lambda x: x.cluster_id):
            content += self._create_topic_section(cluster)
        
        return content
    
    def _create_markdown_table(self, clusters: List[TopicCluster]) -> str:
        """
        Create a markdown table of topics.
        
        Args:
            clusters: List of topic clusters
            
        Returns:
            Markdown table as string
        """
        table = "| Topic ID | Label | Papers | Top Words |\n"
        table += "|----------|-------|--------|----------|\n"
        
        for cluster in sorted(clusters, key=lambda x: x.cluster_id):
            top_words = ", ".join(cluster.top_words[:5]) if cluster.top_words else "N/A"
            
            # Create link to topic folder
            safe_label = self._sanitize_folder_name(cluster.label)
            topic_link = f"[{cluster.label}](./{safe_label}/)"
            
            table += f"| {cluster.cluster_id} | {topic_link} | {len(cluster.paper_ids)} | {top_words} |\n"
        
        return table
    
    def _create_topic_section(self, cluster: TopicCluster) -> str:
        """
        Create detailed section for a single topic.
        
        Args:
            cluster: Topic cluster
            
        Returns:
            Markdown section as string
        """
        safe_label = self._sanitize_folder_name(cluster.label)
        
        section = f"### Topic {cluster.cluster_id}: {cluster.label}\n\n"
        section += f"**Folder:** `{safe_label}/`  \n"
        section += f"**Papers:** {len(cluster.paper_ids)}  \n\n"
        
        # Top words
        if cluster.top_words:
            section += "**Key Terms:**  \n"
            section += ", ".join(f"`{word}`" for word in cluster.top_words[:10])
            section += "\n\n"
        
        # Representative concepts
        if cluster.representative_concepts:
            section += "**Representative Concepts:**  \n"
            for concept in cluster.representative_concepts[:5]:
                section += f"- {concept}\n"
            section += "\n"
        
        section += "---\n\n"
        
        return section
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize folder name to be filesystem-safe.
        
        Args:
            name: Original name
            
        Returns:
            Sanitized name
        """
        # Remove or replace problematic characters
        replacements = {
            '/': '_',
            '\\': '_',
            ':': '_',
            '*': '_',
            '?': '_',
            '"': '_',
            '<': '_',
            '>': '_',
            '|': '_',
            '&': 'and',
            ' ': '_'
        }
        
        sanitized = name
        for old, new in replacements.items():
            sanitized = sanitized.replace(old, new)
        
        # Remove any remaining non-alphanumeric except underscore and hyphen
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '_-')
        
        # Limit length
        return sanitized[:100]