"""
Library Discovery Utility

Provides functions to find existing libraries in common locations.
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml
import logging


class LibraryDiscovery:
    """Discover existing libraries in the file system."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize library discovery.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def find_libraries(self, search_paths: Optional[List[Path]] = None) -> List[Dict[str, any]]:
        """
        Find all libraries in specified search paths.
        
        Args:
            search_paths: List of paths to search. If None, uses default locations.
            
        Returns:
            List of dictionaries containing library information:
            - name: Library name
            - path: Path to library
            - description: Library description (if available)
            - paper_count: Number of papers (if available)
        """
        if search_paths is None:
            search_paths = self._get_default_search_paths()
        
        libraries = []
        
        for search_path in search_paths:
            if not search_path.exists():
                self.logger.debug(f"Search path does not exist: {search_path}")
                continue
            
            self.logger.debug(f"Searching for libraries in: {search_path}")
            libraries.extend(self._scan_directory(search_path))
        
        return libraries
    
    def _get_default_search_paths(self) -> List[Path]:
        """
        Get default search paths for libraries.
        
        Returns:
            List of default paths to search
        """
        return [
            Path.cwd() / "libraries",
            Path.cwd() / "data" / "libraries",
            Path.home() / "libraries",
        ]
    
    def _scan_directory(self, directory: Path, max_depth: int = 3) -> List[Dict[str, any]]:
        """
        Recursively scan directory for libraries.
        
        Args:
            directory: Directory to scan
            max_depth: Maximum recursion depth
            
        Returns:
            List of found libraries
        """
        libraries = []
        
        try:
            config_path = directory / "library_config.yaml"
            if config_path.exists():
                library_info = self._extract_library_info(directory, config_path)
                if library_info:
                    libraries.append(library_info)
                    return libraries
            
            if max_depth > 0:
                for item in directory.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        libraries.extend(self._scan_directory(item, max_depth - 1))
        
        except PermissionError:
            self.logger.debug(f"Permission denied: {directory}")
        except Exception as e:
            self.logger.debug(f"Error scanning {directory}: {e}")
        
        return libraries
    
    def _extract_library_info(self, library_path: Path, config_path: Path) -> Optional[Dict[str, any]]:
        """
        Extract information from library config.
        
        Args:
            library_path: Path to library directory
            config_path: Path to config file
            
        Returns:
            Dictionary with library info or None if error
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            papers_dir = library_path / "papers"
            paper_count = len(list(papers_dir.glob("*.md"))) if papers_dir.exists() else 0
            
            topics_dir = library_path / "topics"
            if topics_dir.exists():
                self.logger.debug(f"Skipping library {library_path} - topics folder already exists")
                return None
            
            name = config.get('name', library_path.name)
            
            description = config.get('description')
            
            return {
                'name': name,
                'path': library_path,
                'description': description,
                'paper_count': paper_count,
                'created_at': config.get('created_at'),
                'api_provider': config.get('api_provider'),
            }
        
        except Exception as e:
            self.logger.warning(f"Failed to read library config at {config_path}: {e}")
            return None
    
    def format_library_choice(self, library_info: Dict[str, any]) -> str:
        """
        Format library info as a choice string.
        
        Args:
            library_info: Library information dictionary
            
        Returns:
            Formatted string for display
        """
        name = library_info['name']
        paper_count = library_info.get('paper_count', 0)
        description = library_info.get('description')
        
        result = f"{name} ({paper_count} paper{'s' if paper_count != 1 else ''})"
        
        if description and description.strip():
            desc_short = description[:50] + "..." if len(description) > 50 else description
            result += f" - {desc_short}"
        
        return result