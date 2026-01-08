"""
Backward compatibility module for configuration classes.

This module provides the original configuration classes but they now
inherit from the new focused config classes. This ensures existing
code continues to work while benefiting from the improved architecture.
"""

from pathlib import Path
import inspect
from ..config.api_config import APIConfig
from ..config.sampling_config import SamplingConfig
from ..config.text_config import TextProcessingConfig
from ..config.storage_config import StorageAndLoggingConfig
from ..config.graph_config import GraphConfig
from ..config.retraction_config import RetractionConfig
from ..config.stopping_config import StoppingConfig

class ConfigObserver:
    def __init__(self):
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def notify(self, new_value):
        for callback in self.callbacks:
            callback(new_value)

TextOptions = TextProcessingConfig
SamplingOptions = SamplingConfig  
StoppingOptions = StoppingConfig
GraphOptions = GraphConfig
RetractionOptions = RetractionConfig
StorageAndLoggingOptions = StorageAndLoggingConfig

class CrawlerParameters:
    """
    Crawler parameters handling seed papers and keywords.
    
    This class remains unchanged as it's already well-focused.
    """
    
    def __init__(self, seed_paperid_file=None, seed_paperid=None, keywords=None):
        """
        Initializes CrawlerParameters with seed paper configuration and keywords.
        
        Args:
            seed_paperid_file (str or None): Path to the file containing seed paper IDs.
            seed_paperid (list or None): List of seed paper IDs.
            keywords (list): List of keywords for validation.
        
        Raises:
            ValueError: If both seed_paperid and seed_paperid_file are defined or both are None.
        """
        self.seed_paperid_file = seed_paperid_file
        self.seed_paperid = seed_paperid
        self.keywords = keywords or []

        if self.seed_paperid and self.seed_paperid_file:
            raise ValueError("Both seed_paperid and seed_paperid_file are defined. Please provide only one.")
        elif not self.seed_paperid and not self.seed_paperid_file:
            raise ValueError("Neither seed_paperid nor seed_paperid_file is defined. Please provide one.")

        self.validate_keywords()

        if self.seed_paperid_file:
            self.load_seed_paperIds()

    def validate_keywords(self):
        """
        Validates that all keywords have balanced parentheses.

        Raises:
            ValueError: If any keyword has unbalanced parentheses.
        """
        def check_balanced(expression):
            stack = []
            for char in expression:
                if char == '(':
                    stack.append(char)
                elif char == ')':
                    if not stack:
                        return False
                    stack.pop()
            return len(stack) == 0
        
        unbalanced_keywords = [kw for kw in self.keywords if not check_balanced(kw)]
        if unbalanced_keywords:
            raise ValueError(f"Unbalanced parentheses in keywords: {unbalanced_keywords}")
        return True

    def load_seed_paperIds(self):
        """
        Loads seed papers from the file specified by seed_paperid_file.

        Raises:
            ValueError: If the file is empty or cannot load paper IDs.
        """
        try:
            with open(self.seed_paperid_file, 'r') as file:
                values = [line.strip() for line in file]
            self.seed_paperid = list(set(values))
            if not self.seed_paperid:
                raise ValueError(f"No seed paper IDs were loaded from {self.seed_paperid_file}.")
            print(f"Loaded {len(self.seed_paperid)} unique seed papers from file.")
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.seed_paperid_file} does not exist.")