"""
Run command for executing crawler from config file.
"""

from rich.console import Console
from ..models.experiment_config import ExperimentConfig


class RunCommand:
    """
    Execute crawler from configuration file.
    """
    
    def __init__(self, console: Console):
        self.console = console
    
    def execute(self, config: ExperimentConfig):
        """
        Run the crawler with given configuration.
        
        Args:
            config: ExperimentConfig object loaded from file
        """
        from ArticleCrawler.cli.main import _run_crawler
        
        self.console.print(f"\n[bold cyan]Running experiment:[/bold cyan] {config.name}")
        self.console.print(f"[cyan]Configuration loaded successfully[/cyan]\n")
        
        _run_crawler(config)