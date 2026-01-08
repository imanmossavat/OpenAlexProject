 
"""
Sample API responses for mocking.
"""

# OpenAlex sample response
OPENALEX_PAPER_RESPONSE = {
    'id': 'https://openalex.org/W2134567890',
    'title': 'Sample Paper Title',
    'abstract_inverted_index': {
        'This': [0],
        'is': [1],
        'a': [2],
        'sample': [3],
        'abstract': [4],
        'text': [5]
    },
    'publication_year': 2024,
    'doi': 'https://doi.org/10.1234/test.2024',
    'primary_location': {
        'source': {
            'display_name': 'Test Journal'
        }
    },
    'authorships': [
        {
            'author': {
                'id': 'https://openalex.org/A1234567890',
                'display_name': 'John Doe'
            }
        }
    ],
    'referenced_works': [
        'https://openalex.org/W999999999'
    ],
    'cited_by_count': 10
}

# Semantic Scholar sample response
S2_PAPER_RESPONSE = {
    'paperId': '1234567890abcdef',
    'title': 'Sample S2 Paper',
    'abstract': 'This is a sample abstract from Semantic Scholar.',
    'venue': 'S2 Conference',
    'year': 2024,
    'doi': '10.1234/s2.2024',
    'authors': [
        {
            'authorId': 'S2_A1',
            'name': 'Jane Smith'
        }
    ],
    'citations': [],
    'references': []
}

# Sample batch response
OPENALEX_BATCH_RESPONSE = [
    OPENALEX_PAPER_RESPONSE,
    {
        'id': 'https://openalex.org/W9876543210',
        'title': 'Another Sample Paper',
        'abstract_inverted_index': None,
        'publication_year': 2023,
        'doi': None,
        'primary_location': None,
        'authorships': [],
        'referenced_works': [],
        'cited_by_count': 0
    }
]