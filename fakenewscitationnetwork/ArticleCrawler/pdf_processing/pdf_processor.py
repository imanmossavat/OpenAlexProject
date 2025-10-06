
from pathlib import Path
from typing import List, Optional
import logging
from .docker_manager import DockerManager
from .grobid_client import GrobidClientWrapper
from .metadata_extractor import PDFMetadataExtractor
from .models import PDFProcessingResult


class PDFProcessor:
    
    def __init__(self, 
                 docker_manager: Optional[DockerManager] = None,
                 grobid_client: Optional[GrobidClientWrapper] = None,
                 metadata_extractor: Optional[PDFMetadataExtractor] = None,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.docker_manager = docker_manager or DockerManager(logger=self.logger)
        self.grobid_client = grobid_client or GrobidClientWrapper(logger=self.logger)
        self.metadata_extractor = metadata_extractor or PDFMetadataExtractor(logger=self.logger)
    
    def ensure_grobid_running(self) -> bool:
        if self.docker_manager.is_grobid_running():
            return True
        
        self.logger.info("GROBID service not running, attempting to start...")
        return self.docker_manager.start_container()
    
    def process_pdfs(self, pdf_paths: List[Path]) -> List[PDFProcessingResult]:
        if not pdf_paths:
            return []
        
        if not self.ensure_grobid_running():
            self.logger.error("Could not start GROBID service")
            return [
                PDFProcessingResult(
                    pdf_path=path,
                    success=False,
                    error_message="GROBID service unavailable"
                )
                for path in pdf_paths
            ]
        
        xml_results = self.grobid_client.process_pdfs(pdf_paths)
        
        results = []
        for pdf_path in pdf_paths:
            if pdf_path in xml_results:
                xml_content = xml_results[pdf_path]
                metadata = self.metadata_extractor.extract(xml_content, pdf_path.name)
                
                if metadata:
                    results.append(PDFProcessingResult(
                        pdf_path=pdf_path,
                        metadata=metadata,
                        success=True
                    ))
                else:
                    results.append(PDFProcessingResult(
                        pdf_path=pdf_path,
                        success=False,
                        error_message="Failed to extract metadata from XML"
                    ))
            else:
                results.append(PDFProcessingResult(
                    pdf_path=pdf_path,
                    success=False,
                    error_message="GROBID did not produce XML output"
                ))
        
        return results