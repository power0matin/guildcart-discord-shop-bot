"""GuildCart application factory and process entry point."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from guildcart.settings import ConfigurationError, Settings

COG_MODULES = ("guildcart.cogs.core", "guildcart.cogs.shop")
logger = logging.getLogger("guildcart")


class GuildCartBot(commands.Bot):
    """Discord bot configured from an explicit settings snapshot."""

    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        # Preserve current prefix-command/member lookup behavior.
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=settings.prefix, intents=intents)
        self.settings = settings
        # discord.py registers a default help command; GuildCart replaces it with
        # the help command supplied by CoreCog, as the pre-refactor bot did.
        self.remove_command("help")

    async def setup_hook(self) -> None:
        """Load only Discord cogs, never helper modules as extensions."""
        for module_name in COG_MODULES:
            try:
                await self.load_extension(module_name)
                logger.info("Loaded Discord extension: %s", module_name)
            except Exception as exc:
                logger.exception("Failed to load required extension %s", module_name)
                raise RuntimeError(
                    f"Could not load required extension {module_name}; "
                    "see the preceding error for details."
                ) from exc

        # Preserve global sync behavior during this refactor.
        await self.tree.sync()
        logger.info("Slash commands synced.")


def create_bot(settings: Settings | None = None) -> GuildCartBot:
    """Construct the bot without connecting to Discord."""
    return GuildCartBot(settings or Settings.from_environment())


def configure_logging(settings: Settings) -> None:
    """Configure console and UTF-8 file logging."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def main(bot: GuildCartBot | None = None) -> None:
    """Validate startup configuration and start the Discord process."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "DISCORD_TOKEN is missing. Copy .env.example to .env and configure your bot token."
        )

    if bot is None:
        try:
            bot = create_bot(Settings.from_environment())
        except ConfigurationError as exc:
            raise SystemExit(f"Invalid GuildCart configuration: {exc}") from exc

    configure_logging(bot.settings)
    logger.info("Starting GuildCart.")
    bot.run(token, log_handler=None)


# Backward-compatible class name from the original entry point.
MyBot = GuildCartBot

__all__ = [
    "COG_MODULES",
    "GuildCartBot",
    "MyBot",
    "configure_logging",
    "create_bot",
    "main",
]
