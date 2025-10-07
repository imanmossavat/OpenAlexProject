
from .matcher import ZoteroMatcher, MatchResult, MatchCandidate
from .strategies import (
    TitleMatchStrategy,
    OpenAlexTitleMatchStrategy,
    SemanticScholarTitleMatchStrategy,
    TitleSimilarityCalculator
)

__all__ = [
    'ZoteroMatcher',
    'MatchResult',
    'MatchCandidate',
    'TitleMatchStrategy',
    'OpenAlexTitleMatchStrategy',
    'SemanticScholarTitleMatchStrategy',
    'TitleSimilarityCalculator',
]