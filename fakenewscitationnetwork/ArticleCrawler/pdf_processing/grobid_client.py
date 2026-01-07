import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import logging
from grobid_client.grobid_client import GrobidClient


class GrobidClientWrapper:
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        resolved_url = server_url or os.getenv("GROBID_URL") or os.getenv("GROBID_BASE_URL") or "http://localhost:8070"
        self.server_url = resolved_url
        self.logger = logger or logging.getLogger(__name__)
        self.client = GrobidClient(grobid_server=resolved_url, check_server=False)
    
    def process_pdfs(self, pdf_paths: List[Path]) -> dict:
        if not pdf_paths:
            return {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            pdf_mapping = {}
            for pdf_path in pdf_paths:
                filename = pdf_path.name
                temp_pdf_path = input_dir / filename
                shutil.copy2(pdf_path, temp_pdf_path)
                pdf_mapping[filename] = pdf_path
                self.logger.info(f"Added: {filename}")
            
            self.logger.info(f"Processing {len(pdf_paths)} files with GROBID...")
            
            try:
                self.client.process(
                    service="processHeaderDocument",
                    input_path=str(input_dir),
                    output=str(output_dir),
                    n=min(10, len(pdf_paths)),
                    consolidate_header=True
                )
            except Exception as e:
                self.logger.error(f"GROBID processing error: {e}")
                return {}
            
            results = {}
            xml_files = list(output_dir.glob("*.xml"))
            self.logger.info(f"Found {len(xml_files)} XML output files")
            
            pdf_to_xml = self._match_pdfs_to_xml(list(pdf_mapping.keys()), xml_files)
            
            for pdf_filename, xml_file in pdf_to_xml.items():
                try:
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    results[pdf_mapping[pdf_filename]] = xml_content
                except Exception as e:
                    self.logger.error(f"Error reading {xml_file}: {e}")
            
            return results
    
    def _match_pdfs_to_xml(self, pdf_filenames: List[str], xml_files: List[Path]) -> dict:
        pdf_to_xml = {}
        
        for xml_file in xml_files:
            xml_base = xml_file.stem.replace('.tei', '').replace('.xml', '')
            
            for pdf_file in pdf_filenames:
                pdf_base = Path(pdf_file).stem
                
                if xml_base == pdf_base or xml_base in pdf_base or pdf_base in xml_base:
                    pdf_to_xml[pdf_file] = xml_file
                    break
        
        return pdf_to_xml
