"""
Extracts and structures metadata from Zotero items.
Single Responsibility: Metadata extraction and structuring.
"""

from typing import Dict, Optional
import re


class ZoteroMetadataExtractor:
    """Extracts structured metadata from Zotero item data."""
    
    @staticmethod
    def extract(item: Dict) -> Dict:
        """
        Extract structured metadata from a Zotero item.
        
        Args:
            item: Zotero item dictionary
            
        Returns:
            Dictionary with structured metadata
        """
        data = item.get('data', {})
        
        creators = data.get('creators', [])
        authors = []
        for creator in creators:
            if creator.get('creatorType') == 'author':
                first = creator.get('firstName', '').strip()
                last = creator.get('lastName', '').strip()
                if first and last:
                    authors.append(f"{first} {last}")
                elif last:
                    authors.append(last)
        
        tags = [t['tag'] for t in data.get('tags', [])]
        
        date_str = data.get('date', '')
        
        metadata = {
            'title': data.get('title', 'Untitled'),
            'authors': authors,
            'date': date_str,
            'year': ZoteroMetadataExtractor._extract_year(date_str),
            'publication': data.get('publicationTitle', ''),
            'doi': data.get('DOI', ''),
            'url': data.get('url', ''),
            'abstract': data.get('abstractNote', ''),
            'tags': tags,
            'item_type': data.get('itemType', ''),
            'zotero_key': data.get('key', '')
        }
        
        return metadata
    
    @staticmethod
    def _extract_year(date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None
        
        match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if match:
            return int(match.group())
        
        return None