
import json
import yaml
from pathlib import Path
from typing import Optional, List
import logging

from .models import LibraryConfig


class LibraryManager:
    """
    Manages library directory structure and configuration.
    
    Responsibilities:
    - Create library folder structure
    - Save/load library configuration
    - Query library structure
    
    Does NOT:
    - Create markdown files (delegates to MarkdownFileGenerator)
    - Fetch paper metadata (delegates to API)
    - Run topic modeling (delegates to TopicModeling)
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize library manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def create_library_structure(self, library_path: Path, library_name: str) -> None:
        """
        Create library directory structure.
        
        Args:
            library_path: Path to library root
            library_name: Name of the library
        """
        library_path = Path(library_path)
        
        library_path.mkdir(parents=True, exist_ok=True)
        (library_path / "papers").mkdir(exist_ok=True)
        
        self.logger.info(f"Created library structure at {library_path}")
    
    def save_library_config(self, config: LibraryConfig) -> None:
        """
        Save library configuration to YAML file.
        
        Args:
            config: Library configuration to save
        """
        config_path = config.base_path / "library_config.yaml"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False)
        
        self.logger.info(f"Saved library configuration to {config_path}")
    
    def load_library_config(self, library_path: Path) -> LibraryConfig:
        """
        Load library configuration from YAML file.
        
        Args:
            library_path: Path to library root
            
        Returns:
            Library configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path(library_path) / "library_config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Library config not found at {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        config = LibraryConfig.from_dict(config_dict)
        self.logger.info(f"Loaded library configuration from {config_path}")
        
        return config
    
    def get_papers_directory(self, library_path: Path) -> Path:
        """Get path to papers directory."""
        return Path(library_path) / "papers"
    
    def get_topics_directory(self, library_path: Path) -> Path:
        """Get path to topics directory."""
        return Path(library_path) / "topics"
    
    def get_all_paper_files(self, library_path: Path) -> List[Path]:
        """
        Get all paper markdown files in library.
        
        Args:
            library_path: Path to library root
            
        Returns:
            List of paths to paper markdown files
        """
        papers_dir = self.get_papers_directory(library_path)
        return list(papers_dir.glob("*.md"))
    
    def library_exists(self, library_path: Path) -> bool:
        """
        Check if a library exists at given path.
        
        Args:
            library_path: Path to check
            
        Returns:
            True if library exists, False otherwise
        """
        config_path = Path(library_path) / "library_config.yaml"
        return config_path.exists()
    
    def create_topic_folder(self, library_path: Path, topic_label: str) -> Path:
        """
        Create a folder for a specific topic.
        
        Args:
            library_path: Path to library root
            topic_label: Label for the topic
            
        Returns:
            Path to created topic folder
        """
        topics_dir = self.get_topics_directory(library_path)
        
        safe_label = self._sanitize_folder_name(topic_label)
        topic_folder = topics_dir / safe_label
        topic_folder.mkdir(parents=True, exist_ok=True)
        
        return topic_folder
    
    def _sanitize_folder_name(self, name: str, max_length: int = 100) -> str:
        """
        Create safe folder name from label.
        
        Args:
            name: Original name
            max_length: Maximum length for folder name
            
        Returns:
            Sanitized folder name
        """
        safe = name.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in (' ', '-', '_', '&'))
        safe = safe.strip()
        
        if len(safe) > max_length:
            safe = safe[:max_length].strip()
        
        return safe
    
    @staticmethod
    def sanitize_filename(title: str, max_length: int = 50) -> str:
        """Create safe filename from title."""
        import re
        safe = re.sub(r'[^\w\s-]', '', title)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe[:max_length]