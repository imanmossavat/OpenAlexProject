from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..ui.prompts import Prompter
from ..ui.seed_providers import SEED_PROVIDERS, PDFSeedProvider
from ..models.experiment_config import ConfigBuilder, ExperimentConfig


class WizardCommand:
    
    def __init__(self, prompter: Prompter, config_builder: ConfigBuilder, console: Console):
        self.prompter = prompter
        self.config_builder = config_builder
        self.console = console
    
    def run(self, output_dir: Path = None) -> ExperimentConfig:
        try:
            name = self._get_experiment_name()
            self.config_builder.with_name(name)
            
            if output_dir:
                root_folder = output_dir
            else:
                root_folder = Path.cwd() / 'data' / 'crawler_experiments'
            
            self.config_builder.with_root_folder(root_folder)
            experiment_folder = root_folder / name
            self.console.print(f"[green]✓[/green] Experiment will be saved to: {experiment_folder}\n")
            
            api_choice = self._get_api_provider()
            
            seeds = self._get_seed_papers(api_choice)
            self.config_builder.with_seeds(seeds)
            
            keywords = self._get_keywords()
            self.config_builder.with_keywords(keywords)
            
            self._get_basic_config()
            
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
            
            config = self.config_builder.build()
            
            if self._review_and_confirm(config):
                return config
            else:
                self.console.print("\n[yellow]Configuration cancelled.[/yellow]")
                return None
                
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️ Wizard cancelled by user[/yellow]")
            return None
    
    def _print_step_header(self, title: str):
        self.console.print()
        self.console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
        self.console.print()
    
    def _get_experiment_name(self) -> str:
        self._print_step_header("STEP 1: Experiment Name")
        
        while True:
            name = self.prompter.input("Enter a name for this experiment")
            
            if not name or not name.strip():
                self.prompter.error("Experiment name cannot be empty")
                continue
            
            clean_name = "".join(c for c in name if c.isalnum() or c in "_ -")
            if clean_name != name:
                self.console.print(f"[yellow]Note: Name sanitized to:[/yellow] {clean_name}")
                name = clean_name
            
            return name
    
    def _get_api_provider(self) -> str:
        self._print_step_header("STEP 2: API Provider")
        
        api_choice = self.prompter.choice(
            "Select API provider",
            choices=["openalex", "semantic_scholar"],
            default=0
        )
        
        api_provider = "openalex" if api_choice == 0 else "semantic_scholar"
        self.config_builder.with_api_provider(api_provider)
        
        self.console.print(f"[green]✓[/green] Using {api_provider}\n")
        return api_provider
    
    def _get_seed_papers(self, api_provider: str) -> list[str]:
        self._print_step_header("STEP 3: Seed Papers")
        
        providers = [
            Provider(self.prompter) if Provider != PDFSeedProvider 
            else Provider(self.prompter, api_provider) 
            for Provider in SEED_PROVIDERS
        ]
        
        choices = [p.display_name() for p in providers]
        
        self.console.print("How would you like to provide seed papers?\n")
        
        choice_idx = self.prompter.choice("Select method", choices=choices)
        
        selected_provider = providers[choice_idx]
        
        try:
            seeds = selected_provider.get_seeds()
            
            if not seeds:
                self.prompter.error("No seeds provided. You need at least one seed paper.")
                return self._get_seed_papers(api_provider)
            
            initial_seed_count = len(seeds)
            is_pdf_provider = isinstance(selected_provider, PDFSeedProvider)
            
            if is_pdf_provider:
                pdf_seed_count = initial_seed_count
                all_seeds = seeds
            else:
                if self.prompter.confirm("\nAlso add seeds from PDF files?", default=False):
                    pdf_provider = PDFSeedProvider(self.prompter, api_provider)
                    pdf_seeds = pdf_provider.get_seeds()
                    all_seeds = seeds + pdf_seeds
                    pdf_seed_count = len(pdf_seeds)
                else:
                    all_seeds = seeds
                    pdf_seed_count = 0
            
            self.config_builder._config['_pdf_seed_count'] = pdf_seed_count
            self.config_builder._config['_initial_seed_count'] = initial_seed_count
            
            self.console.print(f"[green]✓[/green] Loaded {len(all_seeds)} total seed papers")
            if pdf_seed_count > 0:
                non_pdf_count = 0 if is_pdf_provider else initial_seed_count
                if is_pdf_provider:
                    self.console.print(f"[dim]  ({pdf_seed_count} from PDF)[/dim]\n")
                else:
                    self.console.print(f"[dim]  ({non_pdf_count} from primary source, {pdf_seed_count} from PDF)[/dim]\n")
            else:
                self.console.print()
            
            return all_seeds
            
        except NotImplementedError:
            self.prompter.error("This feature is not yet implemented.")
            return self._get_seed_papers(api_provider)
        except Exception as e:
            self.prompter.error(f"Error loading seeds: {e}")
            return self._get_seed_papers(api_provider)
    
    def _get_keywords(self) -> list[str]:
        self._print_step_header("STEP 4: Keywords")
        
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
            self.console.print("[yellow]⚠️ No keywords provided. Crawler will process all papers.[/yellow]\n")
        else:
            self.console.print(f"[green]✓[/green] Added {len(keywords)} keyword filter(s)\n")
        
        return keywords
    
    def _get_basic_config(self):
        self._print_step_header("STEP 5: Basic Configuration")
        
        max_iterations = self.prompter.input_int(
            "Maximum iterations",
            default=1,
            min_value=1
        )
        self.config_builder.with_max_iterations(max_iterations)
        
        papers_per_iteration = self.prompter.input_int(
            "Papers per iteration",
            default=1,
            min_value=1
        )
        self.config_builder.with_papers_per_iteration(papers_per_iteration)
        
        self.console.print(f"[green]✓[/green] Basic configuration complete\n")
    
    def _get_advanced_config(self):
        self._print_step_header("STEP 6: Advanced Configuration")
        
        topic_choice = self.prompter.choice(
            "Topic modeling algorithm",
            choices=["NMF (Non-negative Matrix Factorization)", "LDA (Latent Dirichlet Allocation)"],
            default=0
        )
        topic_model = "NMF" if topic_choice == 0 else "LDA"
        self.config_builder.with_topic_model(topic_model)
        
        num_topics = self.prompter.input_int(
            "Number of topics",
            default=20,
            min_value=2
        )
        self.config_builder.with_num_topics(num_topics)
        
        include_authors = self.prompter.confirm(
            "Include author nodes in graph?",
            default=False
        )
        self.config_builder.with_include_author_nodes(include_authors)
        
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
        
        if language_choice == 4:
            custom_lang = self.prompter.input("Enter ISO 639-1 language code (e.g., 'it', 'pt', 'zh')")
            self.config_builder.with_language(custom_lang)
        else:
            lang_map = {0: "en", 1: "es", 2: "fr", 3: "de"}
            self.config_builder.with_language(lang_map[language_choice])
        
        self.console.print("[green]✓[/green] Advanced options configured\n")
    
    def _review_and_confirm(self, config: ExperimentConfig) -> bool:
        self._print_step_header("STEP 7: Review & Confirm")
        
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
        
        return self.prompter.confirm("\nStart crawling now?", default=True)