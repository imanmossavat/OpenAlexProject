

import yaml
from pathlib import Path
from typing import Optional
import logging

from .models import PaperData
from ..normalization import normalize_venue


class PaperFileReader:
    """
    Reads paper markdown files and parses them into PaperData objects.
    
    Responsibilities:
    - Read markdown files with YAML frontmatter
    - Parse frontmatter into PaperData
    - Handle file I/O errors gracefully
    
    Does NOT:
    - Create markdown files (that's MarkdownFileGenerator's job)
    - Validate paper data (that's PaperData's job)
    - Organize files into folders (that's LibraryManager's job)
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize paper file reader.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def read_paper_from_markdown(self, file_path: Path) -> Optional[PaperData]:
        """
        Read paper markdown file and parse into PaperData.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            PaperData object or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                self.logger.warning(f"No YAML frontmatter found in {file_path}")
                return None
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                self.logger.warning(f"Invalid frontmatter format in {file_path}")
                return None
            
            frontmatter_text = parts[1]
            body_text = parts[2]
            
            metadata = yaml.safe_load(frontmatter_text)
            
            if not metadata:
                self.logger.warning(f"Empty frontmatter in {file_path}")
                return None
            
            return self._metadata_to_paper_data(metadata, body_text)
            
        except Exception as e:
            self.logger.error(f"Failed to read paper from {file_path}: {e}")
            return None
    
    def _metadata_to_paper_data(self, metadata: dict, body: str = "") -> PaperData:
        """
        Convert YAML metadata dictionary to PaperData object.
        
        Args:
            metadata: Parsed YAML frontmatter
            
        Returns:
            PaperData object
        """
        paper_id = metadata.get('paper_id', '')
        title = metadata.get('title', '')
        authors = metadata.get('authors', [])
        
        year = metadata.get('year')
        venue = metadata.get('venue')
        venue_raw = metadata.get('venue_raw', venue)
        normalized_venue = normalize_venue(venue_raw)
        doi = metadata.get('doi')
        abstract = metadata.get('abstract')
        url = metadata.get('url')
        
        concepts = metadata.get('concepts', [])
        topics = metadata.get('topics', [])
        subfields = metadata.get('subfields', [])
        fields = metadata.get('fields', [])
        domains = metadata.get('domains', [])
        
        assigned_topic = metadata.get('assigned_topic')
        topic_label = metadata.get('topic_label')
        
        return PaperData(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            venue=normalized_venue or venue,
            venue_raw=venue_raw,
            doi=doi,
            abstract=abstract,
            url=url,
            concepts=concepts,
            topics=topics,
            subfields=subfields,
            fields=fields,
            domains=domains,
            assigned_topic=assigned_topic,
            topic_label=topic_label
        )
    
    def read_papers_from_directory(self, directory_path: Path) -> list[PaperData]:
        """
        Read all paper markdown files from a directory.
        
        Args:
            directory_path: Path to directory containing markdown files
            
        Returns:
            List of PaperData objects (skips files that fail to parse)
        """
        papers = []
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            self.logger.error(f"Directory does not exist: {directory_path}")
            return papers
        
        markdown_files = list(directory_path.glob("*.md"))
        self.logger.info(f"Found {len(markdown_files)} markdown files in {directory_path}")
        
        for file_path in markdown_files:
            paper_data = self.read_paper_from_markdown(file_path)
            if paper_data:
                papers.append(paper_data)
        
        self.logger.info(f"Successfully parsed {len(papers)} papers from {directory_path}")
        return papers
