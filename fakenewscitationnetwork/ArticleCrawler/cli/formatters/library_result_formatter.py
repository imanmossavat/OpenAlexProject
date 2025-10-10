from pathlib import Path
from rich.console import Console
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...library.models import LibraryConfig


class LibraryResultFormatter:
    """Formats library creation results."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display_success(self, config: 'LibraryConfig', num_papers: int) -> None:
        """
        Display successful library creation.
        
        Args:
            config: Library configuration
            num_papers: Number of papers in library
        """
        self.console.print(f"\n[bold green]✓ Library created successfully![/bold green]")
        self.console.print(f"[green]Location: {config.base_path}[/green]")
        self.console.print(f"[green]Name: {config.name}[/green]")
        self.console.print(f"[green]Papers: {num_papers}[/green]")
        if config.description:
            self.console.print(f"[green]Description: {config.description}[/green]")
        self.console.print()
    
    def display_error(self, error: Exception) -> None:
        """Display error message."""
        self.console.print(f"\n[bold red]Error creating library: {error}[/bold red]")