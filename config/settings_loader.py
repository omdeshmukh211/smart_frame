"""
Settings Loader
Loads configuration from YAML files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


def load_settings() -> Dict[str, Any]:
    """
    Load settings from config/settings.yaml.
    
    Returns:
        Dictionary of settings with defaults
    """
    config_path = Path(__file__).parent / 'settings.yaml'
    
    # Default settings
    defaults = {
        'slideshow_interval': 5,  # seconds
        'slideshow_transition': 'fade',  # fade or instant
        'photos_dir': str(Path.home() / 'Pictures'),
        'music_autoplay': False,
        'volume': 70,
        'brightness': 100,
        'clock_timeout': 120,
        'display_width': 1024,
        'display_height': 600,
    }
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f) or {}
                defaults.update(loaded)
    except Exception as e:
        import logging
        logging.getLogger('settings_loader').warning(f"Error loading settings: {e}")
    
    return defaults


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to config/settings.yaml.
    
    Args:
        settings: Dictionary of settings
        
    Returns:
        True if successful
    """
    config_path = Path(__file__).parent / 'settings.yaml'
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.safe_dump(settings, f, default_flow_style=False)
        return True
    except Exception as e:
        import logging
        logging.getLogger('settings_loader').error(f"Error saving settings: {e}")
        return False
