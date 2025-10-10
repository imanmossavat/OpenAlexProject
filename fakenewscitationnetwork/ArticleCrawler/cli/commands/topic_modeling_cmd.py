import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional

from ...usecases.topic_modeling_usecase import TopicModelingOrchestrator
from ...config.text_config import TextProcessingConfig
from ..ui.prompts import RichPrompter
from .library_create import library_create_command

console = Console()


def topic_modeling_command(
    library_path: Optional[str] = typer.Option(None, "--library-path", "-l", help="Path to library"),
    model_type: Optional[str] = typer.Option(None, "--model-type", "-m", help="Topic model type (NMF or LDA)"),
    num_topics: Optional[int] = typer.Option(None, "--num-topics", "-n", help="Number of topics")
):
    """Run topic modeling on an existing library."""
    
    # Header matching wizard style
    console.print(Panel.fit(
        "[bold cyan]TOPIC MODELING[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\nAnalyze and cluster papers by topic using machine learning.")
    console.print("You can press [bold red]Ctrl+C[/bold red] at any time to cancel.\n")
    
    prompter = RichPrompter(console)
    
    # STEP 1: Library Selection
    _print_step_header(console, "STEP 1: Library Selection")
    
    if not library_path:
        library_choices = ["Use an existing library", "Create a new library"]
        library_choice_idx = prompter.choice(
            "What would you like to do?",
            choices=library_choices,
            default=0
        )
        
        if library_choice_idx == 1:  # Create new library
            console.print("\n[cyan]Let's create a new library first...[/cyan]\n")
            
            created_library_path = library_create_command(name=None, path=None, api_provider='openalex')
            
            if not created_library_path:
                console.print("\n[yellow]Library creation cancelled[/yellow]")
                return
            
            if not prompter.confirm("\nContinue with topic modeling on this library?"):
                console.print("\n[yellow]Cancelled[/yellow]")
                return
            
            library_path = str(created_library_path)
        else:  # Use existing
            library_path = prompter.input("Library path")
    
    library_path_obj = Path(library_path)
    
    if not (library_path_obj / "library_config.yaml").exists():
        console.print(f"\n[bold red]Error: No library found at {library_path}[/bold red]")
        console.print("[yellow]Tip: Run 'crawler library-create' to create a library first[/yellow]")
        return
    
    console.print(f"[green]✓[/green] Library: {library_path}\n")
    
    # STEP 2: Model Type
    _print_step_header(console, "STEP 2: Topic Modeling Algorithm")
    
    if not model_type:
        model_choices = [
            "NMF (Non-negative Matrix Factorization)",
            "LDA (Latent Dirichlet Allocation)"
        ]
        model_choice_idx = prompter.choice(
            "Select algorithm",
            choices=model_choices,
            default=0
        )
        model_type = "NMF" if model_choice_idx == 0 else "LDA"
    
    model_type = model_type.upper()
    console.print(f"[green]✓[/green] Algorithm: {model_type}\n")
    
    # STEP 3: Number of Topics
    _print_step_header(console, "STEP 3: Number of Topics")
    
    if not num_topics:
        num_topics = prompter.input_int(
            "Number of topics",
            default=5,
            min_value=2
        )
    
    console.print(f"[green]✓[/green] Topics: {num_topics}\n")
    
    # Review Configuration
    console.print("\n" + "=" * 70)
    console.print("[bold]Review Configuration[/bold]")
    console.print("=" * 70)
    console.print(f"[cyan]Library:[/cyan] {library_path}")
    console.print(f"[cyan]Algorithm:[/cyan] {model_type}")
    console.print(f"[cyan]Topics:[/cyan] {num_topics}")
    console.print("=" * 70 + "\n")
    
    if not prompter.confirm("Proceed with topic modeling?"):
        console.print("\n[yellow]Cancelled[/yellow]")
        return
    
    try:
        topic_config = TextProcessingConfig(
            num_topics=num_topics,
            default_topic_model_type=model_type
        )
        
        orchestrator = TopicModelingOrchestrator(topic_config=topic_config)
        
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]RUNNING TOPIC MODELING[/bold cyan]")
        console.print("=" * 70 + "\n")
        
        with console.status("[bold cyan]Processing papers and identifying topics..."):
            labeled_clusters, overview_path = orchestrator.run_topic_modeling(
            library_path=library_path_obj,
            model_type=model_type,
            num_topics=num_topics
        )
        
        _display_results(console, labeled_clusters, library_path_obj, overview_path)
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]")
        raise


def _print_step_header(console: Console, step_text: str):
    """Print step header matching wizard style."""
    console.print("─" * 70)
    console.print(f"[bold cyan]{step_text}[/bold cyan]")
    console.print("─" * 70 + "\n")


def _display_results(console: Console, labeled_clusters, library_path: Path, overview_path: Path):
    """
    Display topic modeling results.
    
    Args:
        console: Rich console
        labeled_clusters: List of TopicCluster objects
        library_path: Library path
        overview_path: Path to overview file
    """
    console.print("\n" + "=" * 70)
    console.print("[bold green]✅ TOPIC MODELING COMPLETE[/bold green]")
    console.print("=" * 70 + "\n")
    
    table = Table(title="Topic Clusters", show_header=True, header_style="bold cyan")
    table.add_column("Topic ID", style="cyan", justify="right")
    table.add_column("Label", style="green")
    table.add_column("Papers", justify="right")
    table.add_column("Top Words", style="dim")
    
    for cluster in sorted(labeled_clusters, key=lambda x: x.cluster_id):
        top_words = ", ".join(cluster.top_words[:5]) if cluster.top_words else "N/A"
        
        table.add_row(
            str(cluster.cluster_id),
            cluster.label,
            str(len(cluster.paper_ids)),
            top_words
        )
    
    console.print(table)
    
    topics_dir = library_path / "topics"
    
    console.print(f"\n[cyan]Papers organized in:[/cyan] {topics_dir}")
    console.print(f"[cyan]Topic overview:[/cyan] {overview_path}")
    console.print(f"[dim]Each topic has its own folder with the papers[/dim]")
    console.print("=" * 70 + "\n")