"""
Library Discovery Utility

Provides functions to find existing libraries in common locations.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml


class LibraryDiscovery:
    """Discover existing libraries in the file system."""

    ENV_LIBRARY_ROOT = "ARTICLECRAWLER_LIBRARY_ROOT"

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        default_paths: Optional[Iterable[Path]] = None,
        env_key: str = ENV_LIBRARY_ROOT,
    ):
        """
        Initialize library discovery.

        Args:
            logger: Optional logger instance
            default_paths: Optional explicit search paths
            env_key: Environment variable for overriding search paths
        """
        self.logger = logger or logging.getLogger(__name__)
        self._configured_paths = self._normalize_paths(default_paths) if default_paths else None
        self._env_key = env_key
    
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
        configured = self._configured_paths or self._get_env_configured_paths()
        legacy_defaults = [
            Path.cwd() / "libraries",
            Path.cwd() / "data" / "libraries",
            Path.home() / "libraries",
        ]

        if configured:
            merged = configured + legacy_defaults
            unique: List[Path] = []
            seen = set()
            for path in merged:
                normalized = path.expanduser()
                key = normalized.resolve() if normalized.is_absolute() else normalized
                if key in seen:
                    continue
                seen.add(key)
                unique.append(normalized)
            return unique

        return legacy_defaults

    def _get_env_configured_paths(self) -> Optional[List[Path]]:
        """Return paths configured via environment variable when available."""
        raw_value = os.getenv(self._env_key)
        if not raw_value:
            return None
        parts = [segment.strip() for segment in raw_value.split(os.pathsep) if segment.strip()]
        if not parts:
            return None
        return self._normalize_paths(Path(part) for part in parts)

    @staticmethod
    def _normalize_paths(paths: Optional[Iterable[Path]]) -> List[Path]:
        """Normalize a collection of inputs into concrete Path objects."""
        if not paths:
            return []
        normalized: List[Path] = []
        for path in paths:
            if path is None:
                continue
            normalized.append(Path(path).expanduser())
        return normalized
    
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
