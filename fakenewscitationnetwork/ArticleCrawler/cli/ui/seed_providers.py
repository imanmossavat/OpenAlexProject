from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from rich.console import Console
from .prompts import Prompter
from .validators import validate_paper_id, validate_file_path
from .pdf_ui_helpers import PDFFileSelector, MetadataReviewer, MatchResultsPresenter
from .pdf_workflow import PDFSeedWorkflow
from ...pdf_processing import PDFProcessor


class SeedProvider(ABC):
    
    @abstractmethod
    def get_seeds(self) -> List[str]:
        pass
    
    @abstractmethod
    def display_name(self) -> str:
        pass


class ManualSeedProvider(SeedProvider):
    
    def __init__(self, prompter: Prompter):
        self.prompter = prompter
    
    def display_name(self) -> str:
        return "Enter paper IDs manually"
    
    def get_seeds(self) -> List[str]:
        seeds = []
        self.prompter.console.print("Enter paper IDs (one per line, blank to finish):")
        self.prompter.console.print("[dim]Formats accepted: W123456789 (OpenAlex), DOIs, S2 IDs[/dim]\n")
        
        idx = 1
        while True:
            seed = self.prompter.input(f"Paper ID {idx}").strip()
            
            if not seed:
                break
            
            if validate_paper_id(seed):
                seeds.append(seed)
                idx += 1
            else:
                self.prompter.error(f"Invalid paper ID format: {seed}")
                self.prompter.console.print("[dim]Try: W123456789, DOI, or S2 paper ID[/dim]")
        
        return seeds


class FileSeedProvider(SeedProvider):
    
    def __init__(self, prompter: Prompter):
        self.prompter = prompter
    
    def display_name(self) -> str:
        return "Load from file"
    
    def get_seeds(self) -> List[str]:
        while True:
            path_str = self.prompter.input("Enter path to seed papers file")
            
            is_valid, error_msg = validate_file_path(path_str)
            if not is_valid:
                self.prompter.error(error_msg)
                continue
            
            try:
                seeds = self._load_from_file(Path(path_str))
                if not seeds:
                    self.prompter.error("File is empty or contains no valid paper IDs")
                    continue
                
                return seeds
                
            except Exception as e:
                self.prompter.error(f"Error reading file: {e}")
                continue
    
    def _load_from_file(self, file_path: Path) -> List[str]:
        seeds = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if validate_paper_id(line):
                    seeds.append(line)
                else:
                    self.prompter.warning(f"Line {line_num}: Invalid paper ID format: {line}")
        
        return seeds


class PDFSeedProvider(SeedProvider):
    
    def __init__(self, prompter: Prompter, api_provider_type: str = 'openalex'):
        self.prompter = prompter
        self.api_provider_type = api_provider_type
        console = Console()
        
        file_selector = PDFFileSelector(console)
        metadata_reviewer = MetadataReviewer(prompter, console)
        results_presenter = MatchResultsPresenter(prompter, console, api_provider_type)
        pdf_processor = PDFProcessor()
        
        self.workflow = PDFSeedWorkflow(
            prompter=prompter,
            api_provider_type=api_provider_type,
            pdf_processor=pdf_processor,
            file_selector=file_selector,
            metadata_reviewer=metadata_reviewer,
            results_presenter=results_presenter
        )
    
    def display_name(self) -> str:
        return "Extract from PDF files"
    
    def get_seeds(self) -> List[str]:
        return self.workflow.execute()


SEED_PROVIDERS = [
    ManualSeedProvider,
    FileSeedProvider,
    PDFSeedProvider,
]