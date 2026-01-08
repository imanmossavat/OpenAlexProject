"""
Paper source collector with availability-aware provider selection.
"""

from typing import List
from rich.console import Console
from .prompts import Prompter
from .seed_providers import ManualSeedProvider, FileSeedProvider, PDFSeedProvider, ZoteroSeedProvider


class PaperSourceCollector:
    """
    Collects paper IDs from multiple sources with availability checking.
    
    This collector checks service availability (Zotero, GROBID) and only
    presents available options to the user.
    """
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def collect_from_multiple_sources(self, api_provider: str) -> List[str]:
        """
        Collect paper IDs from multiple sources.
        
        Args:
            api_provider: API provider type ('openalex' or 'semantic_scholar')
        
        Returns:
            List of paper IDs
        """
        all_paper_ids = []
        
        providers = [
            ManualSeedProvider(self.prompter),
            FileSeedProvider(self.prompter),
            PDFSeedProvider(self.prompter, api_provider),
            ZoteroSeedProvider(self.prompter, api_provider),
        ]
        
        while True:
            choices = []
            available_providers = []
            
            for provider in providers:
                is_available, reason = provider.is_available()
                
                if is_available:
                    choices.append(provider.display_name())
                    available_providers.append(provider)
                else:
                    unavailable_text = f"{provider.display_name()} [dim]({reason})[/dim]"
                    choices.append(unavailable_text)
                    available_providers.append(None)
            
            choices.append("Done selecting sources")
            
            if all_paper_ids:
                self.console.print(f"\n[cyan]Currently selected:[/cyan] {len(all_paper_ids)} papers")
            
            self.console.print("\n[bold]Select paper source:[/bold]")
            choice_idx = self.prompter.choice(
                "Choose a source",
                choices=choices,
                default=0
            )
            
            if choice_idx == len(choices) - 1:
                break
            
            provider = available_providers[choice_idx]
            if provider is None:
                original_provider = providers[choice_idx]
                message = original_provider.get_unavailable_message()
                self.console.print(f"\n[yellow]⚠️  {message}[/yellow]\n")
                continue
            
            try:
                paper_ids = provider.get_seeds()
                if paper_ids:
                    all_paper_ids.extend(paper_ids)
                    self.console.print(f"[green]✓ Added {len(paper_ids)} papers[/green]\n")
                else:
                    self.console.print("[yellow]No papers added from this source[/yellow]\n")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Cancelled[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]✗ Error: {e}[/red]\n")
            
            if not self.prompter.confirm("\nAdd papers from another source?", default=True):
                break
        
        unique_paper_ids = list(set(all_paper_ids))
        
        if len(unique_paper_ids) < len(all_paper_ids):
            removed_count = len(all_paper_ids) - len(unique_paper_ids)
            self.console.print(
                f"[yellow]ℹ Removed {removed_count} duplicate(s)[/yellow]"
            )
        
        return unique_paper_ids
