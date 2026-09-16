"""Application settings manager."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    """Manages application settings."""

    DEFAULT_CONFIG_PATH = "config/default_settings.json"
    USER_CONFIG_PATH = "config/settings.json"

    def __init__(self):
        """Initialize settings manager."""
        os.makedirs("config", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/logs", exist_ok=True)
        os.makedirs("data/videos", exist_ok=True)
        os.makedirs("data/screenshots", exist_ok=True)
        os.makedirs("profiles", exist_ok=True)
        
        self.settings: Dict[str, Any] = {}
        self._load_settings()

    def _load_settings(self):
        """Load settings from config files."""
        # Load default settings
        if os.path.exists(self.DEFAULT_CONFIG_PATH):
            with open(self.DEFAULT_CONFIG_PATH, 'r') as f:
                self.settings = json.load(f)
        
        # Override with user settings if they exist
        if os.path.exists(self.USER_CONFIG_PATH):
            with open(self.USER_CONFIG_PATH, 'r') as f:
                user_settings = json.load(f)
                self._deep_merge(self.settings, user_settings)

    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value using dot notation.
        
        Args:
            key: Setting key (e.g., 'browser.headless')
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set setting value using dot notation.
        
        Args:
            key: Setting key (e.g., 'browser.headless')
            value: Value to set
        """
        keys = key.split('.')
        settings = self.settings
        
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        settings[keys[-1]] = value
        self._save_settings()

    def _save_settings(self):
        """Save settings to user config file."""
        with open(self.USER_CONFIG_PATH, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return self.settings.copy()


# Global settings instance
settings = SettingsManager()
