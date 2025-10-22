import tempfile
import shutil
import atexit
from pathlib import Path
from typing import Optional
import logging


class TempLibraryManager:
    """
    Manages temporary library creation and cleanup.
    
    Ensures temporary libraries are cleaned up on exit or error.
    """
    
    _temp_libraries = []
    _cleanup_registered = False
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize temp library manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        if not TempLibraryManager._cleanup_registered:
            atexit.register(TempLibraryManager._cleanup_all_temp_libraries)
            TempLibraryManager._cleanup_registered = True
    
    def create_temp_library(self, prefix: str = "author_analysis_") -> Path:
        """
        Create a temporary library directory.
        
        Args:
            prefix: Prefix for temporary directory name
            
        Returns:
            Path to created temporary library
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        
        TempLibraryManager._temp_libraries.append(temp_dir)
        
        self.logger.info(f"Created temporary library at: {temp_dir}")
        return temp_dir
    
    def cleanup_temp_library(self, library_path: Path) -> bool:
        """
        Clean up a specific temporary library.
        
        Args:
            library_path: Path to library to clean up
            
        Returns:
            True if cleaned up successfully, False otherwise
        """
        try:
            if library_path.exists():
                shutil.rmtree(library_path)
                self.logger.info(f"Cleaned up temporary library: {library_path}")
                
                if library_path in TempLibraryManager._temp_libraries:
                    TempLibraryManager._temp_libraries.remove(library_path)
                
                return True
        except Exception as e:
            self.logger.error(f"Failed to clean up temporary library {library_path}: {e}")
            return False
        
        return False
    
    def make_permanent(
        self, 
        temp_library_path: Path, 
        permanent_path: Path
    ) -> Path:
        """
        Convert a temporary library to permanent by moving it.
        
        Args:
            temp_library_path: Path to temporary library
            permanent_path: Desired permanent location
            
        Returns:
            Path to permanent library
            
        Raises:
            FileExistsError: If permanent path already exists
        """
        if permanent_path.exists():
            raise FileExistsError(f"Permanent library path already exists: {permanent_path}")
        
        shutil.move(str(temp_library_path), str(permanent_path))
        
        if temp_library_path in TempLibraryManager._temp_libraries:
            TempLibraryManager._temp_libraries.remove(temp_library_path)
        
        self.logger.info(f"Converted temporary library to permanent: {permanent_path}")
        return permanent_path
    
    @staticmethod
    def _cleanup_all_temp_libraries():
        """Clean up all tracked temporary libraries on exit."""
        logger = logging.getLogger(__name__)
        
        for temp_lib in TempLibraryManager._temp_libraries[:]:
            try:
                if temp_lib.exists():
                    shutil.rmtree(temp_lib)
                    logger.info(f"Cleaned up temporary library on exit: {temp_lib}")
            except Exception as e:
                logger.error(f"Failed to clean up {temp_lib} on exit: {e}")
        
        TempLibraryManager._temp_libraries.clear()