import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import List, Optional

from ...usecases.library_creation import LibraryCreationOrchestrator
from ..ui.prompts import RichPrompter
from ..ui.seed_providers import (
    ManualSeedProvider,
    FileSeedProvider,
    PDFSeedProvider,
    ZoteroSeedProvider
)

console = Console()


def library_create_command(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Library name"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Library path"),
    api_provider: str = typer.Option("openalex", "--api-provider", help="API provider (default: openalex)")
) -> Optional[Path]:
    """Create a new paper library from various sources."""
    
    # Header matching wizard style
    console.print(Panel.fit(
        "[bold cyan]LIBRARY CREATION[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\nCreate a new library to organize and analyze research papers.")
    console.print("You can press [bold red]Ctrl+C[/bold red] at any time to cancel.\n")
    
    prompter = RichPrompter(console)
    
    # STEP 1: Library Name
    _print_step_header(console, "STEP 1: Library Name")
    if not name:
        name = prompter.input("Library name")
        if not name:
            console.print("\n[yellow]Cancelled[/yellow]")
            return None
    console.print(f"[green]✓[/green] Library name: {name}\n")
    
    # STEP 2: Library Path
    _print_step_header(console, "STEP 2: Library Location")
    if not path:
        default_path = Path.cwd() / "libraries" / name
        path = prompter.input("Library path", default=str(default_path))
        if not path:
            console.print("\n[yellow]Cancelled[/yellow]")
            return None
    
    library_path = Path(path)
    
    if (library_path / "library_config.yaml").exists():
        console.print(f"[yellow]⚠️  Library already exists at {library_path}[/yellow]")
        if not prompter.confirm("Overwrite existing library?"):
            console.print("\n[yellow]Cancelled[/yellow]")
            return None
    
    console.print(f"[green]✓[/green] Location: {library_path}\n")
    
    # STEP 3: Description
    _print_step_header(console, "STEP 3: Library Description")
    description = prompter.input("Description (optional)", default="")
    description = description if description else None
    if description:
        console.print(f"[green]✓[/green] Description added\n")
    else:
        console.print(f"[dim]Skipping description[/dim]\n")
    
    # STEP 4: Paper Sources
    _print_step_header(console, "STEP 4: Paper Sources")
    console.print("[dim]Select sources to add papers to your library[/dim]\n")
    paper_ids = _get_papers_from_sources(prompter, api_provider, console)
    
    if not paper_ids:
        console.print("\n[red]No papers selected. Cancelled.[/red]")
        return None
    
    console.print(f"\n[green]✓[/green] Selected {len(paper_ids)} papers\n")
    
    # Final confirmation
    console.print("\n" + "=" * 70)
    console.print("[bold]Review Configuration[/bold]")
    console.print("=" * 70)
    console.print(f"[cyan]Name:[/cyan] {name}")
    console.print(f"[cyan]Path:[/cyan] {library_path}")
    console.print(f"[cyan]Papers:[/cyan] {len(paper_ids)}")
    console.print(f"[cyan]API Provider:[/cyan] {api_provider}")
    console.print("=" * 70 + "\n")
    
    if not prompter.confirm("Create library with these settings?"):
        console.print("\n[yellow]Cancelled[/yellow]")
        return None
    
    try:
        orchestrator = LibraryCreationOrchestrator(api_provider=api_provider)
        
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]CREATING LIBRARY[/bold cyan]")
        console.print("=" * 70 + "\n")
        
        with console.status("[bold cyan]Fetching papers and creating library..."):
            config = orchestrator.create_library(
                library_name=name,
                library_path=library_path,
                paper_ids=paper_ids,
                description=description
            )
        
        console.print("\n" + "=" * 70)
        console.print("[bold green]✅ LIBRARY CREATED SUCCESSFULLY[/bold green]")
        console.print("=" * 70)
        console.print(f"[cyan]Location:[/cyan] {config.base_path}")
        console.print(f"[cyan]Papers:[/cyan] {len(paper_ids)}")
        console.print("=" * 70 + "\n")
        
        return config.base_path
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]")
        raise


def _print_step_header(console: Console, step_text: str):
    """Print step header matching wizard style."""
    console.print("─" * 70)
    console.print(f"[bold cyan]{step_text}[/bold cyan]")
    console.print("─" * 70 + "\n")


def _get_papers_from_sources(prompter: RichPrompter, api_provider: str, console: Console) -> List[str]:
    """
    Get paper IDs from various sources.
    
    Args:
        prompter: RichPrompter instance
        api_provider: API provider to use
        console: Console instance for printing
        
    Returns:
        List of paper IDs
    """
    all_paper_ids = []
    
    sources_list = [
        'Manual Entry',
        'From File',
        'From PDFs',
        'From Zotero',
        'Done selecting sources'
    ]
    
    sources_map = {
        'Manual Entry': ManualSeedProvider,
        'From File': FileSeedProvider,
        'From PDFs': PDFSeedProvider,
        'From Zotero': ZoteroSeedProvider,
    }
    
    while True:
        choice_idx = prompter.choice(
            "Select paper source",
            choices=sources_list,
            default=0
        )
        
        choice = sources_list[choice_idx]
        
        if choice == 'Done selecting sources':
            break
        
        provider_class = sources_map[choice]
        provider = provider_class(prompter, api_provider)
        
        try:
            paper_ids = provider.get_seeds()
            if paper_ids:
                all_paper_ids.extend(paper_ids)
                console.print(f"[green]✓ Added {len(paper_ids)} papers[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        
        if not prompter.confirm("\nAdd papers from another source?"):
            break
    
    unique_paper_ids = list(set(all_paper_ids))
    
    if len(unique_paper_ids) < len(all_paper_ids):
        console.print(
            f"[yellow]Removed {len(all_paper_ids) - len(unique_paper_ids)} duplicates[/yellow]"
        )
    
    return unique_paper_ids