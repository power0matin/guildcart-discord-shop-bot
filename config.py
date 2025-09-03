# config.py
"""
Configuration file for the bot.

Stores non-sensitive settings like prefix and logging level.
Sensitive data like tokens should be in environment variables.

Server-specific settings can be added here as a dict, e.g., for per-guild configs.
Optional: Logging config can be expanded here.
"""

PREFIX = "$"  # Command prefix for text-based commands
LOG_LEVEL = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Example: Server-specific settings (guild_id: {'key': 'value'})
SERVER_SETTINGS = {
    # 1234567890: {'welcome_channel': 0987654321}
}

