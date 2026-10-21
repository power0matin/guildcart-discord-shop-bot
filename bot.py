import discord
from discord.ext import commands
import os
import logging
import asyncio
from dotenv import load_dotenv

# Load local environment variables before reading DISCORD_TOKEN.
load_dotenv()

from config import PREFIX, LOG_LEVEL

# Setup logging to file in logs/ directory
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Custom Bot class for additional setup
class MyBot(commands.Bot):
    async def setup_hook(self):
        # Automatically load all cogs from features/
        for filename in os.listdir("features"):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"features.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded cog: {cog_name}")
                except Exception as e:
                    logger.exception(f"Failed to load required cog {cog_name}")
                    raise RuntimeError(
                        f"Could not load required extension {cog_name}; "
                        "see the preceding error for details."
                    ) from e

        # Sync slash commands globally (for production, sync per guild if needed)
        # Note: Syncing can be rate-limited; do this sparingly in production
        await self.tree.sync()
        logger.info("Slash commands synced.")


# Initialize bot with prefix from config, required intents
intents = discord.Intents.default()
intents.members = True  # For member join events, etc.
intents.message_content = True  # For reading message content in commands

bot = MyBot(command_prefix=PREFIX, intents=intents)

# Remove default help command to replace with a custom one
bot.remove_command("help")


# Custom help command that dynamically lists commands
@bot.hybrid_command(name="help", description="Displays available commands")
async def help_command(ctx):
    """
    Custom help command that lists all available commands dynamically.
    Groups commands by cog for better organization.
    """
    embed = discord.Embed(title="Bot Commands", color=discord.Color.green())
    for cog_name, cog in bot.cogs.items():
        commands_list = [cmd.name for cmd in cog.get_commands() if not cmd.hidden]
        if commands_list:
            embed.add_field(name=cog_name, value=", ".join(commands_list), inline=False)
    await ctx.send(embed=embed)


# Event: On ready, print bot info and guilds
@bot.event
async def on_ready():
    # Cool startup banner
    banner = """
    ╔════════════════════════════════════════╗
    ║          Discord Bot Started!          ║
    ╚════════════════════════════════════════╝
    """
    print(banner)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Connected to guilds:")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    logger.info(f"Bot ready and connected to {len(bot.guilds)} guilds.")


# Event: Log command usage
@bot.event
async def on_command(ctx):
    logger.info(
        f'Command used: {ctx.command.name} by {ctx.author} in {ctx.guild.name if ctx.guild else "DM"}'
    )


# Error handling: Graceful error responses without exposing details
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore silently
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You lack permissions for this command.", ephemeral=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid arguments provided.", ephemeral=True)
    else:
        await ctx.send("An error occurred. Please try again later.", ephemeral=True)
    logger.error(f"Error in command {ctx.command}: {error}", exc_info=True)


# Run the bot using token from environment variable (secure, no hardcoding)
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not set in environment variables.")
    bot.run(token)
