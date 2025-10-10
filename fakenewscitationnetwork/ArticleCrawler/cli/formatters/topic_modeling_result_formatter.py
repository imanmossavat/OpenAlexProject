import json
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table

from ...library.models import TopicCluster


class TopicModelingResultFormatter:
    """Formats topic modeling results."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display(self, clusters: List[TopicCluster], library_path: Path) -> None:
        """
        Display topic modeling results as a Rich table.
        
        Args:
            clusters: List of topic clusters
            library_path: Path to library
        """
        self.console.print("\n[bold green]✓ Topic modeling complete![/bold green]\n")
        
        table = self._create_table(clusters)
        self.console.print(table)
        
        self._display_summary(clusters, library_path)
    
    def _create_table(self, clusters: List[TopicCluster]) -> Table:
        """Create Rich table from clusters."""
        table = Table(title="Topic Clusters", show_header=True, header_style="bold cyan")
        table.add_column("Topic ID", style="cyan", justify="right")
        table.add_column("Label", style="green")
        table.add_column("Papers", justify="right")
        table.add_column("Top Words", style="dim")
        
        for cluster in sorted(clusters, key=lambda x: x.cluster_id):
            top_words = ", ".join(cluster.top_words[:5]) if cluster.top_words else "N/A"
            
            table.add_row(
                str(cluster.cluster_id),
                cluster.label,
                str(len(cluster.paper_ids)),
                top_words
            )
        
        return table
    
    def _display_summary(self, clusters: List[TopicCluster], library_path: Path) -> None:
        """Display summary information."""
        topics_dir = library_path / "topics"
        self.console.print(f"\n[green]Papers organized in: {topics_dir}[/green]")
        self.console.print(f"[dim]Each topic has its own folder with the papers[/dim]\n")
    
    def to_json(self, clusters: List[TopicCluster]) -> str:
        """
        Format results as JSON (useful for API or programmatic access).
        
        Args:
            clusters: List of topic clusters
            
        Returns:
            JSON string
        """
        return json.dumps([
            {
                'cluster_id': c.cluster_id,
                'label': c.label,
                'paper_count': len(c.paper_ids),
                'papers': c.paper_ids,
                'top_words': c.top_words,
                'representative_concepts': c.representative_concepts
            }
            for c in clusters
        ], indent=2)
    
    def display_error(self, error: Exception) -> None:
        """Display error message."""
        self.console.print(f"\n[bold red]Error: {error}[/bold red]")