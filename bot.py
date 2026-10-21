"""Backward-compatible wrapper for the original bot.py entry point.

New installations should run main.py. This wrapper preserves older scripts that
still invoke python bot.py.
"""
from dotenv import load_dotenv

load_dotenv()

from guildcart.app import COG_MODULES, GuildCartBot, MyBot, create_bot, main
from guildcart.settings import Settings

bot = create_bot(Settings.from_environment())

if __name__ == "__main__":
    main(bot)
