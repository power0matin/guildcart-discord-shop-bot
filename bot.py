import discord
from discord.ext import commands
import os
import logging
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

# Explicitly list Discord Cogs. Helper modules such as order_store.py and
# plan_utils.py are imported by the shop Cog but are not Discord extensions.
COG_MODULES = ("features.shop",)


class MyBot(commands.Bot):
    async def setup_hook(self):
        for cog_name in COG_MODULES:
            try:
                await self.load_extension(cog_name)
                logger.info("Loaded cog: %s", cog_name)
            except Exception as exc:
                logger.exception("Failed to load required cog %s", cog_name)
                raise RuntimeError(
                    f"Could not load required extension {cog_name}; "
                    "see the preceding error for details."
                ) from exc

        # Global command sync remains for the prototype; the roadmap tracks a
        # safer per-guild sync path for development.
        await self.tree.sync()
        logger.info("Slash commands synced.")


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = MyBot(command_prefix=PREFIX, intents=intents)
bot.remove_command("help")


@bot.hybrid_command(name="help", description="Displays available commands")
async def help_command(ctx):
    """List available commands, grouped by cog."""
    embed = discord.Embed(title="Bot Commands", color=discord.Color.green())
    for cog_name, cog in bot.cogs.items():
        commands_list = [cmd.name for cmd in cog.get_commands() if not cmd.hidden]
        if commands_list:
            embed.add_field(
                name=cog_name, value=", ".join(commands_list), inline=False
            )
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
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
    logger.info("Bot ready and connected to %s guilds.", len(bot.guilds))


@bot.event
async def on_command(ctx):
    logger.info(
        "Command used: %s by %s in %s",
        ctx.command.name,
        ctx.author,
        ctx.guild.name if ctx.guild else "DM",
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You lack permissions for this command.", ephemeral=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid arguments provided.", ephemeral=True)
    else:
        await ctx.send("An error occurred. Please try again later.", ephemeral=True)
    logger.error("Error in command %s: %s", ctx.command, error, exc_info=True)


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not set in environment variables.")
    bot.run(token)
