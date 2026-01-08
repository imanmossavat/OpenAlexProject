"""
Formats Zotero items for display.
Single Responsibility: Formatting metadata for UI presentation.
"""


class ZoteroItemFormatter:
    """Formats Zotero items for display in CLI."""
    
    @staticmethod
    def format_collection_preview(metadata: dict) -> str:
        """
        Format metadata for brief display in collection listing.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted string for display
        """
        lines = []
        
        lines.append(metadata['title'])
        
        authors_str = ', '.join(metadata['authors']) if metadata['authors'] else 'N/A'
        lines.append(f"   👤 {authors_str}")
        
        date_pub_parts = []
        if metadata['date']:
            date_pub_parts.append(f"📅 {metadata['date']}")
        if metadata['publication']:
            date_pub_parts.append(f"🏛️  {metadata['publication']}")
        if date_pub_parts:
            lines.append(f"   {' | '.join(date_pub_parts)}")
        
        if metadata['doi']:
            lines.append(f"   🔗 DOI: {metadata['doi']}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_detailed(metadata: dict) -> str:
        """
        Format metadata for detailed display.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted string with full details
        """
        lines = []
        lines.append(f"\n📄 Title: {metadata['title']}")
        
        authors_str = ', '.join(metadata['authors']) if metadata['authors'] else 'N/A'
        lines.append(f"👤 Authors: {authors_str}")
        lines.append(f"📅 Date: {metadata['date']}")
        lines.append(f"🏛️  Publication: {metadata['publication']}")
        lines.append(f"🔗 DOI: {metadata['doi']}")
        
        if metadata['url']:
            lines.append(f"🌐 URL: {metadata['url']}")
        
        tags_str = ', '.join(metadata['tags']) if metadata['tags'] else 'None'
        lines.append(f"🏷️  Tags: {tags_str}")
        
        if metadata['abstract']:
            lines.append("\n📝 Abstract:")
            abstract = metadata['abstract']
            preview = abstract[:500] + ("..." if len(abstract) > 500 else "")
            lines.append(preview)
        
        lines.append("\n" + "-" * 60)
        return '\n'.join(lines)