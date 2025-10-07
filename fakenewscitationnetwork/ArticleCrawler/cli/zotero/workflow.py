"""
Zotero seed workflow orchestration.
Single Responsibility: Orchestrate the complete workflow.
"""

from typing import List, Dict
from rich.console import Console
from ...api.zotero.client import ZoteroClient
from ...api.zotero.metadata_extractor import ZoteroMetadataExtractor
from ...api.zotero.matching.matcher import ZoteroMatcher
from ...api.zotero.formatting import ZoteroItemFormatter
from ..ui.prompts import Prompter
from ...api import create_api_provider
from ArticleCrawler.cli.zotero.ui_components import (
    ZoteroCollectionSelector,
    SelectionModeChooser,
    PaperSelector,
    MatchReviewer,
    MatchResultsPresenter
)


class ZoteroSeedWorkflow:
    """
    Orchestrates the Zotero seed selection workflow.
    Single Responsibility: Coordinate all components in the workflow.
    """
    
    def __init__(
        self,
        prompter: Prompter,
        console: Console,
        api_provider_type: str
    ):
        """
        Initialize workflow with dependencies.
        
        Args:
            prompter: Prompter for user input
            console: Console for output
            api_provider_type: API provider to use for matching
        """
        self.prompter = prompter
        self.console = console
        self.api_provider_type = api_provider_type
        
        try:
            self.client = ZoteroClient()
        except ValueError as e:
            self.prompter.error(str(e))
            raise
        
        self.metadata_extractor = ZoteroMetadataExtractor()
        self.formatter = ZoteroItemFormatter()
        
        self.collection_selector = ZoteroCollectionSelector(prompter, console)
        self.mode_chooser = SelectionModeChooser(prompter, console)
        self.paper_selector = PaperSelector(prompter, console, self.formatter)
        self.match_reviewer = MatchReviewer(prompter, console)
        self.results_presenter = MatchResultsPresenter(console)
    
    def execute(self) -> List[str]:
        """
        Execute the complete workflow.
        
        Returns:
            List of paper IDs
        """
        self.console.print("\n[bold cyan]Zotero Library Import[/bold cyan]\n")
        
        collections = self._load_collections()
        if not collections:
            self.prompter.error("No collections found")
            return []
        
        selected_collection = self.collection_selector.select(collections)
        if not selected_collection:
            return []
        
        items_metadata = self._load_items(selected_collection)
        if not items_metadata:
            self.prompter.error("No bibliographic items found")
            return []
        
        mode = self.mode_chooser.choose()
        
        if mode == 'all':
            selected_items = items_metadata
        else:
            selected_items = self.paper_selector.select(items_metadata)
        
        if not selected_items:
            return []
        
        paper_ids = self._match_papers(selected_items)
        
        return paper_ids
    
    def _load_collections(self) -> List[Dict]:
        """Load collections from Zotero."""
        try:
            with self.console.status("[bold cyan]Loading Zotero collections..."):
                collections = self.client.get_collections()
            return collections
        except Exception as e:
            self.prompter.error(f"Failed to load collections: {e}")
            return []
    
    def _load_items(self, collection: Dict) -> List[Dict]:
        """Load and extract metadata from collection items."""
        try:
            with self.console.status("[bold cyan]Loading papers from collection..."):
                items = self.client.get_collection_items(collection['key'])
                
                items_metadata = []
                for item in items:
                    metadata = self.metadata_extractor.extract(item)
                    items_metadata.append(metadata)
            
            self.console.print(f"[green]✓[/green] Loaded {len(items_metadata)} papers\n")
            return items_metadata
            
        except Exception as e:
            self.prompter.error(f"Failed to load items: {e}")
            return []
    
    def _match_papers(self, items_metadata: List[Dict]) -> List[str]:
        """Match papers to API paper IDs."""
        self.console.print("\n[bold cyan]Matching Papers to API[/bold cyan]\n")
        self.console.print(f"Using API: [green]{self.api_provider_type}[/green]\n")
        
        api_provider = create_api_provider(self.api_provider_type)
        matcher = ZoteroMatcher(api_provider)
        
        with self.console.status("[bold cyan]Searching API for papers..."):
            match_results = matcher.match_items(items_metadata)
        
        paper_ids = self.results_presenter.present(match_results, self.match_reviewer)
        
        if paper_ids:
            self.console.print(f"\n[green]✓[/green] Successfully matched {len(paper_ids)} papers\n")
        else:
            self.prompter.warning("No papers could be matched")
        
        return paper_ids