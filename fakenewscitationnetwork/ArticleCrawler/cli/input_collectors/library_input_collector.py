from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
import questionary

from ..models.library_inputs import LibraryCreationInputs
from ..ui.prompts import RichPrompter


class LibraryInputCollector:
    """Collects inputs for library creation."""
    
    def __init__(self, console: Console):
        self.console = console
        self.prompter = RichPrompter(console)
    
    def collect(
        self,
        name: Optional[str] = None,
        path: Optional[str] = None,
        api_provider: str = 'openalex'
    ) -> Optional[LibraryCreationInputs]:
        """
        Collect all required inputs for library creation.
        
        Args:
            name: Library name (prompts if None)
            path: Library path (prompts if None)
            api_provider: API provider to use
            
        Returns:
            LibraryCreationInputs or None if cancelled
        """
        if not name:
            name = Prompt.ask("Enter library name")
            if not name:
                return None
        
        if not path:
            default_path = Path.cwd() / "libraries" / name
            path = Prompt.ask(
                "Enter library path",
                default=str(default_path)
            )
            if not path:
                return None
        
        library_path = Path(path)
        
        if (library_path / "library_config.yaml").exists():
            self.console.print(f"[yellow]⚠️  Library already exists at {library_path}[/yellow]")
            if not Confirm.ask("Overwrite existing library?"):
                self.console.print("[red]Cancelled[/red]")
                return None
        
        description = Prompt.ask(
            "Enter library description (optional)",
            default=""
        )
        description = description if description else None
        
        self.console.print("\n[bold]Select paper sources:[/bold]")
        paper_ids = self._collect_paper_ids(api_provider)
        
        if not paper_ids:
            self.console.print("[red]No papers selected. Cancelled.[/red]")
            return None
        
        self.console.print(f"\n[green]Selected {len(paper_ids)} papers[/green]\n")
        
        if not Confirm.ask("Create library?"):
            self.console.print("[red]Cancelled[/red]")
            return None
        
        return LibraryCreationInputs(
            name=name,
            path=library_path,
            description=description,
            paper_ids=paper_ids,
            api_provider=api_provider
        )
    
    def _collect_paper_ids(self, api_provider: str) -> List[str]:
        """Collect paper IDs from various sources."""
        from ..ui.seed_providers import (
            ManualSeedProvider,
            FileSeedProvider,
            PDFSeedProvider,
            ZoteroSeedProvider
        )
        
        all_paper_ids = []
        
        sources = {
            'Manual Entry': ManualSeedProvider,
            'From File': FileSeedProvider,
            'From PDFs': PDFSeedProvider,
            'From Zotero': ZoteroSeedProvider,
            'Done selecting sources': None
        }
        
        while True:
            choice = questionary.select(
                "Select paper source:",
                choices=list(sources.keys())
            ).ask()
            
            if not choice or choice == 'Done selecting sources':
                break
            
            provider_class = sources[choice]
            provider = provider_class(self.prompter, api_provider)
            
            try:
                paper_ids = provider.get_seeds()
                if paper_ids:
                    all_paper_ids.extend(paper_ids)
                    self.console.print(f"[green]Added {len(paper_ids)} papers[/green]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
            
            if not Confirm.ask("\nAdd papers from another source?"):
                break
        
        unique_paper_ids = list(set(all_paper_ids))
        
        if len(unique_paper_ids) < len(all_paper_ids):
            self.console.print(
                f"[yellow]Removed {len(all_paper_ids) - len(unique_paper_ids)} duplicates[/yellow]"
            )
        
        return unique_paper_ids