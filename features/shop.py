# features/shop.py
"""
Example Cog: Shop

Demonstrates rich embeds, buttons (for direct links), select menus (for plan selection),
and DM responses on interaction.

- Embeds: Use discord.Embed() with title, fields, color, thumbnail, footer.
- Buttons: discord.ui.Button() with label, url (for direct links) or custom_id for callbacks.
- Select Menus: discord.ui.Select() with options, callback for handling selection.
- Interactions: Handle with async callback, use interaction.response.send_message(ephemeral=True) for feedback.
- DM: await interaction.user.send() for private messages.

This cog is self-contained and auto-loaded.
For production: Handle rate limits with try-except on interactions.
For persistent data: Use JSON in data/ or a DB.
"""

import discord
from discord.ext import commands
from discord import app_commands

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='shop', description='Displays the shop with plans and buy options')
    async def shop(self, ctx: commands.Context):
        """
        Shop command example.
        Sends an embed with buttons and select menu.
        On select, sends DM with details and ephemeral confirmation.
        """
        # Rich embed with dynamic content
        embed = discord.Embed(
            title='Bot Shop',
            description='Choose a plan or buy directly!',
            color=discord.Color.blue()
        )
        embed.add_field(name='Basic Plan', value='$10/month - Essential features', inline=False)
        embed.add_field(name='Pro Plan', value='$20/month - Advanced tools', inline=False)
        embed.set_thumbnail(url='https://example.com/thumbnail.png')  # Replace with real URL
        embed.set_footer(text='Shop powered by xAI')

        # View for buttons and selects
        view = discord.ui.View(timeout=None)  # Persistent view (no timeout for production)

        # Button for direct link (e.g., purchase page)
        buy_button = discord.ui.Button(
            label='Buy Now',
            style=discord.ButtonStyle.primary,
            url='https://example.com/purchase'  # Direct link to external site
        )
        view.add_item(buy_button)

        # Select menu for plan selection
        select = discord.ui.Select(
            placeholder='Select a plan...',
            options=[
                discord.SelectOption(label='Basic', value='basic', description='$10/month'),
                discord.SelectOption(label='Pro', value='pro', description='$20/month')
            ]
        )

        # Callback for select menu (async handling)
        async def select_callback(interaction: discord.Interaction):
            selected = interaction.data['values'][0]
            # DM private details
            await interaction.user.send(f'You selected the {selected.capitalize()} plan! Details: ...')
            # Ephemeral feedback
            await interaction.response.send_message('Plan details sent to your DM!', ephemeral=True)

        select.callback = select_callback
        view.add_item(select)

        # Send the message with embed and view
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Shop(bot))