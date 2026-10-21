"""Discord shop Cog: catalogue UI, tickets, and manual order review."""

import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import discord
from discord import TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, Button, View

from guildcart.domain.plans import parse_amount, parse_plan_label, validate_plans
from guildcart.settings import Settings, load_plan_entries
from guildcart.storage.order_store import (
    PAID, REJECTED, OrderNotFoundError, OrderStateError, OrderStore,
)

SETTINGS = Settings.from_environment()
CATEGORY_NAME = SETTINGS.category_name
ADMIN_CHANNEL_NAME = SETTINGS.admin_channel_name
ADMIN_ROLE_NAME = SETTINGS.admin_role_name
PAYMENT_TIMEOUT_MINUTES = SETTINGS.payment_timeout_minutes
PAYMENTS_DB = SETTINGS.payments_db
CARD_NUMBER = SETTINGS.card_number
CRYPTO_ADDRESS_USDT = SETTINGS.crypto_address_usdt
TICKET_NAME_TEMPLATE = SETTINGS.ticket_name_template
SHOP_TITLE = SETTINGS.shop_title
SHOP_DESCRIPTION = SETTINGS.shop_description
SHOP_FOOTER = SETTINGS.shop_footer
TELEGRAM_SHOP_URL = SETTINGS.telegram_shop_url
TELEGRAM_SUPPORT_URL = SETTINGS.telegram_support_url
BTN_SHOP_LABEL = SETTINGS.btn_shop_label
BTN_SUPPORT_LABEL = SETTINGS.btn_support_label
BTN_PAY_LABEL = SETTINGS.btn_pay_label
BTN_CLOSE_LABEL = SETTINGS.btn_close_label

PLAN_OPTIONS = [
    discord.SelectOption(label=item["label"], value=item["value"])
    for item in load_plan_entries(SETTINGS.config_path)
]


@lru_cache(maxsize=4)
def get_order_store(db_path: str | Path = PAYMENTS_DB) -> OrderStore:
    """Return a cached SQLite repository for a database path."""
    return OrderStore(db_path)


def _store_call(db_path: str | Path, method_name: str, **kwargs):
    """Call a repository method from asyncio.to_thread."""
    return getattr(get_order_store(str(db_path)), method_name)(**kwargs)


logger = logging.getLogger("shop_ticket_payment")
logger.setLevel(logging.INFO)
if not any(getattr(handler, "_guildcart_shop_handler", False) for handler in logger.handlers):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
    handler._guildcart_shop_handler = True
    logger.addHandler(handler)


def generate_ticket_name(author, template: str = TICKET_NAME_TEMPLATE):
    """Generate a ticket name from the configured template."""
    return template.format(author=author.name, rand6=random.randint(100000, 999999))


def is_shop_admin(member, admin_role_name: str = ADMIN_ROLE_NAME) -> bool:
    """Check permissions when every privileged order action is invoked."""
    permissions = getattr(member, "guild_permissions", None)
    if permissions and permissions.administrator:
        return True
    return any(role.name == admin_role_name for role in getattr(member, "roles", ()))


async def send_context(ctx: commands.Context, *args, **kwargs):
    """Use ephemeral replies for interactions without breaking prefix commands."""
    if ctx.interaction is None:
        kwargs.pop("ephemeral", None)
    return await ctx.send(*args, **kwargs)


async def notify_customer(guild: discord.Guild, order, message: str) -> None:
    """Best-effort DM; delivery failure must not undo the saved review decision."""
    member = guild.get_member(order.customer_id)
    if member is None:
        try:
            member = await guild.fetch_member(order.customer_id)
        except discord.HTTPException:
            logger.info("Could not resolve customer for order %s", order.order_id)
            return
    try:
        await member.send(message)
    except discord.HTTPException:
        logger.info("Customer DM unavailable for order %s", order.order_id)


