# features/hello.py
"""
Example Cog: Hello

Demonstrates a simple hybrid command (works as both prefix and slash).
This is a self-contained module; adding it to features/ auto-loads it.

How to add a new Cog:
1. Create a new .py file in features/ (e.g., myfeature.py).
2. Define a class that inherits from commands.Cog.
3. Add __init__(self, bot) to store self.bot.
4. Define commands with @commands.hybrid_command() for prefix + slash support.
5. For event listeners, use @commands.Cog.listener().
6. The bot will auto-load it on startup.

For slash commands: Use @app_commands.describe() for param descriptions.
For DM responses: Use await interaction.user.send() in interactions.
"""

import discord
from discord.ext import commands


class Hello(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="hello", description="Says hello back")
    async def hello(self, ctx: commands.Context):
        """
        Simple command example.
        Supports both !hello (prefix) and /hello (slash).
        """
        await ctx.send(
            f"Hello, {ctx.author.mention}!", ephemeral=True
        )  # Ephemeral for private reply


async def setup(bot):
    await bot.add_cog(Hello(bot))
