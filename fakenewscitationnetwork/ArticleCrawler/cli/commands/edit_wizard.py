from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..ui.prompts import Prompter
from ..models.experiment_config import ExperimentConfig, ConfigBuilder
from ..utils.config_loader import load_config
from ..utils.config_discovery import ConfigDiscovery, ConfigSummary
from .wizard import WizardCommand
from typing import Optional, List, Any

class EditWizardCommand:
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def run(self, config_path: Optional[Path] = None) -> Optional[ExperimentConfig]:
        try:
            if config_path:
                source_config = load_config(config_path)
                self.console.print(f"[green]✓[/green] Loaded configuration from: {config_path}\n")
            else:
                source_config = self._select_experiment()
                if not source_config:
                    return None
            
            new_name = self._get_new_experiment_name(source_config.name)
            
            config_builder = ConfigBuilder()
            self._populate_builder_from_config(config_builder, source_config)
            config_builder.with_name(new_name)
            
            wizard_cmd = WizardCommand(self.prompter, config_builder, self.console)
            
            while True:
                choice = self._show_edit_menu()
                
                if choice == 1:
                    self._edit_api_provider(config_builder, wizard_cmd)
                elif choice == 2:
                    self._edit_seeds(config_builder, wizard_cmd)
                elif choice == 3:
                    self._edit_keywords(config_builder)
                elif choice == 4:
                    self._edit_basic_config(config_builder, wizard_cmd)
                elif choice == 5:
                    self._edit_advanced_config(config_builder, wizard_cmd)
                elif choice == 6:
                    config = config_builder.build()
                    if self._review_and_confirm(config):
                        return config
                    else:
                        continue
                elif choice == 7:
                    self.console.print("\n[yellow]Edit cancelled.[/yellow]")
                    return None
                    
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]⚠️  Edit wizard cancelled by user[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"\n[bold red]✗ Error: {e}[/bold red]")
            raise
    
    def _select_experiment(self) -> Optional[ExperimentConfig]:
        self.console.print(Panel.fit(
            "[bold cyan]SELECT EXPERIMENT TO EDIT[/bold cyan]",
            border_style="cyan"
        ))
        
        choice = self.prompter.choice(
            "\nHow would you like to select the configuration?",
            choices=[
                "From existing experiments",
                "Specify custom config file path"
            ],
            default=0
        )
        
        if choice == 0:
            return self._select_from_existing()
        else:
            return self._select_from_path()
    
    def _select_from_existing(self) -> Optional[ExperimentConfig]:
        root_folder = ConfigDiscovery.get_default_experiments_folder()
        
        if not root_folder.exists():
            self.console.print(f"\n[yellow]Experiments folder does not exist: {root_folder}[/yellow]")
            self.console.print("[yellow]Please specify a custom config file path instead.[/yellow]\n")
            return self._select_from_path()
        
        experiments = ConfigDiscovery.find_experiments(root_folder)
        
        if not experiments:
            self.console.print(f"\n[yellow]No experiments found in {root_folder}[/yellow]")
            self.console.print("[yellow]Looking for folders containing config.yaml files...[/yellow]\n")
            
            if self.prompter.confirm("Would you like to specify a custom config file path?", default=True):
                return self._select_from_path()
            return None
        
        self._display_experiments_table(experiments)
        
        selected_idx = self.prompter.input_int(
            f"\nSelect experiment [1-{len(experiments)}]",
            min_value=1,
            max_value=len(experiments)
        )
        
        selected = experiments[selected_idx - 1]
        return load_config(selected.config_path)
    
    def _select_from_path(self) -> Optional[ExperimentConfig]:
        config_path_str = self.prompter.input("Enter path to config.yaml file")
        config_path = Path(config_path_str)
        
        if not config_path.exists():
            self.prompter.error(f"Config file not found: {config_path}")
            return None
        
        if config_path.is_dir():
            config_path = config_path / 'config.yaml'
            if not config_path.exists():
                self.prompter.error(f"Config file not found in directory: {config_path}")
                return None
        
        try:
            config = load_config(config_path)
            self.console.print(f"[green]✓[/green] Configuration loaded successfully\n")
            return config
        except Exception as e:
            self.prompter.error(f"Failed to load config: {e}")
            self.console.print("\n[yellow]This config file may be from an older version or is missing required fields.[/yellow]")
            self.console.print("[yellow]Required fields: name, seeds, keywords, api_provider[/yellow]\n")
            return None
    
    def _display_experiments_table(self, experiments: List[ConfigSummary]):
        table = Table(title="Available Experiments")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Name", style="bold")
        table.add_column("Created", style="dim")
        table.add_column("Seeds", justify="right")
        table.add_column("Keywords", justify="right")
        table.add_column("API", style="green")
        
        for idx, exp in enumerate(experiments, 1):
            created_str = exp.created.strftime("%Y-%m-%d %H:%M") if exp.created else "Unknown"
            table.add_row(
                str(idx),
                exp.name,
                created_str,
                str(exp.num_seeds),
                str(exp.num_keywords),
                exp.api_provider
            )
        
        self.console.print("\n")
        self.console.print(table)
    
    def _get_new_experiment_name(self, source_name: str) -> str:
        self.console.print(f"\n[cyan]Source experiment:[/cyan] {source_name}")
        self.console.print("[dim]Enter a new name for the edited experiment[/dim]\n")
        
        while True:
            name = self.prompter.input("New experiment name")
            
            if not name or not name.strip():
                self.prompter.error("Experiment name cannot be empty")
                continue
            
            clean_name = "".join(c for c in name if c.isalnum() or c in "_ -")
            if clean_name != name:
                self.console.print(f"[yellow]Note: Name sanitized to:[/yellow] {clean_name}")
                name = clean_name
            
            return name
    
    def _populate_builder_from_config(self, builder: ConfigBuilder, config: ExperimentConfig):
        builder.with_seeds(config.seeds)
        builder.with_keywords(config.keywords)
        builder.with_api_provider(config.api_provider)
        builder.with_max_iterations(config.max_iterations)
        builder.with_papers_per_iteration(config.papers_per_iteration)
        builder.with_num_topics(config.num_topics)
        builder.with_topic_model(config.topic_model)
        builder.with_include_author_nodes(config.include_author_nodes)
        builder.with_enable_retraction_watch(config.enable_retraction_watch)
        builder.with_ignored_venues(config.ignored_venues)
        builder.with_save_figures(config.save_figures)
        builder.with_language(config.language)
        builder.with_root_folder(config.root_folder)
    
    def _show_edit_menu(self) -> int:
        self.console.print("\n" + "=" * 70)
        self.console.print(Panel("[bold cyan]EDIT MENU[/bold cyan]", expand=False))
        
        return self.prompter.choice(
            "What would you like to modify?",
            choices=[
                "API provider",
                "Seed papers",
                "Keywords",
                "Basic configuration",
                "Advanced configuration",
                "Save and run",
                "Cancel"
            ],
            default=0
        ) + 1
    
    def _edit_api_provider(self, builder: ConfigBuilder, wizard_cmd: WizardCommand):
        self.console.print("\n[bold]Current API provider:[/bold]", builder._config.get('api_provider', 'Not set'))
        api_provider = wizard_cmd._get_api_provider()
        builder.with_api_provider(api_provider)
    
    def _edit_seeds(self, builder: ConfigBuilder, wizard_cmd: WizardCommand):
        current_seeds = builder._config.get('seeds', [])
        
        self.console.print(f"\n[bold]Current seeds:[/bold] {len(current_seeds)} papers")
        
        action = self.prompter.choice(
            "What would you like to do?",
            choices=[
                "Add more seed papers",
                "Remove seed papers",
                "Replace all seed papers",
                "Keep current seeds"
            ],
            default=0
        )
        
        if action == 0:
            api_provider = builder._config.get('api_provider', 'openalex')
            new_seeds = wizard_cmd._get_seed_papers(api_provider)
            all_seeds = list(set(current_seeds + new_seeds))
            builder.with_seeds(all_seeds)
            self.console.print(f"[green]✓[/green] Total seeds: {len(all_seeds)}\n")
            
        elif action == 1:
            if not current_seeds:
                self.console.print("[yellow]No seeds to remove[/yellow]\n")
                return
            
            seeds_to_remove = self.prompter.checkbox(
                "Select seeds to remove",
                choices=current_seeds
            )
            
            remaining_seeds = [s for s in current_seeds if s not in seeds_to_remove]
            
            if not remaining_seeds:
                self.console.print("[yellow]⚠️  You must have at least one seed paper[/yellow]")
                return
            
            builder.with_seeds(remaining_seeds)
            self.console.print(f"[green]✓[/green] Removed {len(seeds_to_remove)} seeds. Remaining: {len(remaining_seeds)}\n")

        elif action == 2:
            api_provider = builder._config.get('api_provider', 'openalex')
            new_seeds = wizard_cmd._get_seed_papers(api_provider)
            builder.with_seeds(new_seeds)
            self.console.print(f"[green]✓[/green] Replaced with {len(new_seeds)} new seeds\n")
    
    def _edit_keywords(self, builder: ConfigBuilder):
        current_keywords = builder._config.get('keywords', [])
        
        self.console.print(f"\n[bold]Current keywords:[/bold] {len(current_keywords)} filters")
        if current_keywords:
            for kw in current_keywords:
                self.console.print(f"  - {kw}")
        
        action = self.prompter.choice(
            "\nWhat would you like to do?",
            choices=[
                "Add more keywords",
                "Remove keywords",
                "Replace all keywords",
                "Keep current keywords"
            ],
            default=0
        )
        
        if action == 0:
            self.console.print("\nEnter additional keywords (one per line, blank line when done):")
            new_keywords = []
            idx = len(current_keywords) + 1
            
            while True:
                keyword = self.prompter.input(f"Keyword {idx}").strip()
                if not keyword:
                    break
                new_keywords.append(keyword)
                idx += 1
            
            all_keywords = current_keywords + new_keywords
            builder.with_keywords(all_keywords)
            self.console.print(f"[green]✓[/green] Total keywords: {len(all_keywords)}\n")
            
        elif action == 1:
            if not current_keywords:
                self.console.print("[yellow]No keywords to remove[/yellow]\n")
                return
            
            keywords_to_remove = self.prompter.checkbox(
                "Select keywords to remove",
                choices=current_keywords
            )
            
            remaining_keywords = [k for k in current_keywords if k not in keywords_to_remove]
            builder.with_keywords(remaining_keywords)
            self.console.print(f"[green]✓[/green] Removed {len(keywords_to_remove)} keywords. Remaining: {len(remaining_keywords)}\n")
            
        elif action == 2:
            self.console.print("\nEnter new keywords (one per line, blank line when done):")
            new_keywords = []
            idx = 1
            
            while True:
                keyword = self.prompter.input(f"Keyword {idx}").strip()
                if not keyword:
                    break
                new_keywords.append(keyword)
                idx += 1
            
            builder.with_keywords(new_keywords)
            self.console.print(f"[green]✓[/green] Replaced with {len(new_keywords)} new keywords\n")
    
    def _edit_basic_config(self, builder: ConfigBuilder, wizard_cmd: WizardCommand):
        current_max_iter = builder._config.get('max_iterations', 1)
        current_papers = builder._config.get('papers_per_iteration', 1)
        
        self.console.print(f"\n[bold]Current basic configuration:[/bold]")
        self.console.print(f"  Max iterations: {current_max_iter}")
        self.console.print(f"  Papers per iteration: {current_papers}")
        
        if self.prompter.confirm("\nEdit basic configuration?", default=True):
            wizard_cmd._get_basic_config()
    
    def _edit_advanced_config(self, builder: ConfigBuilder, wizard_cmd: WizardCommand):
        current_topic_model = builder._config.get('topic_model', 'NMF')
        current_num_topics = builder._config.get('num_topics', 20)
        current_author_nodes = builder._config.get('include_author_nodes', False)
        current_language = builder._config.get('language', 'en')
        
        self.console.print(f"\n[bold]Current advanced configuration:[/bold]")
        self.console.print(f"  Topic model: {current_topic_model}")
        self.console.print(f"  Number of topics: {current_num_topics}")
        self.console.print(f"  Author nodes: {current_author_nodes}")
        self.console.print(f"  Language: {current_language}")
        
        if self.prompter.confirm("\nEdit advanced configuration?", default=True):
            wizard_cmd._get_advanced_config()
    
    def _review_and_confirm(self, config: ExperimentConfig) -> bool:
        self.console.print("\n" + "=" * 70)
        self.console.print(Panel("[bold cyan]REVIEW NEW CONFIGURATION[/bold cyan]", expand=False))
        
        self.console.print(f"\n[cyan]Experiment:[/cyan] {config.name}")
        self.console.print(f"[cyan]Seed papers:[/cyan] {len(config.seeds)}")
        self.console.print(f"[cyan]Keywords:[/cyan] {len(config.keywords)} filters")
        self.console.print(f"[cyan]Papers/iteration:[/cyan] {config.papers_per_iteration}")
        self.console.print(f"[cyan]Max iterations:[/cyan] {config.max_iterations}")
        self.console.print(f"[cyan]API:[/cyan] {config.api_provider}")
        self.console.print(f"[cyan]Language:[/cyan] {config.language}")
        self.console.print(f"[cyan]Topic model:[/cyan] {config.topic_model} ({config.num_topics} topics)")
        
        return self.prompter.confirm("\nSave configuration and start crawling?", default=True)