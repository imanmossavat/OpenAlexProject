from pathlib import Path
from typing import List
import os
from dotenv import load_dotenv
import pyalex
from rich.console import Console
from ...pdf_processing import PDFProcessor, APIMetadataMatcher, PDFMetadata, APIMatchResult
from .pdf_ui_helpers import PDFFileSelector, MetadataReviewer, MatchResultsPresenter
from .prompts import Prompter


class PDFSeedWorkflow:
    
    def __init__(self, 
                 prompter: Prompter,
                 api_provider_type: str,
                 pdf_processor: PDFProcessor,
                 file_selector: PDFFileSelector,
                 metadata_reviewer: MetadataReviewer,
                 results_presenter: MatchResultsPresenter):
        self.prompter = prompter
        self.api_provider_type = api_provider_type
        self.pdf_processor = pdf_processor
        self.file_selector = file_selector
        self.metadata_reviewer = metadata_reviewer
        self.results_presenter = results_presenter
        self.console = Console()
    
    def execute(self) -> List[str]:
        self.console.print("\n[bold cyan]PDF Processing Workflow[/bold cyan]\n")
        
        pdf_paths = self.file_selector.select_files()
        if not pdf_paths:
            return []
        
        processing_results = self._process_pdfs(pdf_paths)
        
        valid_metadata = self.metadata_reviewer.review_and_edit(processing_results)
        if not valid_metadata:
            return []
        
        match_results = self._match_with_api(valid_metadata)
        
        paper_ids = self.results_presenter.show_and_confirm(match_results)
        
        return paper_ids
    
    def _process_pdfs(self, pdf_paths: List[Path]):
        self.console.print("[cyan]Processing PDFs with GROBID...[/cyan]")
        
        with self.console.status("[bold cyan]Extracting metadata from PDFs..."):
            results = self.pdf_processor.process_pdfs(pdf_paths)
        
        success_count = sum(1 for r in results if r.success)
        self.console.print(f"[green]✓[/green] Processed {success_count}/{len(results)} files successfully\n")
        
        return results
    
    def _match_with_api(self, metadata_list: List[PDFMetadata]) -> List[APIMatchResult]:
        self.console.print("\n[bold cyan]Matching with API[/bold cyan]\n")
        self.console.print(f"Using API: [green]{self.api_provider_type}[/green]\n")
        
        if self.api_provider_type == 'openalex':
            self._configure_openalex()
        
        from ArticleCrawler.api import create_api_provider
        api_provider = create_api_provider(self.api_provider_type)
        
        matcher = APIMetadataMatcher(api_provider, logger=self.pdf_processor.logger)
        
        self.console.print(f"[dim]Matching {len(metadata_list)} papers (with rate limiting)...[/dim]")
        
        with self.console.status("[bold cyan]Searching API for papers..."):
            match_results = matcher.match_metadata(metadata_list)
        
        matched_count = sum(1 for r in match_results if r.matched)
        self.console.print(f"[green]✓[/green] Matched {matched_count}/{len(metadata_list)} papers\n")
        
        return match_results
    
    def _configure_openalex(self):
        load_dotenv()
        email = os.getenv('OPENALEX_EMAIL')
        
        if email:
            pyalex.config.email = email
            self.console.print(f"[dim]Using polite pool with email: {email}[/dim]")
        else:
            self.console.print("[yellow]⚠ No OPENALEX_EMAIL set - using slower rate limits[/yellow]")
            self.console.print("[dim]Add your email to .env file for faster access:[/dim]")
            self.console.print("[dim]OPENALEX_EMAIL=your.email@example.com[/dim]\n")