class PaymentModal(Modal):
    """Collect payment claims for staff review; this modal does not verify payment."""

    def __init__(
        self, plan_label: str, price_label: str, ticket_channel_id: int,
        settings: Settings | None = None,
    ):
        self.settings = settings or SETTINGS
        super().__init__(title=self.settings.btn_pay_label)
        self.plan_label = plan_label
        self.price_label = price_label
        self.ticket_channel_id = ticket_channel_id
        self.last4 = TextInput(
            label="Last 4 digits of card", placeholder="1234",
            min_length=4, max_length=4, required=True,
        )
        self.owner = TextInput(
            label="Cardholder name", placeholder="Name as shown by the bank",
            min_length=2, max_length=35, required=True,
        )
        self.amount = TextInput(
            label="Amount", placeholder=f"Example: {price_label[:-1]}",
            min_length=1, max_length=32, required=True,
        )
        self.tx = TextInput(
            label="Transaction reference / note (optional)",
            required=False, max_length=1000, style=TextStyle.long,
        )
        self.add_item(self.last4)
        self.add_item(self.amount)
        self.add_item(self.owner)
        self.add_item(self.tx)

    async def on_submit(self, interaction: discord.Interaction):
        last4_value = self.last4.value.strip()
        transaction_reference = self.tx.value.strip()

        if not last4_value.isdigit() or len(last4_value) != 4:
            await interaction.response.send_message(
                "The card field must contain exactly four digits.", ephemeral=True
            )
            return

        try:
            submitted_amount = parse_amount(self.amount.value)
            expected_amount = parse_amount(self.price_label)
        except ValueError:
            await interaction.response.send_message(
                "Enter a valid positive amount.", ephemeral=True
            )
            return

        if submitted_amount != expected_amount:
            await interaction.response.send_message(
                f"Entered amount ({submitted_amount}) does not match "
                f"the listed price ({self.price_label}).",
                ephemeral=True,
            )
            return

        if interaction.guild_id is None or interaction.guild is None:
            await interaction.response.send_message(
                "Orders can only be submitted from a server ticket.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Save first. Cardholder name and card digits are deliberately not stored.
        try:
            order = await asyncio.to_thread(
                _store_call, str(self.settings.payments_db), "create_order",
                guild_id=interaction.guild_id,
                customer_id=interaction.user.id,
                product_label=self.plan_label,
                price_label=self.price_label,
                submitted_amount=str(submitted_amount),
                payment_reference=transaction_reference,
                ticket_channel_id=self.ticket_channel_id,
            )
        except (OSError, sqlite3.Error, ValueError):
            logger.exception(
                "Unable to persist an order for guild %s", interaction.guild_id
            )
            await interaction.followup.send(
                "The order could not be saved. No review request was created; "
                "please contact the shop staff.",
                ephemeral=True,
            )
            return

        admin_channel = discord.utils.get(
            interaction.guild.text_channels, name=self.settings.admin_channel_name
        )
        admin_role = discord.utils.get(interaction.guild.roles, name=self.settings.admin_role_name)
        admin_embed = discord.Embed(
            title="Payment details submitted — manual review required",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        admin_embed.add_field(name="Order ID", value=order.order_id, inline=False)
        admin_embed.add_field(name="Customer", value=interaction.user.mention, inline=True)
        admin_embed.add_field(name="Cardholder", value=self.owner.value, inline=True)
        admin_embed.add_field(name="Product", value=self.plan_label, inline=True)
        admin_embed.add_field(name="Listed price", value=self.price_label, inline=True)
        admin_embed.add_field(
            name="Claimed amount", value=str(submitted_amount), inline=True
        )
        admin_embed.add_field(name="Last four digits", value=last4_value, inline=True)
        admin_embed.add_field(
            name="Transaction reference",
            value=transaction_reference[:1000] or "Not provided",
            inline=False,
        )
        admin_embed.add_field(
            name="Review commands",
            value=(
                f"/order approve {order.order_id}\n"
                f"/order reject {order.order_id} reason: ..."
            ),
            inline=False,
        )

        notification_failed = admin_channel is None
        if admin_channel is not None:
            try:
                await admin_channel.send(
                    content=admin_role.mention if admin_role else "",
                    embed=admin_embed,
                )
            except discord.HTTPException:
                notification_failed = True
                logger.exception(
                    "Order %s was saved but admin notification failed", order.order_id
                )

        if notification_failed:
            await interaction.followup.send(
                f"Order {order.order_id} was saved and is awaiting review, but the "
                "admin notification could not be delivered. Please contact staff "
                "and provide this order ID.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"Order {order.order_id} was saved and sent for manual review. "
            "This is not payment confirmation, and no product has been delivered yet.",
            ephemeral=True,
        )


class ShopCog(commands.Cog):
    """Shopfront, order queue, and manual review commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = getattr(bot, "settings", None) or SETTINGS
        self.plan_options = [
            discord.SelectOption(label=item["label"], value=item["value"])
            for item in load_plan_entries(self.settings.config_path)
        ]

    async def _require_admin(self, ctx: commands.Context) -> bool:
        if ctx.guild is not None and is_shop_admin(ctx.author, self.settings.admin_role_name):
            return True
        await send_context(
            ctx,
            "You need administrator permissions or the configured shop-admin role.",
            ephemeral=True,
        )
        return False

    @commands.hybrid_command(name="shop", description="Show the shop and available plans")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title=self.settings.shop_title, description=self.settings.shop_description, color=discord.Color.blue()
        )
        embed.set_footer(text=self.settings.shop_footer)
        view = View(timeout=None)

        if self.settings.telegram_shop_url:
            view.add_item(
                Button(label=self.settings.btn_shop_label, style=discord.ButtonStyle.link, url=self.settings.telegram_shop_url)
            )
        if self.settings.telegram_support_url:
            view.add_item(
                Button(label=self.settings.btn_support_label, style=discord.ButtonStyle.link, url=self.settings.telegram_support_url)
            )

        select = Select(placeholder="Choose a plan...", options=self.plan_options)

        async def select_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            selected_value = interaction.data["values"][0]
            selected_label = next(
                option.label for option in select.options if option.value == selected_value
            )
            plan_label, price_label = parse_plan_label(selected_label)
            guild = interaction.guild
            author = interaction.user

            if guild is None:
                await interaction.followup.send(
                    "Please use the shop inside a server.", ephemeral=True
                )
                return

            category = discord.utils.get(guild.categories, name=self.settings.category_name)
            if category is None:
                category = await guild.create_category(
                    self.settings.category_name,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        guild.me: discord.PermissionOverwrite(view_channel=True),
                    },
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
            admin_role = discord.utils.get(guild.roles, name=self.settings.admin_role_name)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_messages=True
                )

            ticket_channel = await category.create_text_channel(
                name=generate_ticket_name(author, self.settings.ticket_name_template),
                overwrites=overwrites,
                reason=f"Shop order ticket for {author.name} ({author.id})",
            )
            ticket_embed = discord.Embed(
                title="GuildCart | Order Ticket",
                description=(
                    f"You selected **{selected_label}**.\n"
                    f"Payment instructions: **{self.settings.card_number}**\n"
                    "Submit the payment details for manual staff review."
                ),
                timestamp=datetime.now(timezone.utc),
            )

            ticket_view = View(timeout=None)
            pay_button = Button(label=self.settings.btn_pay_label, style=discord.ButtonStyle.primary)

            async def pay_callback(button_interaction: discord.Interaction):
                if button_interaction.user.id != author.id:
                    await button_interaction.response.send_message(
                        "Only the customer who opened this ticket can submit payment details.",
                        ephemeral=True,
                    )
                    return
                await button_interaction.response.send_modal(
                    PaymentModal(plan_label, price_label, ticket_channel.id, settings=self.settings)
                )

            pay_button.callback = pay_callback
            ticket_view.add_item(pay_button)
            close_button = Button(label=self.settings.btn_close_label, style=discord.ButtonStyle.danger)

            async def close_callback(close_interaction: discord.Interaction):
                if (
                    close_interaction.user.id != author.id
                    and not is_shop_admin(close_interaction.user, self.settings.admin_role_name)
                ):
                    await close_interaction.response.send_message(
                        "Only the ticket owner or shop staff can close this ticket.",
                        ephemeral=True,
                    )
                    return
                await close_interaction.response.defer()
                await ticket_channel.delete(
                    reason="Ticket closed by customer or shop staff"
                )

            close_button.callback = close_callback
            ticket_view.add_item(close_button)
            await ticket_channel.send(
                content=f"Hello {author.mention}!", embed=ticket_embed, view=ticket_view
            )
            await interaction.followup.send(
                f"Your ticket has been created: {ticket_channel.mention}",
                ephemeral=True,
            )

        select.callback = select_callback
        view.add_item(select)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="orders", description="List orders awaiting review")
    @commands.guild_only()
    async def orders(self, ctx: commands.Context):
        if not await self._require_admin(ctx):
            return
        try:
            orders = await asyncio.to_thread(
                _store_call, str(self.settings.payments_db), "list_pending_orders",
                guild_id=ctx.guild.id,
                limit=10,
            )
        except (OSError, sqlite3.Error):
            logger.exception("Could not list orders for guild %s", ctx.guild.id)
            await send_context(ctx, "The order database is temporarily unavailable.", ephemeral=True)
            return

        if not orders:
            await send_context(ctx, "There are no orders awaiting review.", ephemeral=True)
            return

        lines = [
            f"**{order.order_id}** — <@{order.customer_id}> — "
            f"{order.product_label} — {order.price_label} — {order.created_at}"
            for order in orders
        ]
        await send_context(
            ctx,
            "Orders awaiting manual review (up to 10):\n" + "\n".join(lines),
            ephemeral=True,
        )

    @commands.hybrid_group(name="order", invoke_without_command=True)
    @commands.guild_only()
    async def order(self, ctx: commands.Context):
        """Manage an order after checking the submitted payment independently."""
        await send_context(
            ctx,
            "Use /orders, /order approve <order_id>, or "
            "/order reject <order_id> <reason>.",
            ephemeral=True,
        )

    @order.command(name="approve", description="Approve after manually verifying payment")
    async def order_approve(self, ctx: commands.Context, order_id: str):
        if not await self._require_admin(ctx):
            return
        try:
            order = await asyncio.to_thread(
                _store_call, str(self.settings.payments_db), "review_order",
                guild_id=ctx.guild.id,
                order_id=order_id,
                reviewer_id=ctx.author.id,
                decision=PAID,
                note="Manually approved by shop staff",
            )
        except OrderNotFoundError:
            await send_context(ctx, "That order was not found in this server.", ephemeral=True)
            return
        except OrderStateError as exc:
            await send_context(ctx, str(exc), ephemeral=True)
            return
        except (OSError, sqlite3.Error):
            logger.exception("Could not approve order %s", order_id)
            await send_context(ctx, "The order database is temporarily unavailable.", ephemeral=True)
            return

        await notify_customer(
            ctx.guild,
            order,
            f"Your GuildCart order {order.order_id} was approved after manual payment review. "
            "This prototype has not automatically provisioned a product or VPN subscription.",
        )
        await send_context(
            ctx,
            f"Order {order.order_id} marked as paid after manual review. "
            "No product or VPN subscription was automatically delivered.",
            ephemeral=True,
        )

    @order.command(name="reject", description="Reject after manual review")
    async def order_reject(self, ctx: commands.Context, order_id: str, *, reason: str):
        if not await self._require_admin(ctx):
            return
        if not reason.strip():
            await send_context(ctx, "A rejection reason is required.", ephemeral=True)
            return
        try:
            order = await asyncio.to_thread(
                _store_call, str(self.settings.payments_db), "review_order",
                guild_id=ctx.guild.id,
                order_id=order_id,
                reviewer_id=ctx.author.id,
                decision=REJECTED,
                note=reason,
            )
        except OrderNotFoundError:
            await send_context(ctx, "That order was not found in this server.", ephemeral=True)
            return
        except OrderStateError as exc:
            await send_context(ctx, str(exc), ephemeral=True)
            return
        except (OSError, sqlite3.Error):
            logger.exception("Could not reject order %s", order_id)
            await send_context(ctx, "The order database is temporarily unavailable.", ephemeral=True)
            return

        await notify_customer(
            ctx.guild,
            order,
            f"Your GuildCart order {order.order_id} was rejected after manual review. "
            f"Reason: {reason.strip()[:500]}",
        )
        await send_context(
            ctx,
            f"Order {order.order_id} rejected. The decision and reason were saved.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))


__all__ = [
    "PaymentModal", "PLAN_OPTIONS", "ShopCog", "generate_ticket_name",
    "get_order_store", "is_shop_admin", "setup",
]
