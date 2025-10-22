"""Shared utility for collecting papers from multiple sources."""

from typing import List
from rich.console import Console
from .prompts import Prompter
from .seed_providers import SEED_PROVIDERS, PDFSeedProvider


class PaperSourceCollector:
    """Reusable component for collecting papers from multiple sources."""
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def collect_from_multiple_sources(self, api_provider: str) -> List[str]:
        """
        Collect paper IDs from various sources with continuous selection.
        
        Args:
            api_provider: API provider to use for PDF extraction
            
        Returns:
            List of unique paper IDs
        """
        all_paper_ids = []
        
        # Build provider list
        providers = [
            Provider(self.prompter) if Provider != PDFSeedProvider 
            else Provider(self.prompter, api_provider) 
            for Provider in SEED_PROVIDERS
        ]
        
        choices = [p.display_name() for p in providers]
        choices.append('Done selecting sources')
        
        self.console.print("Select sources to add papers from:\n")
        
        while True:
            choice_idx = self.prompter.choice("Select paper source", choices=choices)
            
            if choice_idx == len(choices) - 1:
                break
            
            selected_provider = providers[choice_idx]
            
            try:
                paper_ids = selected_provider.get_seeds()
                
                if paper_ids:
                    all_paper_ids.extend(paper_ids)
                    self.console.print(f"[green]✓ Added {len(paper_ids)} papers[/green]")
                else:
                    self.console.print("[yellow]No papers added from this source[/yellow]")
                    
            except NotImplementedError:
                self.prompter.error("This feature is not yet implemented.")
            except Exception as e:
                self.prompter.error(f"Error loading seeds: {e}")
            
            if not self.prompter.confirm("\nAdd papers from another source?", default=True):
                break
        
        unique_paper_ids = list(set(all_paper_ids))
        
        if len(unique_paper_ids) < len(all_paper_ids):
            self.console.print(
                f"[yellow]Removed {len(all_paper_ids) - len(unique_paper_ids)} duplicates[/yellow]"
            )
        
        return unique_paper_ids