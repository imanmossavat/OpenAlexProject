import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from typing import Optional
import questionary
from questionary import Style
import tempfile
import sys

from ArticleCrawler.usecases.author_topic_evolution_usecase import AuthorTopicEvolutionUseCase
from ArticleCrawler.library.author_search_service import AuthorSearchService
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
from ArticleCrawler.library.temporal_analysis_service import TemporalAnalysisService
from ArticleCrawler.visualization.topic_evolution_visualizer import (
    LineChartVisualizer,
    HeatmapVisualizer,
    StackedAreaVisualizer
)
from ArticleCrawler.utils.library_temp_manager import TempLibraryManager
from ArticleCrawler.config.text_config import TextProcessingConfig
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
from ArticleCrawler.visualization.visualization_config import VisualizationConfig
from ArticleCrawler.api import create_api_provider
from ArticleCrawler.LogManager.crawler_logger import CrawlerLogger
from ArticleCrawler.library.models import AuthorInfo

console = Console()

custom_style = Style([
    ('question', 'fg:#00ffff bold'),
    ('answer', 'fg:#00ff00 bold'),
    ('pointer', 'fg:#00ffff bold'),
    ('selected', 'fg:#00ff00'),
    ('separator', 'fg:#666666'),
])


def author_topic_evolution_command():
    """
    Analyze how an author's research topics evolve over time.
    
    Interactive wizard that guides you through:
    - Searching and selecting an author
    - Configuring topic modeling parameters
    - Performing temporal analysis
    - Generating visualizations
    """
    try:
        _print_welcome()
        
        logger, api_provider = _initialize_services()
        
        author = _search_and_select_author(api_provider, logger)
        if not author:
            console.print("\n[yellow]Analysis cancelled.[/yellow]")
            return
        
        use_advanced = _choose_config_mode()
        
        if use_advanced:
            config = _get_advanced_config()
        else:
            config = _get_default_config()
        
        if not config:
            console.print("\n[yellow]Analysis cancelled.[/yellow]")
            return
        
        if not _review_and_confirm(author, config):
            console.print("\n[yellow]Analysis cancelled.[/yellow]")
            return
        
        result = _run_analysis(author, config, logger, api_provider)
        
        _display_results(result)
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Analysis cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        raise


