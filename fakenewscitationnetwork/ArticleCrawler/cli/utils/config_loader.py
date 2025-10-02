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
    """
    Flatten nested configuration dictionary.
    
    Handles both flat and nested YAML structures.
    """
    flat = {}
    
    # Check if already flat
    if 'name' in nested_dict and 'seeds' in nested_dict:
        return nested_dict
    
    # Extract from nested structure
    for section_name, section_data in nested_dict.items():
        if isinstance(section_data, dict):
            flat.update(section_data)
        else:
            flat[section_name] = section_data
    
    return flat


def _structure_config(flat_dict: dict) -> dict:
    """
    Structure flat configuration into logical sections.
    
    Creates a more readable YAML output.
    """
    # Convert Path objects to strings
    for key, value in flat_dict.items():
        if isinstance(value, Path):
            flat_dict[key] = str(value)
    
    structured = {
        "experiment": {
            "name": flat_dict.pop("name"),
        },
        "seeds": {
            "ids": flat_dict.pop("seeds"),
        },
        "keywords": flat_dict.pop("keywords", []),
        "crawling": {
            "max_iterations": flat_dict.pop("max_iterations"),
            "papers_per_iteration": flat_dict.pop("papers_per_iteration"),
            "api_provider": flat_dict.pop("api_provider"),
            "api_retries": flat_dict.pop("api_retries"),
        },
        "sampling": {
            "no_keyword_lambda": flat_dict.pop("no_keyword_lambda"),
            "hyperparams": flat_dict.pop("sampling_hyperparams"),
            "ignored_venues": flat_dict.pop("ignored_venues"),
        },
        "text_processing": {
            "min_abstract_length": flat_dict.pop("min_abstract_length"),
            "num_topics": flat_dict.pop("num_topics"),
            "topic_model": flat_dict.pop("topic_model"),
            "stemmer": flat_dict.pop("stemmer"),
            "language": flat_dict.pop("language"),
            "save_figures": flat_dict.pop("save_figures"),
            "random_state": flat_dict.pop("random_state"),
        },
        "graph": {
            "include_author_nodes": flat_dict.pop("include_author_nodes"),
            "max_centrality_iterations": flat_dict.pop("max_centrality_iterations"),
        },
        "retraction": {
            "enable": flat_dict.pop("enable_retraction_watch"),
            "avoid_in_sampler": flat_dict.pop("avoid_retraction_in_sampler"),
            "avoid_in_reporting": flat_dict.pop("avoid_retraction_in_reporting"),
        },
        "output": {
            "root_folder": flat_dict.pop("root_folder", None),
            "log_level": flat_dict.pop("log_level"),
            "open_vault_folder": flat_dict.pop("open_vault_folder"),
        }
    }
    
    return structured