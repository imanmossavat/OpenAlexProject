class StoppingConfig:
    """
    Configuration for crawler stopping criteria.
    
    This class handles all settings related to when the crawler should stop
    its execution.
    """
    
    def __init__(self, 
                 max_iter: int = 1, 
                 max_df_size: float = 1E9):
        """
        Initialize stopping configuration.
        
        Args:
            max_iter (int): Maximum number of crawler iterations
            max_df_size (float): Maximum DataFrame size before stopping
        """
        self.max_iter = max_iter
        self.max_df_size = max_df_size
        
        if max_iter <= 0:
            raise ValueError("max_iter must be positive")
        if max_df_size <= 0:
            raise ValueError("max_df_size must be positive")
    
    def copy(self):
        """Create a copy of this configuration."""
        return StoppingConfig(
            max_iter=self.max_iter,
            max_df_size=self.max_df_size
        )

class StoppingOptions(StoppingConfig):
    """Backward compatibility alias for StoppingConfig."""
    pass