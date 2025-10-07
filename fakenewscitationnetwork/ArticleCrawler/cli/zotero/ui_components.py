"""
UI components for Zotero seed selection.
Single Responsibility: User interface and interaction.
"""

from typing import List, Optional, Dict
from rich.console import Console
from ..ui.prompts import Prompter


class ZoteroCollectionSelector:
    """Handles collection selection UI."""
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def select(self, collections: List[Dict]) -> Optional[Dict]:
        """
        Display collections and let user select one.
        
        Returns:
            Selected collection or None if cancelled
        """
        self.console.print("📚 [bold]Your Zotero Collections:[/bold]\n")
        
        for i, col in enumerate(collections, start=1):
            self.console.print(f"{i}. {col['name']}")
        
        self.console.print()
        
        while True:
            choice = self.prompter.input("Select collection number").strip()
            
            if not choice.isdigit():
                self.prompter.error("Please enter a number")
                continue
            
            choice_num = int(choice)
            if choice_num < 1 or choice_num > len(collections):
                self.prompter.error(f"Please enter a number between 1 and {len(collections)}")
                continue
            
            selected = collections[choice_num - 1]
            self.console.print(f"\n[green]✓[/green] Selected: {selected['name']}\n")
            return selected


class SelectionModeChooser:
    """Handles selection mode choice UI."""
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def choose(self) -> str:
        """
        Ask user if they want all papers or individual selection.
        
        Returns:
            'all' or 'individual'
        """
        self.console.print("[bold]Selection Mode:[/bold]")
        self.console.print("1. Use all papers from collection")
        self.console.print("2. Choose papers individually\n")
        
        while True:
            choice = self.prompter.input("Select mode").strip()
            
            if choice == '1':
                return 'all'
            elif choice == '2':
                return 'individual'
            else:
                self.prompter.error("Please enter 1 or 2")


class PaperSelector:
    """Handles individual paper selection UI."""
    
    def __init__(self, prompter: Prompter, console: Console, formatter):
        self.prompter = prompter
        self.console = console
        self.formatter = formatter
    
    def select(self, items_metadata: List[Dict]) -> List[Dict]:
        """
        Display papers and let user select which to use.
        
        Returns:
            List of selected metadata dictionaries
        """
        self.console.print("\n[bold cyan]Papers in Collection:[/bold cyan]\n")
        
        # Display all papers
        for i, metadata in enumerate(items_metadata, start=1):
            self.console.print(f"\n[bold]{i}.[/bold]")
            formatted = self.formatter.format_collection_preview(metadata)
            self.console.print(formatted)
        
        self.console.print("\n" + "=" * 60)
        self.console.print("\n[bold]Enter paper numbers (e.g., 1 3 5-7 10)[/bold]")
        self.console.print("[dim]Or press Enter to cancel[/dim]\n")
        
        while True:
            selection = self.prompter.input("Paper numbers").strip()
            
            if not selection:
                return []
            
            try:
                indices = self._parse_selection(selection, len(items_metadata))
                if indices:
                    selected = [items_metadata[i] for i in indices]
                    self.console.print(f"\n[green]✓[/green] Selected {len(selected)} papers\n")
                    return selected
                else:
                    self.prompter.error("No valid papers selected")
            except ValueError as e:
                self.prompter.error(str(e))
    
    def _parse_selection(self, selection: str, max_index: int) -> List[int]:
        """Parse selection string like '1 3 5-7' into indices."""
        indices = set()
        
        parts = selection.split()
        for part in parts:
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start_idx = int(start) - 1
                    end_idx = int(end) - 1
                    
                    if start_idx < 0 or end_idx >= max_index or start_idx > end_idx:
                        raise ValueError(f"Invalid range: {part}")
                    
                    indices.update(range(start_idx, end_idx + 1))
                except ValueError:
                    raise ValueError(f"Invalid range format: {part}")
            else:
                try:
                    idx = int(part) - 1
                    if idx < 0 or idx >= max_index:
                        raise ValueError(f"Number out of range: {part}")
                    indices.add(idx)
                except ValueError:
                    raise ValueError(f"Invalid number: {part}")
        
        return sorted(list(indices))


class MatchReviewer:
    """Handles manual review of match candidates."""
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def review(self, match_result) -> Optional[str]:
        """
        Show candidates and let user choose.
        
        Returns:
            Selected paper ID or None
        """
        self.console.print(f"\n[bold cyan]Your paper:[/bold cyan]")
        self.console.print(f"  {match_result.title}\n")
        
        self.console.print(f"[bold]Found {len(match_result.candidates)} possible matches:[/bold]\n")
        
        # Display candidates
        for i, candidate in enumerate(match_result.candidates, 1):
            similarity_pct = candidate.similarity * 100
            
            # Color code by similarity
            if candidate.similarity >= 0.85:
                color = "green"
            elif candidate.similarity >= 0.75:
                color = "yellow"
            else:
                color = "red"
            
            self.console.print(f"{i}. [{color}]Similarity: {similarity_pct:.1f}%[/{color}]")
            self.console.print(f"   Title: {candidate.title}")
            
            if candidate.year:
                self.console.print(f"   Year: {candidate.year}")
            if candidate.venue:
                self.console.print(f"   Venue: {candidate.venue}")
            if candidate.doi:
                self.console.print(f"   DOI: {candidate.doi}")
            
            self.console.print(f"   ID: {candidate.paper_id}")
            self.console.print()
        
        # Ask user to select
        self.console.print("[bold]Options:[/bold]")
        self.console.print(f"  Enter number (1-{len(match_result.candidates)}) to select")
        self.console.print("  Press Enter to skip\n")
        
        while True:
            choice = self.prompter.input("Your choice").strip()
            
            if not choice:
                self.console.print("[yellow]Skipped[/yellow]\n")
                return None
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(match_result.candidates):
                    selected = match_result.candidates[choice_num - 1]
                    self.console.print(f"[green]✓ Selected: {selected.title[:60]}...[/green]\n")
                    return selected.paper_id
            
            self.prompter.error(f"Please enter 1-{len(match_result.candidates)} or press Enter")


class MatchResultsPresenter:
    """Presents matching results to the user."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def present(self, results: List, reviewer: MatchReviewer) -> List[str]:
        """
        Display results and collect confirmed paper IDs.
        
        Returns:
            List of confirmed paper IDs
        """
        self.console.print("\n[bold]Matching Results:[/bold]\n")
        
        # Separate results
        auto_matched = [r for r in results if r.matched]
        needs_review = [r for r in results if not r.matched and r.candidates]
        failed = [r for r in results if not r.matched and not r.candidates]
        
        paper_ids = []
        
        # Show automatic matches
        if auto_matched:
            self.console.print(f"[green]✓ Automatically matched {len(auto_matched)} papers:[/green]")
            for r in auto_matched:
                self.console.print(f"  • {r.title[:60]}... -> {r.paper_id}")
                paper_ids.append(r.paper_id)
            self.console.print()
        
        # Handle manual review
        if needs_review:
            self.console.print(f"[yellow]⚠ {len(needs_review)} papers need manual review:[/yellow]\n")
            
            for r in needs_review:
                reviewed_id = reviewer.review(r)
                if reviewed_id:
                    paper_ids.append(reviewed_id)
        
        # Show failures
        if failed:
            self.console.print(f"\n[red]✗ Could not find matches for {len(failed)} papers:[/red]")
            for r in failed:
                error_msg = r.error or "Unknown error"
                self.console.print(f"  • {r.title[:60]}... ({error_msg})")
        
        self.console.print()
        return paper_ids