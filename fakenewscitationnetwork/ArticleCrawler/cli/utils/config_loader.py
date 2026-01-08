"""
Configuration file loading and saving utilities.
"""

import yaml
from pathlib import Path
from ..models.experiment_config import ExperimentConfig


def load_config(config_path: Path) -> ExperimentConfig:
    """
    Load experiment configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        ExperimentConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    # Convert nested structure if needed
    config_dict = _flatten_config(config_dict)
    
    return ExperimentConfig(**config_dict)


def save_config(config: ExperimentConfig, config_path: Path):
    """
    Save experiment configuration to YAML file.
    
    Args:
        config: ExperimentConfig object to save
        config_path: Path where to save the configuration
    """
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dictionary
    config_dict = config.model_dump()
    
    # Structure for better readability
    structured_config = _structure_config(config_dict)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(structured_config, f, default_flow_style=False, sort_keys=False)


def _flatten_config(nested_dict: dict) -> dict:
    flat = {}
    
    if 'name' in nested_dict and 'seeds' in nested_dict:
        return nested_dict
    
    if 'experiment' in nested_dict and isinstance(nested_dict['experiment'], dict):
        flat['name'] = nested_dict['experiment'].get('name')
        display_name = nested_dict['experiment'].get('display_name')
        if display_name:
            flat['display_name'] = display_name
    
    if 'seeds' in nested_dict:
        if isinstance(nested_dict['seeds'], dict) and 'ids' in nested_dict['seeds']:
            flat['seeds'] = nested_dict['seeds']['ids']
        elif isinstance(nested_dict['seeds'], list):
            flat['seeds'] = nested_dict['seeds']
    
    if 'keywords' in nested_dict:
        flat['keywords'] = nested_dict['keywords']

    if 'library' in nested_dict and isinstance(nested_dict['library'], dict):
        lib_block = nested_dict['library']
        if 'path' in lib_block and lib_block['path']:
            flat['library_path'] = Path(lib_block['path'])
        if 'name' in lib_block and lib_block['name']:
            flat['library_name'] = lib_block['name']
    
    if 'crawling' in nested_dict and isinstance(nested_dict['crawling'], dict):
        crawl = nested_dict['crawling']
        flat['max_iterations'] = crawl.get('max_iterations', 1)
        flat['papers_per_iteration'] = crawl.get('papers_per_iteration', 1)
        flat['api_provider'] = crawl.get('api_provider', 'openalex')
        flat['api_retries'] = crawl.get('api_retries', 3)
    
    if 'sampling' in nested_dict and isinstance(nested_dict['sampling'], dict):
        samp = nested_dict['sampling']
        flat['no_keyword_lambda'] = samp.get('no_keyword_lambda', 0.2)
        flat['sampling_hyperparams'] = samp.get('hyperparams', {'year': 0.3, 'centrality': 1.0})
        flat['ignored_venues'] = samp.get('ignored_venues', ['', 'ArXiv', 'medRxiv', 'WWW'])
    
    if 'text_processing' in nested_dict and isinstance(nested_dict['text_processing'], dict):
        text = nested_dict['text_processing']
        flat['min_abstract_length'] = text.get('min_abstract_length', 120)
        flat['num_topics'] = text.get('num_topics', 20)
        flat['topic_model'] = text.get('topic_model', 'NMF')
        flat['stemmer'] = text.get('stemmer', 'Porter')
        flat['language'] = text.get('language', 'en')
        flat['save_figures'] = text.get('save_figures', True)
        flat['random_state'] = text.get('random_state', 42)
    
    if 'graph' in nested_dict and isinstance(nested_dict['graph'], dict):
        graph = nested_dict['graph']
        flat['include_author_nodes'] = graph.get('include_author_nodes', False)
        flat['max_centrality_iterations'] = graph.get('max_centrality_iterations', 1000)
    
    if 'retraction' in nested_dict and isinstance(nested_dict['retraction'], dict):
        retr = nested_dict['retraction']
        flat['enable_retraction_watch'] = retr.get('enable', True)
        flat['avoid_retraction_in_sampler'] = retr.get('avoid_in_sampler', False)
        flat['avoid_retraction_in_reporting'] = retr.get('avoid_in_reporting', True)
    
    if 'output' in nested_dict and isinstance(nested_dict['output'], dict):
        output = nested_dict['output']
        root = output.get('root_folder')
        if root:
            flat['root_folder'] = Path(root)
        flat['log_level'] = output.get('log_level', 'INFO')
        flat['open_vault_folder'] = output.get('open_vault_folder', True)
    
    return flat


def _structure_config(flat_dict: dict) -> dict:
    structured = {
        'experiment': {
            'name': flat_dict.get('name')
        },
        'seeds': {
            'ids': flat_dict.get('seeds', [])
        },
        'keywords': flat_dict.get('keywords', []),
        'crawling': {
            'max_iterations': flat_dict.get('max_iterations', 1),
            'papers_per_iteration': flat_dict.get('papers_per_iteration', 1),
            'api_provider': flat_dict.get('api_provider', 'openalex'),
            'api_retries': flat_dict.get('api_retries', 3)
        },
        'sampling': {
            'no_keyword_lambda': flat_dict.get('no_keyword_lambda', 0.2),
            'hyperparams': flat_dict.get('sampling_hyperparams', {'year': 0.3, 'centrality': 1.0}),
            'ignored_venues': flat_dict.get('ignored_venues', ['', 'ArXiv', 'medRxiv', 'WWW'])
        },
        'text_processing': {
            'min_abstract_length': flat_dict.get('min_abstract_length', 120),
            'num_topics': flat_dict.get('num_topics', 20),
            'topic_model': flat_dict.get('topic_model', 'NMF'),
            'stemmer': flat_dict.get('stemmer', 'Porter'),
            'language': flat_dict.get('language', 'en'),
            'save_figures': flat_dict.get('save_figures', True),
            'random_state': flat_dict.get('random_state', 42)
        },
        'graph': {
            'include_author_nodes': flat_dict.get('include_author_nodes', False),
            'max_centrality_iterations': flat_dict.get('max_centrality_iterations', 1000)
        },
        'retraction': {
            'enable': flat_dict.get('enable_retraction_watch', True),
            'avoid_in_sampler': flat_dict.get('avoid_retraction_in_sampler', False),
            'avoid_in_reporting': flat_dict.get('avoid_retraction_in_reporting', True)
        },
        'output': {
            'root_folder': str(flat_dict.get('root_folder', Path.cwd() / 'data' / 'crawler_experiments')),
            'log_level': flat_dict.get('log_level', 'INFO'),
            'open_vault_folder': flat_dict.get('open_vault_folder', True)
        }
    }

    display_name = flat_dict.get('display_name')
    if display_name:
        structured['experiment']['display_name'] = display_name

    library_path = flat_dict.get('library_path')
    library_name = flat_dict.get('library_name')
    if library_path or library_name:
        structured['library'] = {}
        if library_path:
            structured['library']['path'] = str(library_path)
        if library_name:
            structured['library']['name'] = library_name
    
    return structured
