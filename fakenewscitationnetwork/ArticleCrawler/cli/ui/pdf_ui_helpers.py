from pathlib import Path
from typing import List, Optional
from tkinter import filedialog
import tkinter as tk
from rich.console import Console
from rich.table import Table
from .prompts import Prompter
from ...pdf_processing import PDFMetadata, PDFProcessingResult, APIMatchResult


class PDFFileSelector:
    
    def __init__(self, console: Console):
        self.console = console
    
    def select_files(self) -> List[Path]:
        self.console.print("Opening file dialog to select PDF files...")
        self.console.print("[dim]Please select PDF files in the dialog window that will appear...[/dim]\n")
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        
        try:
            file_paths = filedialog.askopenfilenames(
                title="Select PDF files",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                parent=root
            )
        finally:
            root.destroy()
        
        if not file_paths:
            return []
        
        pdf_paths = [Path(p) for p in file_paths]
        self.console.print(f"[green]✓[/green] Selected {len(pdf_paths)} PDF file(s)\n")
        return pdf_paths


class MetadataReviewer:
    
    def __init__(self, prompter: Prompter, console: Console):
        self.prompter = prompter
        self.console = console
    
    def review_and_edit(self, processing_results: List[PDFProcessingResult]) -> List[PDFMetadata]:
        self.console.print("\n[bold cyan]Review Extracted Metadata[/bold cyan]\n")
        
        valid_metadata = []
        
        for i, result in enumerate(processing_results, 1):
            self.console.print(f"\n[bold]File {i}/{len(processing_results)}:[/bold]")
            
            if not result.success:
                self.console.print(f"[red]✗ Failed:[/red] {result.error_message}")
                
                if self.prompter.confirm("Enter metadata manually?", default=False):
                    metadata = self._manual_entry(result.pdf_path.name)
                    if metadata:
                        valid_metadata.append(metadata)
                continue
            
            self._display_metadata(result.metadata)
            
            action = self.prompter.choice("Action", choices=["Accept", "Edit", "Skip"], default=0)
            
            if action == 0:
                valid_metadata.append(result.metadata)
            elif action == 1:
                edited = self._edit_metadata(result.metadata)
                if edited:
                    valid_metadata.append(edited)
        
        self.console.print(f"\n[green]✓[/green] {len(valid_metadata)} papers ready for API matching\n")
        return valid_metadata
    
    def _display_metadata(self, metadata: PDFMetadata):
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Title", metadata.title or "[dim]Not found[/dim]")
        table.add_row("Authors", metadata.authors or "[dim]Not found[/dim]")
        table.add_row("Venue", metadata.venue or "[dim]Not found[/dim]")
        table.add_row("Year", metadata.year or "[dim]Not found[/dim]")
        table.add_row("DOI", metadata.doi or "[dim]Not found[/dim]")
        
        self.console.print(table)
    
    def _edit_metadata(self, metadata: PDFMetadata) -> Optional[PDFMetadata]:
        self.console.print("\n[cyan]Edit metadata (press Enter to keep current value):[/cyan]")
        
        title = self.prompter.input("Title", default=metadata.title or "")
        if not title:
            self.prompter.error("Title is required")
            return None
        
        authors = self.prompter.input("Authors", default=metadata.authors or "")
        venue = self.prompter.input("Venue", default=metadata.venue or "")
        year = self.prompter.input("Year", default=metadata.year or "")
        doi = self.prompter.input("DOI", default=metadata.doi or "")
        
        return PDFMetadata(
            filename=metadata.filename,
            title=title,
            authors=authors if authors else None,
            venue=venue if venue else None,
            year=year if year else None,
            doi=doi if doi else None
        )
    
    def _manual_entry(self, filename: str) -> Optional[PDFMetadata]:
        self.console.print(f"\n[cyan]Manual entry for {filename}:[/cyan]")
        
        title = self.prompter.input("Title")
        if not title:
            return None
        
        authors = self.prompter.input("Authors (optional)", default="")
        venue = self.prompter.input("Venue (optional)", default="")
        year = self.prompter.input("Year (optional)", default="")
        doi = self.prompter.input("DOI (optional)", default="")
        
        return PDFMetadata(
            filename=filename,
            title=title,
            authors=authors if authors else None,
            venue=venue if venue else None,
            year=year if year else None,
            doi=doi if doi else None
        )


class MatchResultsPresenter:
    
    def __init__(self, prompter: Prompter, console: Console, api_provider_type: str):
        self.prompter = prompter
        self.console = console
        self.api_provider_type = api_provider_type
    
    def show_and_confirm(self, match_results: List[APIMatchResult]) -> List[str]:
        self.console.print("\n[bold cyan]API Match Results[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("File", style="white", no_wrap=True)
        table.add_column("Status", style="cyan")
        table.add_column("Paper ID", style="green")
        table.add_column("Confidence", style="yellow", justify="right")
        table.add_column("Method", style="dim")
        
        paper_ids = []
        
        for result in match_results:
            if result.matched:
                status = "✓ Matched"
                paper_id = result.paper_id
                confidence = f"{result.confidence:.0%}"
                method = result.match_method
                paper_ids.append(result.paper_id)
            else:
                status = "✗ Not found"
                paper_id = "-"
                confidence = "-"
                method = "-"
            
            filename = result.metadata.filename[:30] + "..." if len(result.metadata.filename) > 30 else result.metadata.filename
            table.add_row(filename, status, paper_id, confidence, method)
        
        self.console.print(table)
        
        if not paper_ids:
            self.prompter.error("No papers were matched with the API")
            self.console.print("\n[yellow]This could be due to:[/yellow]")
            self.console.print("  • Rate limiting (429 errors) - try again in a few minutes")
            self.console.print("  • Papers not indexed in the API")
            self.console.print("  • Incorrect metadata extraction")
            return []
        
        self.console.print(f"\n[green]Found {len(paper_ids)} paper(s) in {self.api_provider_type}[/green]")
        
        not_found_count = len(match_results) - len(paper_ids)
        if not_found_count > 0:
            self.console.print(f"[yellow]⚠ {not_found_count} paper(s) not found in API[/yellow]")
            self.console.print("[dim]Note: Some may be due to rate limiting - you can try again[/dim]")
        
        if self.prompter.confirm("\nUse these matched papers as seeds?", default=True):
            return paper_ids
        
        return []