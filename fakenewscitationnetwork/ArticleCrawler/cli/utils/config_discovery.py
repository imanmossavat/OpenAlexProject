from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConfigSummary:
    name: str
    path: Path
    config_path: Path
    created: Optional[datetime]
    num_seeds: int
    num_keywords: int
    api_provider: str


class ConfigDiscovery:
    
    @staticmethod
    def find_experiments(root_folder: Path) -> List[ConfigSummary]:
        root_folder = Path(root_folder)
        
        if not root_folder.exists():
            return []
        
        summaries = []
        
        for experiment_dir in root_folder.iterdir():
            if not experiment_dir.is_dir():
                continue
            
            config_file = experiment_dir / 'config.yaml'
            
            if not config_file.exists():
                continue
            
            try:
                from ..utils.config_loader import load_config
                config = load_config(config_file)
                
                created = datetime.fromtimestamp(config_file.stat().st_ctime)
                
                summary = ConfigSummary(
                    name=config.name,
                    path=experiment_dir,
                    config_path=config_file,
                    created=created,
                    num_seeds=len(config.seeds) if config.seeds else 0,
                    num_keywords=len(config.keywords) if config.keywords else 0,
                    api_provider=config.api_provider
                )
                summaries.append(summary)
                
            except Exception as e:
                continue
        
        summaries.sort(key=lambda x: x.created, reverse=True)
        return summaries
    
    @staticmethod
    def get_default_experiments_folder() -> Path:
        return Path.cwd() / 'data' / 'crawler_experiments'