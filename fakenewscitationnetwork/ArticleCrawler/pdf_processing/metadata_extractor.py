
import xml.etree.ElementTree as ET
import re
from typing import Optional, Tuple
import logging
from .models import PDFMetadata


class PDFMetadataExtractor:
    
    NAMESPACES = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, xml_content: str, filename: str) -> Optional[PDFMetadata]:
        try:
            root = ET.fromstring(xml_content)
            
            title = self._extract_title(root)
            doi = self._extract_doi(root)
            year = self._extract_year(root)
            authors = self._extract_authors(root)
            venue = self._extract_venue(root)
            
            return PDFMetadata(
                filename=filename,
                title=title,
                doi=doi,
                year=year,
                authors=authors,
                venue=venue
            )
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error for {filename}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {filename}: {e}")
            return None
    
    def _extract_title(self, root: ET.Element) -> Optional[str]:
        title_elem = root.find('.//tei:titleStmt/tei:title', self.NAMESPACES)
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return None
    
    def _extract_doi(self, root: ET.Element) -> Optional[str]:
        idno_elements = root.findall('.//tei:idno', self.NAMESPACES)
        for idno in idno_elements:
            if idno.get('type') == 'DOI' and idno.text:
                return idno.text.strip()
        
        biblio_elements = root.findall('.//tei:biblStruct', self.NAMESPACES)
        for biblio in biblio_elements:
            idno_elements = biblio.findall('.//tei:idno', self.NAMESPACES)
            for idno in idno_elements:
                if idno.get('type') == 'DOI' and idno.text:
                    return idno.text.strip()
        
        return None
    
    def _extract_year(self, root: ET.Element) -> Optional[str]:
        date_elements = root.findall('.//tei:publicationStmt/tei:date', self.NAMESPACES)
        year = self._extract_year_from_dates(date_elements)
        if year:
            return year
        
        biblio_elements = root.findall('.//tei:biblStruct', self.NAMESPACES)
        for biblio in biblio_elements:
            date_elements = biblio.findall('.//tei:date', self.NAMESPACES)
            year = self._extract_year_from_dates(date_elements)
            if year:
                return year
        
        all_date_elements = root.findall('.//tei:date', self.NAMESPACES)
        return self._extract_year_from_dates(all_date_elements)
    
    def _extract_year_from_dates(self, date_elements: list) -> Optional[str]:
        for date_elem in date_elements:
            if date_elem.get('when'):
                date_str = date_elem.get('when')
                if len(date_str) >= 4 and date_str[:4].isdigit():
                    return date_str[:4]
            elif date_elem.text and date_elem.text.strip():
                date_text = date_elem.text.strip()
                year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
                if year_match:
                    return year_match.group()
        return None
    
    def _extract_authors(self, root: ET.Element) -> Optional[str]:
        authors = []
        
        author_elements = root.findall('.//tei:fileDesc//tei:author', self.NAMESPACES)
        for author_elem in author_elements:
            author_name = self._extract_author_name(author_elem)
            if author_name:
                authors.append(author_name)
        
        if not authors:
            author_elements = root.findall('.//tei:titleStmt//tei:author', self.NAMESPACES)
            for author_elem in author_elements:
                if author_elem.text and author_elem.text.strip():
                    authors.append(author_elem.text.strip())
        
        if not authors:
            return None
        
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            return f"{', '.join(authors[:-1])} and {authors[-1]}"
    
    def _extract_author_name(self, author_elem: ET.Element) -> Optional[str]:
        persname_elem = author_elem.find('.//tei:persName', self.NAMESPACES)
        if persname_elem is not None:
            forename_elem = persname_elem.find('tei:forename', self.NAMESPACES)
            surname_elem = persname_elem.find('tei:surname', self.NAMESPACES)
            
            if forename_elem is not None and surname_elem is not None:
                forename = forename_elem.text.strip() if forename_elem.text else ""
                surname = surname_elem.text.strip() if surname_elem.text else ""
                if forename and surname:
                    return f"{forename} {surname}"
                elif surname:
                    return surname
                elif forename:
                    return forename
            
            elif persname_elem.text and persname_elem.text.strip():
                return persname_elem.text.strip()
        
        if author_elem.text and author_elem.text.strip():
            return author_elem.text.strip()
        
        return None
    
    def _extract_venue(self, root: ET.Element) -> Optional[str]:
        journal_elements = root.findall('.//tei:monogr/tei:title[@level="j"]', self.NAMESPACES)
        if journal_elements:
            for journal_elem in journal_elements:
                if journal_elem.text and journal_elem.text.strip():
                    return journal_elem.text.strip()
        
        meeting_elements = root.findall('.//tei:monogr/tei:title[@level="m"]', self.NAMESPACES)
        if meeting_elements:
            for meeting_elem in meeting_elements:
                if meeting_elem.text and meeting_elem.text.strip():
                    return meeting_elem.text.strip()
        
        title_elements = root.findall('.//tei:monogr/tei:title', self.NAMESPACES)
        if title_elements:
            for title_elem in title_elements:
                if title_elem.text and title_elem.text.strip():
                    return title_elem.text.strip()
        
        publisher_elements = root.findall('.//tei:publisher', self.NAMESPACES)
        if publisher_elements:
            for pub_elem in publisher_elements:
                if pub_elem.text and pub_elem.text.strip():
                    return pub_elem.text.strip()
        
        return None