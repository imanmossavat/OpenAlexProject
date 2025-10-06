"""
Interactive wizard command for setting up new experiments.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..ui.prompts import Prompter
from ..ui.seed_providers import SEED_PROVIDERS
from ..models.experiment_config import ConfigBuilder, ExperimentConfig


class WizardCommand:
    """
    Orchestrates the interactive wizard flow.
    
    Guides users through experiment setup with step-by-step prompts.
    """
    
    def __init__(self, prompter: Prompter, config_builder: ConfigBuilder, console: Console):
        self.prompter = prompter
        self.config_builder = config_builder
        self.console = console
    
    def run(self, output_dir: Path = None) -> ExperimentConfig:
        """
        Run the wizard and return configured experiment.
        
        Args:
            output_dir: Optional output directory override
            
        Returns:
            ExperimentConfig object ready for crawler
        """
        try:
            # Step 1: Experiment Name
            name = self._get_experiment_name()
            self.config_builder.with_name(name)
            
            # Determine output folder
            if output_dir:
                root_folder = output_dir
            else:
                root_folder = Path.cwd() / 'data' / 'crawler_experiments'
            
            self.config_builder.with_root_folder(root_folder)
            experiment_folder = root_folder / name
            self.console.print(f"[green]✓[/green] Experiment will be saved to: {experiment_folder}\n")
            
            # Step 2: Seed Papers
            seeds = self._get_seed_papers()
            self.config_builder.with_seeds(seeds)
            
            # Step 3: Keywords
            keywords = self._get_keywords()
            self.config_builder.with_keywords(keywords)
            
            # Step 4: Basic Configuration
            self._get_basic_config()
            
            # Step 5: Advanced Options (optional)
            if self.prompter.confirm("\nConfigure advanced settings?", default=False):
                self._get_advanced_config()
            else:
                self.console.print("\n[green]✓[/green] Using default settings for:")
                self.console.print("  - Topic modeling (NMF, 20 topics)")
                self.console.print("  - Graph options (no author nodes)")
                self.console.print("  - Retraction watch (enabled)")
                self.console.print("  - Save figures (enabled)")
                self.console.print("  - Ignored venues (ArXiv, medRxiv, WWW)")
                self.console.print("  - Language (English)")
            
            # Step 6: Review & Confirm
            config = self.config_builder.build()
            
            if self._review_and_confirm(config):
                return config
            else:
                self.console.print("\n[yellow]Configuration cancelled.[/yellow]")
                return None
                
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️  Wizard cancelled by user[/yellow]")
            return None
    
    def _get_experiment_name(self) -> str:
        """Step 1: Get experiment name."""
        self._print_step_header("STEP 1: Experiment Name")
        
        while True:
            name = self.prompter.input("Enter a name for this experiment")
            
            # Validate name
            if not name or not name.strip():
                self.prompter.error("Experiment name cannot be empty")
                continue
            
            # Clean name
            clean_name = "".join(c for c in name if c.isalnum() or c in "_ -")
            if clean_name != name:
                self.console.print(f"[yellow]Note: Name sanitized to:[/yellow] {clean_name}")
                name = clean_name
            
            return name
    
    def _get_seed_papers(self) -> list[str]:
        """Step 2: Get seed papers using pluggable providers."""
        self._print_step_header("STEP 2: Seed Papers")
        
        # Get available providers
        providers = [Provider(self.prompter) for Provider in SEED_PROVIDERS]
        choices = [p.display_name() for p in providers]
        
        self.console.print("How would you like to provide seed papers?\n")
        
        choice_idx = self.prompter.choice(
            "Select method",
            choices=choices
        )
        
        selected_provider = providers[choice_idx]
        
        try:
            seeds = selected_provider.get_seeds()
            
            if not seeds:
                self.prompter.error("No seeds provided. You need at least one seed paper.")
                return self._get_seed_papers()  # Retry
            
            self.console.print(f"[green]✓[/green] Loaded {len(seeds)} seed papers\n")
            return seeds
            
        except NotImplementedError:
            self.prompter.error("This feature is not yet implemented.")
            return self._get_seed_papers()  # Retry with different method
        except Exception as e:
            self.prompter.error(f"Error loading seeds: {e}")
            return self._get_seed_papers()  # Retry
    
    def _get_keywords(self) -> list[str]:
        """Step 3: Get keyword filters."""
        self._print_step_header("STEP 3: Keywords")
        
        self.console.print("Enter keyword filters (one per line, blank line when done):")
        self.console.print("[dim]Use operators: AND, OR, NOT, parentheses for grouping[/dim]\n")
        
        keywords = []
        idx = 1
        
        while True:
            keyword = self.prompter.input(f"Keyword {idx}").strip()
            
            if not keyword:
                break
            
            keywords.append(keyword)
            idx += 1
        
        if not keywords:
            self.console.print("[yellow]⚠️  No keywords provided. Crawler will process all papers.[/yellow]\n")
        else:
            self.console.print(f"[green]✓[/green] Added {len(keywords)} keyword filters\n")
        
        return keywords
    
    def _get_basic_config(self):
        """Step 4: Get basic configuration."""
        self._print_step_header("STEP 4: Basic Configuration")
        
        # Papers per iteration
        papers_per_iter = self.prompter.input_int(
            "Papers per iteration",
            default=1,
            min_value=1
        )
        self.config_builder.with_papers_per_iteration(papers_per_iter)
        
        # Max iterations
        max_iter = self.prompter.input_int(
            "Maximum iterations",
            default=1,
            min_value=1
        )
        self.config_builder.with_max_iterations(max_iter)
        
        # API provider
        api_choice = self.prompter.choice(
            "API provider",
            choices=["openalex", "semantic_scholar"],
            default=0
        )
        self.config_builder.with_api_provider(
            "openalex" if api_choice == 0 else "semantic_scholar"
        )
        
        self.console.print("[green]✓[/green] Configuration saved\n")
    
    def _get_advanced_config(self):
        """Step 5: Get advanced configuration."""
        self._print_step_header("STEP 5: Advanced Options")
        
        # Topic modeling
        num_topics = self.prompter.input_int(
            "Number of topics for topic modeling",
            default=20,
            min_value=2
        )
        self.config_builder.with_num_topics(num_topics)
        
        model_choice = self.prompter.choice(
            "Topic modeling algorithm",
            choices=["NMF", "LDA"],
            default=0
        )
        self.config_builder.with_topic_model("NMF" if model_choice == 0 else "LDA")
        
        # Graph options
        include_authors = self.prompter.confirm(
            "Include author nodes in graph?",
            default=False
        )
        self.config_builder.with_include_author_nodes(include_authors)
        
        # Retraction watch
        enable_retraction = self.prompter.confirm(
            "Enable retraction watch?",
            default=True
        )
        self.config_builder.with_enable_retraction_watch(enable_retraction)

        save_figs = self.prompter.confirm(
            "Save topic modeling figures? (PNG files for visualization)",
            default=True
        )
        self.config_builder.with_save_figures(save_figs)

        if self.prompter.confirm("\nCustomize ignored venues?", default=False):
            self.console.print("\n[dim]Default ignored: '', 'ArXiv', 'medRxiv', 'WWW'[/dim]")
            self.console.print("Enter additional venues to ignore (one per line, blank when done):")
            
            custom_venues = []
            idx = 1
            while True:
                venue = self.prompter.input(f"Venue {idx}").strip()
                if not venue:
                    break
                custom_venues.append(venue)
                self.console.print(f"[green]✓[/green] Added: {venue}")
                idx += 1
            
            if custom_venues:
                # Merge with defaults
                all_ignored = ["", "ArXiv", "medRxiv", "WWW"] + custom_venues
                self.config_builder.with_ignored_venues(all_ignored)
                self.console.print(f"[green]✓[/green] Total ignored venues: {len(all_ignored)}")

        language_choice = self.prompter.choice(
            "Language for text processing",
            choices=[
                "English (en)",
                "Spanish (es)", 
                "French (fr)",
                "German (de)",
                "Other (specify)"
            ],
            default=0
        )
        
        if language_choice == 4:  # Other
            custom_lang = self.prompter.input("Enter ISO 639-1 language code (e.g., 'it', 'pt', 'zh')")
            self.config_builder.with_language(custom_lang)
        else:
            lang_map = {0: "en", 1: "es", 2: "fr", 3: "de"}
            self.config_builder.with_language(lang_map[language_choice])
        
        self.console.print("[green]✓[/green] Advanced options configured\n")
    
    def _review_and_confirm(self, config: ExperimentConfig) -> bool:
        """Step 6: Review configuration and confirm."""
        self._print_step_header("STEP 6: Review & Confirm")
        
        # Display summary
        self.console.print(f"[cyan]Experiment:[/cyan] {config.name}")
        self.console.print(f"[cyan]Seed papers:[/cyan] {len(config.seeds)}")
        self.console.print(f"[cyan]Keywords:[/cyan] {len(config.keywords)} filters")
        self.console.print(f"[cyan]Papers/iteration:[/cyan] {config.papers_per_iteration}")
        self.console.print(f"[cyan]Max iterations:[/cyan] {config.max_iterations}")
        self.console.print(f"[cyan]API:[/cyan] {config.api_provider}")
        self.console.print(f"[cyan]Output:[/cyan] {config.root_folder / config.name}")
        self.console.print(f"[cyan]Language:[/cyan] {config.language}")
        self.console.print(f"[cyan]Save figures:[/cyan] {'Yes' if config.save_figures else 'No'}")
        self.console.print(f"[cyan]Ignored venues:[/cyan] {len(config.ignored_venues)} venues")
        
        # Confirm
        return self.prompter.confirm("\nStart crawling now?", default=True)
    
    def _print_step_header(self, title: str):
        """Print a step header."""
        self.console.print("\n" + "━" * 70)
        self.console.print(f"[bold cyan]{title}[/bold cyan]")
        self.console.print("━" * 70 + "\n")