"""Backward-compatible constants for the original config.py module."""
from guildcart.settings import Settings

_settings = Settings.from_environment()
PREFIX = _settings.prefix
LOG_LEVEL = _settings.log_level
SERVER_SETTINGS = {}

__all__ = ["PREFIX", "LOG_LEVEL", "SERVER_SETTINGS"]
