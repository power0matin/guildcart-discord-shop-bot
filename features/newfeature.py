# Template for new features (save as features/newfeature.py)
"""
Template for a new Cog.

Copy this to features/<name>.py and customize.
The bot auto-loads it via bot.py.

Includes examples for:
- Hybrid commands (prefix + slash).
- Event listeners.
- Buttons with DM response.
- Error handling in commands.
- Role checks.
- Async operations.

For database: Import json or aiosqlite, use in commands.
For utils: Create utils/ folder with helpers, import here.
"""

import discord
from discord.ext import commands
from discord import app_commands

class NewFeature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Example hybrid command with param and role check
    @commands.hybrid_command(name='newcmd', description='Does something new')
    @commands.has_permissions(manage_messages=True)  # Optional role-based permission
    @app_commands.describe(arg='An argument')
    async def newcmd(self, ctx: commands.Context, arg: str):
        # Sanitize input
        sanitized = discord.utils.escape_mentions(arg)
        await ctx.send(f'You said: {sanitized}', ephemeral=True)

    # Example button interaction with DM
    @commands.hybrid_command(name='buttondm', description='Sends a button that DMs on click')
    async def buttondm(self, ctx: commands.Context):
        view = discord.ui.View()
        button = discord.ui.Button(label='Click for DM', style=discord.ButtonStyle.secondary)

        async def button_callback(interaction: discord.Interaction):
            await interaction.user.send('This is a private DM response!')
            await interaction.response.send_message('DM sent!', ephemeral=True)

        button.callback = button_callback
        view.add_item(button)
        await ctx.send('Click the button:', view=view)

    # Example event listener
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Welcome with embed and button
        embed = discord.Embed(title=f'Welcome {member.name}!', color=discord.Color.green())
        view = discord.ui.View()
        button = discord.ui.Button(label='Support', url='https://example.com/support')
        view.add_item(button)
        channel = member.guild.system_channel
        if channel:
            await channel.send(embed=embed, view=view)

    # Error handling in cog (optional, supplements global handler)
    async def cog_command_error(self, ctx: commands.Context, error):
        await ctx.send('Feature-specific error occurred.', ephemeral=True)

async def setup(bot):
    await bot.add_cog(NewFeature(bot))