import os
import json
import logging
import random
from datetime import datetime

import discord
from discord import TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, Button, View
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CATEGORY_NAME = os.getenv("CATEGORY_NAME", "tickets")
ADMIN_CHANNEL_NAME = os.getenv("ADMIN_CHANNEL_NAME", "admin-notify")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")

# Payment settings
CARD_NUMBER = os.getenv("CARD_NUMBER", "**** **** **** 4242")
PAYMENT_TIMEOUT_MINUTES = int(os.getenv("PAYMENT_TIMEOUT_MINUTES", 30))
PAYMENTS_DB = os.getenv("PAYMENTS_DB", "data/payments.db")
CRYPTO_ADDRESS_USDT = os.getenv("CRYPTO_ADDRESS_USDT", "")

# Ticket settings
TICKET_NAME_TEMPLATE = os.getenv("TICKET_NAME_TEMPLATE", "ticket-{author}-{rand6}")

# Shop texts
SHOP_TITLE = os.getenv("SHOP_TITLE", "💎 HyperShield | High Speed Servers")
SHOP_DESCRIPTION = os.getenv("SHOP_DESCRIPTION", "")
SHOP_FOOTER = os.getenv("SHOP_FOOTER", "")

# Telegram links
TELEGRAM_SHOP_URL = os.getenv("TELEGRAM_SHOP_URL", "")
TELEGRAM_SUPPORT_URL = os.getenv("TELEGRAM_SUPPORT_URL", "")

# Button labels
BTN_SHOP_LABEL = os.getenv("BTN_SHOP_LABEL", "📱 Telegram Channel")
BTN_SUPPORT_LABEL = os.getenv("BTN_SUPPORT_LABEL", "🧑‍💻 Support")
BTN_PAY_LABEL = os.getenv("BTN_PAY_LABEL", "💳 Sabt Pardakht")
BTN_CLOSE_LABEL = os.getenv("BTN_CLOSE_LABEL", "🔒 Bastan Ticket")

# Load plan options from config.json
PLAN_OPTIONS = []
try:
    with open("config.json", "r", encoding="utf-8") as f:
        for item in json.load(f)["plans"]:
            PLAN_OPTIONS.append(
                discord.SelectOption(label=item["label"], value=item["value"])
            )
except Exception as e:
    print(f"⚠️ Failed to load config.json: {e}")

# Logging setup
logger = logging.getLogger("shop_ticket_payment")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


def generate_ticket_name(author):
    """Generate a ticket name based on template in .env"""
    return TICKET_NAME_TEMPLATE.format(
        author=author.name, rand6=random.randint(100000, 999999)
    )


class PaymentModal(Modal):
    """Modal for registering payment details."""

    def __init__(self, plan_label: str, price_label: str, ticket_channel_id: int):
        super().__init__(title=BTN_PAY_LABEL)
        self.plan_label = plan_label
        self.price_label = price_label
        self.ticket_channel_id = ticket_channel_id

        self.last4 = TextInput(
            label="4 ragham akhar kart",
            placeholder="1234",
            min_length=4,
            max_length=4,
            required=True,
        )
        self.owner = TextInput(
            label="name saheb kart",
            placeholder="ali rezaei",
            min_length=2,
            max_length=35,
            required=True,
        )
        self.amount = TextInput(
            label="Mablagh (amount)",
            placeholder=f"mesal: {price_label[:-1]}",  # Remove 'T' for clarity
            min_length=1,
            required=True,
        )
        self.tx = TextInput(
            label="Tx ID / Description (optional)", required=False, style=TextStyle.long
        )

        self.add_item(self.last4)
        self.add_item(self.amount)
        self.add_item(self.owner)
        self.add_item(self.tx)

    async def on_submit(self, interaction: discord.Interaction):
        last4_val = self.last4.value.strip()
        amount_raw = self.amount.value.strip().rstrip("Tt")
        tx_val = self.tx.value.strip() or "N/A"

        # Validate last4
        if not last4_val.isdigit() or len(last4_val) != 4:
            await interaction.response.send_message(
                "⚠️ Last4 bayad 4 ragham numeric bashe.", ephemeral=True
            )
            return

        # Validate amount
        try:
            amount_val = float(amount_raw)
            if amount_val <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await interaction.response.send_message(
                "⚠️ Mablagh ghalat ast. Lotfan adad vared konid (mesal: 40).",
                ephemeral=True,
            )
            return

        # Check if amount matches expected
        expected_price = float(self.price_label.rstrip("Tt"))
        if amount_val != expected_price:
            await interaction.response.send_message(
                f"⚠️ Mablagh vared shode ({amount_val}T) ba gheymat plan ({self.price_label}) motabeghat nadarad.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Confirm to user
        await interaction.followup.send(
            f"✅ Pardakht shoma sabt shod!\n"
            f"User: {self.owner}\n"
            f"Plan: **{self.plan_label}** | Price: **{self.price_label}**\n"
            f"Amount: **{amount_val}T** | Last4: **{last4_val}**\nTx/Desc: {tx_val}",
            ephemeral=True,
        )

        # Notify admin
        admin_channel = discord.utils.get(
            interaction.guild.text_channels, name=ADMIN_CHANNEL_NAME
        )
        admin_role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)

        if admin_channel:
            mention_text = admin_role.mention if admin_role else ""
            admin_embed = discord.Embed(
                title="💳 Pardakht Jadid",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )
            admin_embed.add_field(
                name="User", value=interaction.user.mention, inline=True
            )
            admin_embed.add_field(name="Card Owner", value=self.owner, inline=True)
            admin_embed.add_field(name="Plan", value=self.plan_label, inline=True)
            admin_embed.add_field(name="Price", value=self.price_label, inline=True)
            admin_embed.add_field(name="Amount", value=f"{amount_val}T", inline=True)
            admin_embed.add_field(name="Last4", value=last4_val, inline=True)
            admin_embed.add_field(name="Tx/Desc", value=tx_val, inline=False)

            await admin_channel.send(content=mention_text, embed=admin_embed)