def _print_welcome():
    """Print welcome header."""
    console.print(Panel.fit(
        "[bold cyan]AUTHOR TOPIC EVOLUTION ANALYZER[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\nAnalyze how an author's research topics change over time.")
    console.print("You can press [bold red]Ctrl+C[/bold red] at any time to cancel.\n")


def _initialize_services():
    """Initialize logger and API provider."""
    console.print("[cyan]Initializing services...[/cyan]")
    
    try:
        from ArticleCrawler.config.storage_config import StorageAndLoggingConfig
        from pathlib import Path
        import tempfile
        
        temp_dir = Path(tempfile.gettempdir()) / "author_evolution_logs"
        temp_dir.mkdir(exist_ok=True)
        
        storage_config = StorageAndLoggingConfig(
            experiment_file_name='author_evolution',
            root_folder=temp_dir,
            log_level='INFO'
        )
        
        logger = CrawlerLogger(storage_config)
        api_provider = create_api_provider('openalex', logger=logger)
        console.print("[green]✓[/green] Services initialized\n")
        return logger, api_provider
    except Exception as e:
        console.print(f"[red]Failed to initialize services: {e}[/red]")
        raise


def _print_step_header(step_text: str):
    """Print a step header."""
    console.print(f"\n[bold cyan]═══ {step_text} ═══[/bold cyan]\n")


def _search_and_select_author(api_provider, logger) -> Optional[AuthorInfo]:
    """Search for and select an author."""
    _print_step_header("STEP 1: Find Author")
    
    author_name = Prompt.ask("[cyan]Enter author name[/cyan]")
    
    if not author_name or not author_name.strip():
        console.print("[red]Author name is required[/red]")
        return None
    
    console.print(f"\n[cyan]Searching for '{author_name}'...[/cyan]")
    
    author_search_service = AuthorSearchService(api_provider, logger)
    
    with console.status("[bold cyan]Searching..."):
        authors = author_search_service.search_authors(author_name.strip(), limit=10)
    
    if not authors:
        console.print(f"[yellow]No authors found for '{author_name}'[/yellow]")
        
        if Confirm.ask("Try another search?", default=True):
            return _search_and_select_author(api_provider, logger)
        return None
    
    console.print(f"[green]Found {len(authors)} authors:[/green]\n")
    
    choices = []
    for i, author in enumerate(authors, 1):
        institution = author.institutions[0] if author.institutions else "No affiliation"
        label = f"{i}. {author.name} - {institution} ({author.works_count} papers, {author.cited_by_count:,} citations)"
        choices.append(questionary.Choice(label, value=i-1))
    
    selection = questionary.select(
        "Select an author:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if selection is None:
        return None
    
    selected_author = authors[selection]
    console.print(f"\n[green]✓ Selected:[/green] {selected_author.name}")
    console.print(f"  [dim]Papers: {selected_author.works_count}, Citations: {selected_author.cited_by_count:,}[/dim]\n")
    
    return selected_author


def _choose_config_mode() -> bool:
    """Choose between default and advanced configuration."""
    _print_step_header("STEP 2: Configuration Mode")
    
    console.print("Choose your configuration preference:\n")
    console.print("  [cyan]Default[/cyan]:  Quick setup with recommended settings")
    console.print("  [cyan]Advanced[/cyan]: Customize all parameters\n")
    
    choice = questionary.select(
        "Configuration mode:",
        choices=[
            questionary.Choice("Default (Recommended)", value=False),
            questionary.Choice("Advanced", value=True)
        ],
        style=custom_style
    ).ask()
    
    return choice if choice is not None else False


def _get_default_config() -> Optional[dict]:
    """Get default configuration."""
    _print_step_header("STEP 3: Configuration")
    
    console.print("[cyan]Using default configuration:[/cyan]\n")
    console.print("  • Topic Model: [green]NMF[/green]")
    console.print("  • Number of Topics: [green]5[/green]")
    console.print("  • Time Period: [green]3 years[/green]")
    console.print("  • Visualization: [green]Line Chart[/green]")
    console.print("  • Library: [green]Temporary[/green]")
    console.print()
    
    console.print("[yellow]⚠️  Using temporary library (deleted on exit)[/yellow]")
    output_path_str = Prompt.ask(
        "[cyan]Where to save visualization[/cyan]", 
        default="./topic_evolution.png"
    )
    output_path = Path(output_path_str)
    
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    console.print()
    
    return {
        'model_type': 'NMF',
        'num_topics': 5,
        'time_period_years': 3,
        'viz_type': 'line',
        'save_library': False,
        'library_path': None,
        'output_path': output_path,
        'max_papers': None
    }


def _get_advanced_config() -> Optional[dict]:
    """Get advanced configuration through prompts."""
    _print_step_header("STEP 3: Advanced Configuration")
    
    model_choice = questionary.select(
        "Topic modeling algorithm:",
        choices=[
            questionary.Choice("NMF (Non-negative Matrix Factorization)", value="NMF"),
            questionary.Choice("LDA (Latent Dirichlet Allocation)", value="LDA")
        ],
        style=custom_style
    ).ask()
    
    if model_choice is None:
        return None
    
    num_topics_str = Prompt.ask("[cyan]Number of topics[/cyan]", default="5")
    try:
        num_topics = int(num_topics_str)
        if num_topics < 2:
            console.print("[red]Number of topics must be at least 2[/red]")
            return None
    except ValueError:
        console.print("[red]Invalid number[/red]")
        return None
    
    time_period_str = Prompt.ask("[cyan]Years per time period[/cyan]", default="3")
    try:
        time_period_years = int(time_period_str)
        if time_period_years < 1:
            console.print("[red]Time period must be at least 1 year[/red]")
            return None
    except ValueError:
        console.print("[red]Invalid number[/red]")
        return None
    
    viz_choice = questionary.select(
        "Visualization type:",
        choices=[
            questionary.Choice("Line Chart (topic trends over time)", value="line"),
            questionary.Choice("Heatmap (topic intensity matrix)", value="heatmap"),
            questionary.Choice("Stacked Area (topic composition)", value="stacked")
        ],
        style=custom_style
    ).ask()
    
    if viz_choice is None:
        return None
    
    if Confirm.ask("\n[cyan]Limit number of papers to analyze?[/cyan]", default=False):
        max_papers_str = Prompt.ask("Maximum papers", default="100")
        try:
            max_papers = int(max_papers_str)
        except ValueError:
            console.print("[yellow]Invalid number, using no limit[/yellow]")
            max_papers = None
    else:
        max_papers = None
    
    console.print("\n[bold]Library Storage:[/bold]")
    save_library = Confirm.ask("[cyan]Save library permanently?[/cyan]", default=False)
    library_path = None
    output_path = None
    
    if save_library:
        library_path_str = Prompt.ask("[cyan]Library path[/cyan]", default="./libraries")
        library_path = Path(library_path_str)
        
        if not library_path.exists():
            library_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Created directory: {library_path}[/green]")
        
        if Confirm.ask("[cyan]Also save visualization to a different location?[/cyan]", default=False):
            output_path_str = Prompt.ask("[cyan]Visualization output path[/cyan]", default="./topic_evolution.png")
            output_path = Path(output_path_str)
    else:
        console.print("\n[yellow]⚠️  Temporary library will be deleted on exit.[/yellow]")
        console.print("[yellow]You MUST specify where to save the visualization.[/yellow]\n")
        
        output_path_str = Prompt.ask(
            "[cyan]Where to save visualization[/cyan]", 
            default="./topic_evolution.png"
        )
        output_path = Path(output_path_str)
        
        if not output_path.parent.exists():
            if Confirm.ask(f"[cyan]Create directory {output_path.parent}?[/cyan]", default=True):
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                console.print("[red]Cannot save without output directory[/red]")
                return None
    
    console.print("\n[green]✓[/green] Configuration complete\n")
    
    return {
        'model_type': model_choice,
        'num_topics': num_topics,
        'time_period_years': time_period_years,
        'viz_type': viz_choice,
        'save_library': save_library,
        'library_path': library_path,
        'output_path': output_path,
        'max_papers': max_papers
    }



def _review_and_confirm(author: AuthorInfo, config: dict) -> bool:
    """Review configuration and confirm."""
    _print_step_header("STEP 4: Review & Confirm")
    
    console.print(f"[cyan]Author:[/cyan] {author.name}")
    console.print(f"[cyan]Papers Available:[/cyan] {author.works_count}")
    if config['max_papers']:
        console.print(f"[cyan]Papers to Analyze:[/cyan] {config['max_papers']}")
    console.print(f"[cyan]Model:[/cyan] {config['model_type']}")
    console.print(f"[cyan]Topics:[/cyan] {config['num_topics']}")
    console.print(f"[cyan]Time Period:[/cyan] {config['time_period_years']} years")
    console.print(f"[cyan]Visualization:[/cyan] {config['viz_type'].title()}")
    
    if config['save_library']:
        console.print(f"[cyan]Library:[/cyan] {config['library_path']} (permanent)")
    else:
        console.print(f"[cyan]Library:[/cyan] Temporary")
    
    if config['output_path']:
        console.print(f"[cyan]Output:[/cyan] {config['output_path']}")
    
    console.print()
    return Confirm.ask("[bold]Start analysis now?[/bold]", default=True)


def _run_analysis(author, config, logger, api_provider):
    """Run the complete analysis workflow."""
    _print_step_header("STEP 5: Running Analysis")
    
    console.print("[cyan]This may take a few minutes...[/cyan]\n")
    
    if config['save_library'] and config['library_path']:
        safe_author_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in author.name)
        safe_author_name = safe_author_name.replace(' ', '_')
        
        author_library_path = config['library_path'] / f"author_library_{safe_author_name}"
        
        if author_library_path.exists():
            counter = 1
            original_path = author_library_path
            while author_library_path.exists():
                author_library_path = Path(f"{original_path}_{counter}")
                counter += 1
            console.print(f"[yellow]Library exists, using: {author_library_path.name}[/yellow]")
        
        config['library_path'] = author_library_path
        console.print(f"[cyan]Library will be saved to:[/cyan] {author_library_path}\n")
    
    library_manager = LibraryManager(logger=logger)
    temp_library_manager = TempLibraryManager(logger=logger)
    
    from ArticleCrawler.config.storage_config import StorageAndLoggingConfig
    
    temp_storage_config = StorageAndLoggingConfig(
        experiment_file_name='author_evolution',
        root_folder=Path(tempfile.gettempdir()) / 'author_evolution',
        log_level='INFO'
    )
    
    markdown_writer = MarkdownFileGenerator(
        storage_and_logging_options=temp_storage_config,
        api_provider_type='openalex'
    )
    
    topic_config = TextProcessingConfig(
        num_topics=config['num_topics'],
        default_topic_model_type=config['model_type']
    )
    topic_orchestrator = TopicModelingOrchestrator(topic_config=topic_config)
    
    temporal_config = TemporalAnalysisConfig(
        time_period_years=config['time_period_years'],
        min_papers_per_period=2,
        period_strategy="fixed"
    )
    temporal_analyzer = TemporalAnalysisService(temporal_config, logger)
    
    viz_config = VisualizationConfig(
        figure_width=14,
        figure_height=8,
        show_grid=True,
        legend_location='best'
    )
    
    if config['viz_type'] == "line":
        visualizer = LineChartVisualizer(viz_config, logger)
    elif config['viz_type'] == "heatmap":
        visualizer = HeatmapVisualizer(viz_config, logger)
    elif config['viz_type'] == "stacked":
        visualizer = StackedAreaVisualizer(viz_config, logger)
    else:
        visualizer = LineChartVisualizer(viz_config, logger)
    
    use_case = AuthorTopicEvolutionUseCase(
        api_provider=api_provider,
        author_search_service=AuthorSearchService(api_provider, logger),
        library_manager=library_manager,
        topic_orchestrator=topic_orchestrator,
        temporal_analyzer=temporal_analyzer,
        visualizer=visualizer,
        temp_library_manager=temp_library_manager,
        markdown_writer=markdown_writer,
        logger=logger
    )
    
    with console.status("[bold cyan]Fetching papers..."):
        result = use_case.run(
            author=author,
            model_type=config['model_type'],
            num_topics=config['num_topics'],
            save_library=config['save_library'],
            library_path=config['library_path'],
            output_path=config['output_path'],
            max_papers=config['max_papers']
        )
    
    return result

def _display_results(result):
    """Display analysis results."""
    _print_step_header("ANALYSIS COMPLETE")
    
    console.print(Panel.fit(
        "[bold green]✓ Success![/bold green]\n"
        f"Analyzed {result.temporal_data.total_papers} papers across "
        f"{len(result.temporal_data.time_periods)} time periods",
        border_style="green"
    ))
    
    console.print("\n[bold]Summary:[/bold]\n")
    console.print(f"  [cyan]Author:[/cyan] {result.author.name}")
    console.print(f"  [cyan]Time Span:[/cyan] {result.temporal_data.time_periods[0]} → {result.temporal_data.time_periods[-1]}")
    console.print(f"  [cyan]Topics Found:[/cyan] {len(result.temporal_data.topic_labels)}")
    
    console.print("\n[bold]Time Periods:[/bold]\n")
    for i, period in enumerate(result.temporal_data.time_periods):
        count = result.temporal_data.paper_counts_per_period[i]
        console.print(f"  • {period}: [green]{count} papers[/green]")
    
    console.print("\n[bold]Topics Identified:[/bold]\n")
    for i, topic in enumerate(result.temporal_data.topic_labels, 1):
        console.print(f"  {i}. {topic}")
    
    emerging = result.temporal_data.get_emerging_topics(threshold=0.5)
    if emerging:
        console.print("\n[bold green]📈 Emerging Topics:[/bold green]\n")
        for topic in emerging:
            console.print(f"  • {topic}")
    
    declining = result.temporal_data.get_declining_topics(threshold=0.5)
    if declining:
        console.print("\n[bold yellow]📉 Declining Topics:[/bold yellow]\n")
        for topic in declining:
            console.print(f"  • {topic}")
    
    console.print("\n[bold]Output Files:[/bold]\n")
    
    if result.is_temporary:
        console.print(f"  [cyan]Visualization:[/cyan] {result.visualization_path}")
        console.print("\n  [yellow]💡 Tip: Use advanced config to save permanently[/yellow]")
    else:
        console.print(f"  [cyan]Library:[/cyan] {result.library_path}")
        console.print(f"  [cyan]Visualization:[/cyan] {result.visualization_path}")
    
    console.print()