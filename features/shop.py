# filename: shop_cog.py
"""
Discord Shop Cog with ticket creation & payment modal.
Dependencies:
  - discord.py 2.0+ (pip install -U discord.py)
  - python-dotenv (pip install python-dotenv)

Includes small testable helpers at the bottom with pytest tests.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Optional, Tuple

import discord
from discord import TextStyle
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, View
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# Configuration (read from env with safe defaults)
CATEGORY_NAME = os.getenv("CATEGORY_NAME", "tickets")
ADMIN_CHANNEL_NAME = os.getenv("ADMIN_CHANNEL_NAME", "admin-payments")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admins")
CARD_NUMBER = os.getenv("CARD_NUMBER", "**** **** **** 4242")

# Validate minimal config
if not CATEGORY_NAME:
    CATEGORY_NAME = "tickets"
if not ADMIN_CHANNEL_NAME:
    ADMIN_CHANNEL_NAME = "admin-payments"
if not ADMIN_ROLE_NAME:
    ADMIN_ROLE_NAME = "Admins"

# Logging setup
logger = logging.getLogger("shop_ticket_payment")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
_handler = logging.StreamHandler()
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
)
if not logger.handlers:
    logger.addHandler(_handler)


# --- Helper functions (testable) ---
def parse_plan_label(selected_label: str) -> Tuple[str, str]:
    """
    Parse a label like "⚡10GB – 40T" into ("⚡10GB", "40T").
    Works with common dash characters (hyphen, en-dash, em-dash).
    If no separator found, returns (selected_label, "N/A").
    """
    if not selected_label:
        return ("N/A", "N/A")

    # Normalize various dash characters to a single separator
    normalized = re.sub(r"[—–-]+", "–", selected_label)
    parts = normalized.split("–", 1)
    left = parts[0].strip()
    right = parts[1].strip() if len(parts) > 1 else "N/A"
    return left, right


def sanitize_channel_name(name: str, max_len: int = 90) -> str:
    """
    Create a safe channel name:
      - Lowercase
      - Replace spaces and invalid chars with '-'
      - Trim to max_len and avoid leading/trailing '-'
    Discord channel name limit is 100 chars, use 90 for safety.
    """
    if not name:
        return "ticket"
    # Keep letters, numbers, hyphens and underscores; replace others with '-'
    sanitized = re.sub(r"[^a-zA-Z0-9-_]+", "-", name)
    sanitized = sanitized.strip("-").lower()
    # Collapse multiple hyphens
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    return sanitized[:max_len].rstrip("-")


# --- Modal for payment collection ---
class PaymentModal(Modal):
    """
    Modal to collect last4, amount and optional tx id.
    """

    def __init__(self, plan_label: str, price_label: str, ticket_channel_id: int):
        super().__init__(title="Sabt Pardakht")
        self.plan_label = plan_label
        self.price_label = price_label
        self.ticket_channel_id = ticket_channel_id

        # Inputs: last 4 digits, amount, tx/description
        self.last4 = TextInput(
            label="4 ragham akhar kart",
            placeholder="1234",
            min_length=4,
            max_length=4,
            required=True,
        )
        self.amount = TextInput(
            label="Mablagh (amount)",
            placeholder=f"mesal: {price_label}",
            min_length=1,
            required=True,
        )
        self.tx = TextInput(
            label="Tx ID / Description (optional)",
            style=TextStyle.long,
            required=False,
            max_length=512,
        )

        # Add inputs to modal
        self.add_item(self.last4)
        self.add_item(self.amount)
        self.add_item(self.tx)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Validate inputs and notify admin channel + confirm to user.
        """
        last4_val = (self.last4.value or "").strip()
        amount_raw = (self.amount.value or "").strip()
        tx_val = (self.tx.value or "").strip() or "N/A"

        # Validate last4
        if not last4_val.isdigit() or len(last4_val) != 4:
            await interaction.response.send_message(
                "⚠️ 'Last4' باید دقیقاً ۴ رقم عددی باشد.", ephemeral=True
            )
            return

        # Validate amount
        try:
            amount_val = float(amount_raw.replace(",", "."))
            if amount_val <= 0:
                raise ValueError("Amount must be positive")
        except Exception:
            await interaction.response.send_message(
                "⚠️ مقدار مبلغ نامعتبر است. لطفاً عدد مثبتی وارد کنید.", ephemeral=True
            )
            return

        # Defer response to allow followup sending
        await interaction.response.defer(ephemeral=True)

        # Confirm to user (don't log sensitive last4)
        await interaction.followup.send(
            (
                f"✅ پرداخت شما ثبت شد!\n"
                f"Plan: **{self.plan_label}** | Price: **{self.price_label}**\n"
                f"Amount: **{amount_val}T** | Last4: ******{last4_val[-4:]}**\n"
                f"Tx/Desc: {tx_val}"
            ),
            ephemeral=True,
        )

        # Prepare admin notification
        guild = interaction.guild
        if not guild:
            logger.error("PaymentModal: interaction.guild is None")
            return

        admin_channel = discord.utils.get(guild.text_channels, name=ADMIN_CHANNEL_NAME)
        admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)

        if admin_channel:
            try:
                mention_text = admin_role.mention if admin_role else ""
                admin_embed = discord.Embed(
                    title="💳 Pardakht Jadid",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                admin_embed.add_field(
                    name="User", value=interaction.user.mention, inline=True
                )
                admin_embed.add_field(name="Plan", value=self.plan_label, inline=True)
                admin_embed.add_field(name="Price", value=self.price_label, inline=True)
                admin_embed.add_field(
                    name="Amount", value=f"{amount_val}T", inline=True
                )
                admin_embed.add_field(
                    name="Last4", value=f"****{last4_val}", inline=True
                )
                admin_embed.add_field(name="Tx/Desc", value=tx_val, inline=False)
                await admin_channel.send(content=mention_text, embed=admin_embed)
                logger.info(
                    "Notified admin channel about payment (user=%s, plan=%s, amount=%s).",
                    interaction.user,
                    self.plan_label,
                    amount_val,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to send payment embed to admin channel: %s", exc
                )
        else:
            logger.warning(
                "Admin channel '%s' not found in guild %s. Payment not announced to admins.",
                ADMIN_CHANNEL_NAME,
                guild.name,
            )


# --- Cog that provides the /shop command ---
class ShopCog(commands.Cog):
    """Shop cog with a /shop hybrid command that opens a plan selector and creates tickets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ Show shop embed and plans")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context) -> None:
        """Send the shop embed with plan selector and support links."""
        embed = discord.Embed(
            title="💎 HyperShield | High Speed Servers",
            description=(
                "🚀 **چرا HyperShield؟**\n"
                "- سرورهای anti-filter با پینگ پایین\n"
                "- پشتیبانی ۲۴/۷ از طریق Telegram\n"
                "- تست رایگان ۲۴ ساعته\n"
                "- پرداخت امن با کارت و کریپتو\n\n"
                "📱 Channel Telegram: [Shop HyperShield](https://t.me/Shop_HyperSheild)"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="🌐 HyperShield — Speed ⚡ Security")
        embed.add_field(
            name="🔥 Tunnel",
            value=(
                "**10GB** – 40T\n"
                "**20GB** – 65T\n"
                "**30GB** – 90T\n"
                "**40GB** – 130T\n"
                "**50GB** – 160T\n"
                "**60GB** – 190T"
            ),
            inline=True,
        )
        embed.add_field(
            name="⚡ Unlimited",
            value=(
                "**80GB** – 210T\n"
                "**100GB** – 260T\n"
                "**150GB** – 390T\n"
                "**200GB** – 520T"
            ),
            inline=True,
        )
        embed.add_field(
            name="🌐 Premium (ویژه)",
            value=(
                "**10GB** – 80T\n"
                "**20GB** – 160T\n"
                "**30GB** – 240T\n"
                "**40GB** – 320T\n"
                "**50GB** – 400T"
            ),
            inline=True,
        )

        view = View(timeout=None)

        # Link buttons
        view.add_item(
            Button(
                label="📱 Telegram Channel",
                style=discord.ButtonStyle.link,
                url="https://t.me/Shop_HyperSheild",
            )
        )
        view.add_item(
            Button(
                label="🧑‍💻 Support",
                style=discord.ButtonStyle.link,
                url="https://t.me/Assistant_HyperShield",
            )
        )

        # Plan select
        options = [
            discord.SelectOption(label="⚡10GB – 40T", value="10g"),
            discord.SelectOption(label="⚡20GB – 65T", value="20g"),
            discord.SelectOption(label="⚡30GB – 90T", value="30g"),
            discord.SelectOption(label="⚡40GB – 130T", value="40g"),
            discord.SelectOption(label="⚡50GB – 160T", value="50g"),
            discord.SelectOption(label="⚡60GB – 190T", value="60g"),
            discord.SelectOption(label="⚡80GB – 210T", value="80g"),
            discord.SelectOption(label="⚡100GB – 260T", value="100g"),
            discord.SelectOption(label="⚡150GB – 390T", value="150g"),
            discord.SelectOption(label="⚡200GB – 520T", value="200g"),
        ]
        select = Select(
            placeholder="📦 Yek plan entekhab konid...",
            options=options,
            min_values=1,
            max_values=1,
        )

        # Callback for the select
        async def select_cb(interaction: discord.Interaction) -> None:
            try:
                # Basic safety checks
                values = interaction.data.get("values") if interaction.data else None
                if not values:
                    await interaction.response.send_message(
                        "⚠️ No plan selected.", ephemeral=True
                    )
                    return

                selected_value = values[0]
                # find the matching option label
                selected_label = next(
                    (
                        opt.label
                        for opt in select.options
                        if opt.value == selected_value
                    ),
                    None,
                )
                if not selected_label:
                    await interaction.response.send_message(
                        "⚠️ Selected plan not recognized.", ephemeral=True
                    )
                    return

                plan_label, price_label = parse_plan_label(selected_label)

                guild = interaction.guild
                author = interaction.user
                if not guild or not author:
                    await interaction.response.send_message(
                        "⚠️ Cannot create ticket here.", ephemeral=True
                    )
                    return

                # Ensure category exists (create if missing)
                category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
                if category is None:
                    try:
                        perms = {
                            guild.default_role: discord.PermissionOverwrite(
                                view_channel=False
                            )
                        }
                        category = await guild.create_category(
                            CATEGORY_NAME, overwrites=perms
                        )
                        logger.info(
                            "Created category %s in guild %s", CATEGORY_NAME, guild.name
                        )
                    except Exception as exc:
                        logger.exception("Failed to create category: %s", exc)
                        await interaction.response.send_message(
                            "⚠️ خطا در ساختن کانال دسته‌بندی تیکت. لطفاً ادمین را مطلع کنید.",
                            ephemeral=True,
                        )
                        return

                # Build channel name safely
                safe_name = sanitize_channel_name(
                    f"ticket-{author.name}-{author.discriminator}"
                )
                # Build permission overwrites
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    author: discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, read_message_history=True
                    ),
                }
                bot_member = guild.get_member(self.bot.user.id) or guild.me
                if bot_member:
                    overwrites[bot_member] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )
                admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
                if admin_role:
                    overwrites[admin_role] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )

                # Create channel
                try:
                    ticket_channel = await guild.create_text_channel(
                        name=safe_name,
                        category=category,
                        overwrites=overwrites,
                        reason=f"Ticket for {author} (plan {selected_label})",
                    )
                except Exception as exc:
                    logger.exception("Failed to create ticket channel: %s", exc)
                    await interaction.response.send_message(
                        "⚠️ خطا در ساختن کانال تیکت. لطفاً از امکان ساختن کانال توسط بات اطمینان حاصل کنید.",
                        ephemeral=True,
                    )
                    return

                # Ticket embed and view
                ticket_embed = discord.Embed(
                    title="🎫 HyperShield | Ticket",
                    description=(
                        f"✅ شما طرح **{selected_label}** را انتخاب کردید.\n"
                        f"💳 کارت برای واریز: **{CARD_NUMBER}**\n"
                        "📸 لطفاً تصویر رسید/پرداخت را ارسال کنید یا از قسمت ثبت پرداخت استفاده کنید."
                    ),
                    timestamp=datetime.utcnow(),
                )
                pay_button = Button(
                    label="💳 Sabt Pardakht", style=discord.ButtonStyle.primary
                )

                async def pay_cb(btn_interaction: discord.Interaction) -> None:
                    # Ensure same user opens the modal (optional check could be added)
                    try:
                        await btn_interaction.response.send_modal(
                            PaymentModal(
                                plan_label=plan_label,
                                price_label=price_label,
                                ticket_channel_id=ticket_channel.id,
                            )
                        )
                    except discord.errors.InteractionResponded:
                        # If already responded elsewhere, fallback to ephemeral message
                        await btn_interaction.followup.send(
                            "⚠️ modal قبلاً باز شده است.", ephemeral=True
                        )
                    except Exception as exc:
                        logger.exception("Failed to show payment modal: %s", exc)
                        await btn_interaction.response.send_message(
                            "⚠️ خطایی رخ داد.", ephemeral=True
                        )

                pay_button.callback = pay_cb
                ticket_view = View(timeout=None)
                ticket_view.add_item(pay_button)

                # Send to ticket channel
                await ticket_channel.send(
                    content=f"👋 Salam {author.mention}!",
                    embed=ticket_embed,
                    view=ticket_view,
                )

                # Notify admin channel (if exists)
                admin_channel = discord.utils.get(
                    guild.text_channels, name=ADMIN_CHANNEL_NAME
                )
                if admin_channel:
                    mention_text = admin_role.mention if admin_role else ""
                    admin_embed = discord.Embed(
                        title="🚨 Ticket Jadid",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow(),
                    )
                    admin_embed.add_field(
                        name="User", value=author.mention, inline=True
                    )
                    admin_embed.add_field(name="Plan", value=plan_label, inline=True)
                    admin_embed.add_field(
                        name="Channel", value=ticket_channel.mention, inline=False
                    )
                    try:
                        await admin_channel.send(
                            content=mention_text, embed=admin_embed
                        )
                    except Exception:
                        logger.exception(
                            "Failed to notify admin channel about new ticket."
                        )
                else:
                    logger.warning(
                        "Admin channel '%s' not found in guild %s.",
                        ADMIN_CHANNEL_NAME,
                        guild.name,
                    )

                # Final ephemeral confirmation to the user who triggered select
                await interaction.followup.send(
                    f"🎟️ Ticket برای طرح **{selected_label}** ساخته شد: {ticket_channel.mention}",
                    ephemeral=True,
                )

            except Exception as exc:
                logger.exception("Unhandled error in select_cb: %s", exc)
                try:
                    await interaction.response.send_message(
                        "⚠️ خطای داخلی رخ داد.", ephemeral=True
                    )
                except Exception:
                    # Already responded; try followup
                    try:
                        await interaction.followup.send(
                            "⚠️ خطای داخلی رخ داد.", ephemeral=True
                        )
                    except Exception:
                        logger.exception("Failed to inform user about internal error.")

        select.callback = select_cb
        view.add_item(select)

        # Send the embed and view
        await ctx.send(embed=embed, view=view)


# Cog loader for modern discord.py
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShopCog(bot))


# --- Unit tests for helper functions (pytest) ---
# Save this portion as tests/test_shop_helpers.py and run `pytest` to run these.
# For convenience, included here. If you prefer separate file, move tests to tests/ folder.

if __name__ == "__main__":  # quick local-run check
    # Basic smoke test for helpers
    assert parse_plan_label("⚡10GB – 40T") == ("⚡10GB", "40T")
    assert parse_plan_label("NoDashLabel") == ("NoDashLabel", "N/A")
    assert sanitize_channel_name("ticket-Matin#1234")  # should not raise
    print("Sanity checks passed.")