class ShopCog(commands.Cog):
    """Cog for handling shop commands and interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ Show shop embed and plans")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title=SHOP_TITLE,
            description=SHOP_DESCRIPTION,
            color=discord.Color.blue(),
        )
        embed.set_footer(text=SHOP_FOOTER)

        view = View(timeout=None)

        # Buttons from .env
        if TELEGRAM_SHOP_URL:
            view.add_item(
                Button(
                    label=BTN_SHOP_LABEL,
                    style=discord.ButtonStyle.link,
                    url=TELEGRAM_SHOP_URL,
                )
            )
        if TELEGRAM_SUPPORT_URL:
            view.add_item(
                Button(
                    label=BTN_SUPPORT_LABEL,
                    style=discord.ButtonStyle.link,
                    url=TELEGRAM_SUPPORT_URL,
                )
            )

        # Select from config.json
        select = Select(
            placeholder="📦 Yek plan entekhab konid...", options=PLAN_OPTIONS
        )

        async def select_cb(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            selected_value = interaction.data["values"][0]
            selected_label = next(
                opt.label for opt in select.options if opt.value == selected_value
            )

            plan_label, price_label = (
                (
                    selected_label.split("–")[0].strip()[1:],
                    selected_label.split("–")[1].strip(),
                )
                if "–" in selected_label
                else (selected_label, "N/A")
            )

            guild = interaction.guild
            author = interaction.user
            category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

            if category is None:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(view_channel=True),
                }
                category = await guild.create_category(
                    CATEGORY_NAME, overwrites=overwrites
                )

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                author: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_messages=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_messages=True
                ),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_messages=True
                )

            ticket_name = generate_ticket_name(author)
            ticket_channel = await category.create_text_channel(
                name=ticket_name,
                overwrites=overwrites,
                reason=f"Ticket for {author.name} ({author.id})",
            )

            ticket_embed = discord.Embed(
                title="🎫 HyperShield | Ticket",
                description=f"✅ Shoma plan **{selected_label}** ro entekhab kardi.\n💳 **{CARD_NUMBER}**\n📸 Tasvir pardakht ro ersal konid.",
                timestamp=datetime.utcnow(),
            )

            ticket_view = View(timeout=None)

            pay_button = Button(label=BTN_PAY_LABEL, style=discord.ButtonStyle.primary)

            async def pay_cb(btn_interaction: discord.Interaction):
                if btn_interaction.user.id != author.id:
                    await btn_interaction.response.send_message(
                        "⚠️ Faghat sakht ticket mitavanad az in dokme estefade konad.",
                        ephemeral=True,
                    )
                    return
                await btn_interaction.response.send_modal(
                    PaymentModal(plan_label, price_label, ticket_channel.id)
                )

            pay_button.callback = pay_cb
            ticket_view.add_item(pay_button)

            close_button = Button(
                label=BTN_CLOSE_LABEL, style=discord.ButtonStyle.danger
            )

            async def close_cb(close_interaction: discord.Interaction):
                if close_interaction.user.id != author.id and not any(
                    role.name == ADMIN_ROLE_NAME
                    for role in close_interaction.user.roles
                ):
                    await close_interaction.response.send_message(
                        "⚠️ Faghat sakht ya admin mitavanad ticket ra bebandad.",
                        ephemeral=True,
                    )
                    return
                await close_interaction.response.defer()
                await ticket_channel.delete(reason="Ticket closed by user or admin")

            close_button.callback = close_cb
            ticket_view.add_item(close_button)

            await ticket_channel.send(
                content=f"👋 Salam {author.mention}!",
                embed=ticket_embed,
                view=ticket_view,
            )

        select.callback = select_cb
        view.add_item(select)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
