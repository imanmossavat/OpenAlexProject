"""
Main CLI entry point for ArticleCrawler.

Defines all available commands and orchestrates the application flow.
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import sys

app = typer.Typer(
    name="crawler",
    help="ArticleCrawler - Scientific Literature Discovery Tool",
    add_completion=False,
    no_args_is_help=True
)

console = Console()


@app.command()
def wizard(
    output: Path = typer.Option(
        None, 
        "--output", 
        "-o",
        help="Output directory for experiment"
    )
):
    """
    Interactive setup wizard for new experiments.
    
    Guides you through configuring and starting a new crawl experiment
    with step-by-step prompts for all settings.
    """
    try:
        from .commands.wizard import WizardCommand
        from .ui.prompts import RichPrompter
        from .models.experiment_config import ConfigBuilder
        
        console.print(Panel.fit(
            "[bold cyan]ARTICLE CRAWLER - INTERACTIVE SETUP WIZARD[/bold cyan]",
            border_style="cyan"
        ))
        console.print("\nWelcome! This wizard will guide you through setting up a new crawl experiment.")
        console.print("You can press [bold red]Ctrl+C[/bold red] at any time to cancel.\n")
        
        prompter = RichPrompter(console)
        config_builder = ConfigBuilder()
        wizard_cmd = WizardCommand(prompter, config_builder, console)
        
        config = wizard_cmd.run(output)
        
        if config:
            _run_crawler(config)
        else:
            console.print("\n[yellow]Wizard cancelled.[/yellow]")
            
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Wizard cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        raise


@app.command()
def run(
    config_file: Path = typer.Argument(
        ..., 
        help="Path to config YAML file",
        exists=True,
        file_okay=True,
        dir_okay=False
    )
):
    """
    Run crawler from configuration file.
    
    Load experiment configuration from a YAML file and start crawling.
    """
    try:
        from .utils.config_loader import load_config
        from .commands.run import RunCommand
        
        console.print(f"\n[cyan]Loading configuration from:[/cyan] {config_file}")
        config = load_config(config_file)
        
        run_cmd = RunCommand(console)
        run_cmd.execute(config)
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        raise


@app.command()
def version():
    """Show ArticleCrawler version information."""
    try:
        import ArticleCrawler
        version = getattr(ArticleCrawler, '__version__', 'unknown')
    except:
        version = 'unknown'
    
    console.print(f"\n[bold cyan]ArticleCrawler[/bold cyan] version [bold]{version}[/bold]")
    console.print("Scientific Literature Discovery Tool\n")


def _run_crawler(config):
    """
    Internal function to start crawler with given config.
    
    Args:
        config: ExperimentConfig object with all settings
    """
    from ArticleCrawler import Crawler
    from ArticleCrawler.config.crawler_initialization import CrawlerParameters
    from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    
    try:
        crawl_params = CrawlerParameters(
            seed_paperid=config.seeds,
            keywords=config.keywords
        )
        
        crawler_configs = config.to_crawler_configs()
        
        crawler_configs["storage_config"].experiment_file_name = config.name
        
        md_gen = MarkdownFileGenerator(crawler_configs["storage_config"])
        
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]INITIALIZING CRAWLER[/bold cyan]")
        console.print("=" * 70)
        
        stopping_config = crawler_configs.pop("stopping_config")
        
        crawler = Crawler(
            crawl_initial_condition=crawl_params,
            stopping_criteria_config=stopping_config,
            md_generator=md_gen,
            **crawler_configs
        )
        
        console.print("[green]✓[/green] Crawler initialized successfully")
        
        # Phase 1: Crawling
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]PHASE 1: CRAWLING[/bold cyan]")
        console.print("=" * 70)
        
        crawler.crawl()
        
        console.print("\n[bold green]✅ Crawling completed successfully![/bold green]")
        
        # Phase 2: Markdown Generation
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]PHASE 2: GENERATING MARKDOWN FILES[/bold cyan]")
        console.print("=" * 70)
        
        crawler.generate_markdown_files()
        
        console.print(f"\n[green]✓[/green] Markdown files generated at: {crawler_configs['storage_config'].vault_folder}")
        
        # Phase 3: Analysis
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]PHASE 3: ANALYSIS AND REPORTING[/bold cyan]")
        console.print("=" * 70)
        
        crawler.analyze_and_report(
            save_figures=config.save_figures, 
            num_topics=config.num_topics
        )
        
        console.print("\n[bold green]✅ Analysis and reporting completed![/bold green]")
        
        # Summary
        console.print("\n" + "=" * 70)
        console.print("[bold green]🎉 EXPERIMENT COMPLETE - SUMMARY[/bold green]")
        console.print("=" * 70)
        console.print(f"\n[cyan]Experiment:[/cyan] {config.name}")
        console.print(f"[cyan]API Provider:[/cyan] {config.api_provider}")
        console.print(f"[cyan]Topic Model:[/cyan] {config.topic_model}")
        console.print(f"\n[cyan]Outputs:[/cyan]")
        console.print(f"  - PKL: {crawler_configs['storage_config'].pkl_folder}")
        console.print(f"  - Logs: {crawler_configs['storage_config'].log_folder}")
        console.print(f"  - Vault: {crawler_configs['storage_config'].vault_folder}")
        console.print(f"  - Reports: {crawler_configs['storage_config'].xlsx_folder}")
        console.print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Crawler failed: {e}[/bold red]")
        raise


if __name__ == "__main__":
    app()