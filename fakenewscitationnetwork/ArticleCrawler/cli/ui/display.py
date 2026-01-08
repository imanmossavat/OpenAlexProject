"""
Display utilities for formatted output.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Any


def display_config_summary(config: Dict[str, Any], console: Console = None):
    """
    Display configuration summary in a nice table.
    
    Args:
        config: Configuration dictionary
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    table = Table(title="Experiment Configuration", show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for key, value in config.items():
        # Format value for display
        if isinstance(value, list):
            value_str = f"{len(value)} items"
        elif isinstance(value, bool):
            value_str = "✓" if value else "✗"
        else:
            value_str = str(value)
        
        table.add_row(key, value_str)
    
    console.print(table)


def display_progress_summary(iteration: int, total: int, papers_retrieved: int, console: Console = None):
    """
    Display crawling progress summary.
    
    Args:
        iteration: Current iteration number
        total: Total iterations
        papers_retrieved: Number of papers retrieved so far
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    progress_text = f"Iteration {iteration}/{total} - Papers retrieved: {papers_retrieved}"
    
    console.print(Panel(
        progress_text,
        title="[bold cyan]Progress[/bold cyan]",
        border_style="cyan"
    ))