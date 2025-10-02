 
"""
Sample paper objects for testing.
"""

from unittest.mock import Mock
from typing import List


def create_paper(
    paper_id: str,
    title: str,
    abstract: str = None,
    venue: str = "Test Venue",
    year: int = 2024,
    doi: str = None,
    authors: List = None,
    citations: List = None,
    references: List = None
):
    """
    Factory function to create paper objects.
    
    Args:
        paper_id: Paper ID
        title: Paper title
        abstract: Paper abstract (optional)
        venue: Publication venue
        year: Publication year
        doi: DOI string
        authors: List of author objects
        citations: List of citing papers
        references: List of referenced papers
    
    Returns:
        Mock paper object
    """
    paper = Mock()
    paper.paperId = paper_id
    paper.title = title
    paper.abstract = abstract
    paper.venue = venue
    paper.year = year
    paper.doi = doi or f"10.1234/{paper_id}"
    paper.authors = authors or []
    paper.citations = citations or []
    paper.references = references or []
    
    return paper


def create_author(author_id: str, name: str):
    """
    Factory function to create author objects.
    
    Args:
        author_id: Author ID
        name: Author name
    
    Returns:
        Mock author object
    """
    author = Mock()
    author.authorId = author_id
    author.name = name
    return author


def create_complete_paper_with_citations():
    """
    Create a complete paper with authors, citations, and references.
    
    Returns:
        Mock paper object with full relationships
    """
    # Create authors
    author1 = create_author("A1", "Alice Johnson")
    author2 = create_author("A2", "Bob Smith")
    
    # Create referenced papers
    ref1 = create_paper("W001", "Referenced Paper 1", authors=[create_author("A3", "Carol White")])
    ref2 = create_paper("W002", "Referenced Paper 2", authors=[create_author("A4", "Dave Brown")])
    
    # Create citing papers
    cite1 = create_paper("W003", "Citing Paper 1", authors=[create_author("A5", "Eve Green")])
    cite2 = create_paper("W004", "Citing Paper 2", authors=[create_author("A6", "Frank Black")])
    
    # Create main paper
    main_paper = create_paper(
        paper_id="W100",
        title="Main Test Paper",
        abstract="This is a comprehensive test paper with full metadata.",
        venue="Top Conference",
        year=2024,
        doi="10.1234/main.2024",
        authors=[author1, author2],
        citations=[cite1, cite2],
        references=[ref1, ref2]
    )
    
    return main_paper


def create_papers_batch(count: int = 5):
    """
    Create a batch of papers for testing.
    
    Args:
        count: Number of papers to create
    
    Returns:
        List of mock paper objects
    """
    papers = []
    for i in range(count):
        author = create_author(f"A{i}", f"Author {i}")
        paper = create_paper(
            paper_id=f"W{i:09d}",
            title=f"Test Paper {i}",
            abstract=f"Abstract for test paper {i}.",
            year=2024 - (i % 5),
            authors=[author]
        )
        papers.append(paper)
    
    return papers