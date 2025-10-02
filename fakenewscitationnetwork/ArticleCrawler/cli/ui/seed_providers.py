"""
Pluggable seed paper providers.

Uses Strategy pattern to allow different methods of obtaining seed papers.
New providers can be added by creating a new class and adding it to SEED_PROVIDERS.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from .prompts import Prompter
from .validators import validate_paper_id, validate_file_path


class SeedProvider(ABC):
    """
    Abstract base for seed paper sources.
    
    Implement this interface to add new ways of providing seed papers.
    """
    
    @abstractmethod
    def get_seeds(self) -> List[str]:
        """
        Get list of seed paper IDs.
        
        Returns:
            List of paper ID strings
        """
        pass
    
    @abstractmethod
    def display_name(self) -> str:
        """
        Get human-readable name for this provider.
        
        Returns:
            Display name string
        """
        pass


class ManualSeedProvider(SeedProvider):
    """Manually enter paper IDs one by one."""
    
    def __init__(self, prompter: Prompter):
        self.prompter = prompter
    
    def display_name(self) -> str:
        return "Enter paper IDs manually"
    
    def get_seeds(self) -> List[str]:
        """Get seeds through manual entry."""
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
    """Load seeds from a text file."""
    
    def __init__(self, prompter: Prompter):
        self.prompter = prompter
    
    def display_name(self) -> str:
        return "Load from file"
    
    def get_seeds(self) -> List[str]:
        """Load seeds from file."""
        while True:
            path_str = self.prompter.input("Enter path to seed papers file")
            
            # Validate path
            is_valid, error_msg = validate_file_path(path_str)
            if not is_valid:
                self.prompter.error(error_msg)
                continue
            
            # Try to load file
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
        """
        Load paper IDs from file.
        
        Args:
            file_path: Path to file containing paper IDs
            
        Returns:
            List of valid paper IDs
        """
        seeds = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Validate paper ID
                if validate_paper_id(line):
                    seeds.append(line)
                else:
                    self.prompter.warning(f"Line {line_num}: Invalid paper ID format: {line}")
        
        return seeds


class DOISeedProvider(SeedProvider):
    """
    Search by DOI (future implementation).
    
    This is a placeholder for future functionality.
    """
    
    def __init__(self, prompter: Prompter):
        self.prompter = prompter
    
    def display_name(self) -> str:
        return "Search by DOI/title (coming soon)"
    
    def get_seeds(self) -> List[str]:
        """Not yet implemented."""
        raise NotImplementedError("DOI search feature coming soon!")


# Registry of available seed providers
SEED_PROVIDERS = [
    ManualSeedProvider,
    FileSeedProvider,
    DOISeedProvider,
]