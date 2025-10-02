from typing import Optional

class RetractionConfig:
    """
    Configuration for retraction watch functionality.
    
    This class handles all retraction-related settings including data sources,
    filtering behavior, and integration options.
    """
    
    def __init__(self,
                 enable_retraction_watch: bool = True,
                 avoid_retraction_in_sampler: bool = False,
                 avoid_retraction_in_reporting: bool = True,
                 retraction_watch_raw_url: str = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv",
                 retraction_watch_commits_api_url: str = "https://gitlab.com/api/v4/projects/crossref%2Fretraction-watch-data/repository/commits?path=retraction_watch.csv&per_page=1"):
        """
        Initialize retraction configuration.
        
        Args:
            enable_retraction_watch (bool): Toggle the entire retraction watch mechanism
            avoid_retraction_in_sampler (bool): Exclude retracted papers from sampling
            avoid_retraction_in_reporting (bool): Exclude retracted papers from NLP analysis
            retraction_watch_raw_url (str): URL to retrieve the raw retraction watch CSV
            retraction_watch_commits_api_url (str): URL for the retraction watch commits API
        """
        self.enable_retraction_watch = enable_retraction_watch
        self.avoid_retraction_in_sampler = avoid_retraction_in_sampler
        self.avoid_retraction_in_reporting = avoid_retraction_in_reporting
        self.retraction_watch_raw_url = retraction_watch_raw_url
        self.retraction_watch_commits_api_url = retraction_watch_commits_api_url
    
    def copy(self):
        """Create a copy of this configuration."""
        return RetractionConfig(
            enable_retraction_watch=self.enable_retraction_watch,
            avoid_retraction_in_sampler=self.avoid_retraction_in_sampler,
            avoid_retraction_in_reporting=self.avoid_retraction_in_reporting,
            retraction_watch_raw_url=self.retraction_watch_raw_url,
            retraction_watch_commits_api_url=self.retraction_watch_commits_api_url
        )

class RetractionOptions(RetractionConfig):
    """Backward compatibility alias for RetractionConfig."""
    pass