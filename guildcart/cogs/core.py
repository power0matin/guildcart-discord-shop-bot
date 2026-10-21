"""Shared help command and core Discord event handlers."""
import logging
import discord
from discord.ext import commands

logger = logging.getLogger("guildcart")

class CoreCog(commands.Cog):
    """Commands and event handlers shared by all feature cogs."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", description="Displays available commands")
    async def help_command(self, ctx: commands.Context) -> None:
        embed = discord.Embed(title="GuildCart commands", color=discord.Color.green())
        for cog_name, cog in self.bot.cogs.items():
            names = sorted(command.name for command in cog.get_commands() if not command.hidden)
            if names:
                embed.add_field(name=cog_name, value=", ".join(names), inline=False)
        if not embed.fields:
            embed.description = "No commands are currently available."
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        user = self.bot.user
        logger.info("Connected as %s (%s)", user, user.id if user else "unknown")
        logger.info(
            "Connected to %s guild(s): %s",
            len(self.bot.guilds),
            ", ".join(f"{guild.name} ({guild.id})" for guild in self.bot.guilds),
        )

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        logger.info("Command used: %s by %s in %s",
                    ctx.command.qualified_name if ctx.command else "<unknown>",
                    ctx.author, ctx.guild.name if ctx.guild else "DM")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            message = "You lack permissions for this command."
        elif isinstance(error, commands.BadArgument):
            message = "Invalid arguments provided."
        else:
            message = "An error occurred. Please try again later."
        kwargs = {"ephemeral": True} if ctx.interaction is not None else {}
        await ctx.send(message, **kwargs)
        logger.error("Command error in %s: %s",
                     ctx.command.qualified_name if ctx.command else "<unknown>",
                     error, exc_info=(type(error), error, error.__traceback__))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoreCog(bot))

__all__ = ["CoreCog", "setup"]
