import os
import logging
from datetime import datetime

import discord
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, Button, View
from dotenv import load_dotenv
import random


# Load environment variables
load_dotenv()

# Constants for configuration
CATEGORY_NAME = os.getenv("CATEGORY_NAME", "tickets")
ADMIN_CHANNEL_NAME = os.getenv("ADMIN_CHANNEL_NAME", "admin-payments")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admins")
CARD_NUMBER = os.getenv("CARD_NUMBER", "**** **** **** 4242")

# Logging setup
logger = logging.getLogger("shop_ticket_payment")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class PaymentModal(Modal):
    """
    Modal for registering payment details.
    """

    def __init__(self, plan_label: str, price_label: str, ticket_channel_id: int):
        super().__init__(title="Sabt Pardakht")
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
        amount_raw = self.amount.value.strip().rstrip("Tt")  # Allow 'T' or 't' suffix
        tx_val = self.tx.value.strip() or "N/A"

        # Validate last4
        if not last4_val.isdigit() or len(last4_val) != 4:
            await interaction.response.send_message(
                "⚠️ Last4 bayad 4 ragham numeric bashe.", ephemeral=True
            )
            return

        # Validate and parse amount
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

        # Optionally: Check if amount matches expected price
        expected_price = float(self.price_label.rstrip("Tt"))
        if amount_val != expected_price:
            await interaction.response.send_message(
                f"⚠️ Mablagh vared shode ({amount_val}T) ba gheymat plan ({self.price_label}) motabeghat nadarad.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Confirm to user
        try:
            await interaction.followup.send(
                f"✅ Pardakht shoma sabt shod!\n"
                f"User: {self.owner}\n"
                f"Plan: **{self.plan_label}** | Price: **{self.price_label}**\n"
                f"Amount: **{amount_val}T** | Last4: **{last4_val}**\nTx/Desc: {tx_val}",
                ephemeral=True,
            )
            logger.info(
                f"Payment registered for user {interaction.user.id} in ticket {self.ticket_channel_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send user confirmation: {e}")

        # Notify admin channel as embed
        admin_channel = discord.utils.get(
            interaction.guild.text_channels, name=ADMIN_CHANNEL_NAME
        )
        admin_role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)

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
                admin_embed.add_field(name="User", value=self.owner, inline=True)
                admin_embed.add_field(name="Plan", value=self.plan_label, inline=True)
                admin_embed.add_field(name="Price", value=self.price_label, inline=True)
                admin_embed.add_field(
                    name="Amount", value=f"{amount_val}T", inline=True
                )
                admin_embed.add_field(name="Last4", value=last4_val, inline=True)
                admin_embed.add_field(name="Tx/Desc", value=tx_val, inline=False)
                await admin_channel.send(content=mention_text, embed=admin_embed)
                logger.info(f"Admin notified for payment in channel {admin_channel.id}")
            except Exception as e:
                logger.error(f"Failed to send to admin channel: {e}")
        else:
            logger.warning("Admin channel not found; skipping notification")


class ShopCog(commands.Cog):
    """
    Cog for handling shop commands and interactions.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ Show shop embed and plans")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        """
        Displays the shop embed with plan options and handles ticket creation.
        """
        embed = discord.Embed(
            title="💎 HyperShield | High Speed Servers",
            description=(
                "🚀 **Chara HyperShield?**\n"
                "- Serverhaye anti-filter ba ping kam\n"
                "- Poshtibani 24/7 az tarigh Telegram\n"
                "- Test free 24 sa'ate\n"
                "- Pardakht amn ba cart & crypto\n\n"
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

        buy_button = Button(
            label="📱 Telegram Channel",
            style=discord.ButtonStyle.link,
            url="https://t.me/Shop_HyperSheild",
        )
        view.add_item(buy_button)

        assistant_button = Button(
            label="🧑‍💻 Support",
            style=discord.ButtonStyle.link,
            url="https://t.me/Assistant_HyperShield",
        )
        view.add_item(assistant_button)

        # Updated select with Premium options distinguished by prefix
        select = Select(
            placeholder="📦 Yek plan entekhab konid...",
            options=[
                # Tunnel plans
                discord.SelectOption(label="🔥10GB – 40T", value="t10g"),
                discord.SelectOption(label="🔥20GB – 65T", value="t20g"),
                discord.SelectOption(label="🔥30GB – 90T", value="t30g"),
                discord.SelectOption(label="🔥40GB – 130T", value="t40g"),
                discord.SelectOption(label="🔥50GB – 160T", value="t50g"),
                discord.SelectOption(label="🔥60GB – 190T", value="t60g"),
                # Unlimited plans
                discord.SelectOption(label="⚡80GB – 210T", value="u80g"),
                discord.SelectOption(label="⚡100GB – 260T", value="u100g"),
                discord.SelectOption(label="⚡150GB – 390T", value="u150g"),
                discord.SelectOption(label="⚡200GB – 520T", value="u200g"),
                # Premium plans
                discord.SelectOption(label="🌐10GB – 80T", value="p10g"),
                discord.SelectOption(label="🌐20GB – 160T", value="p20g"),
                discord.SelectOption(label="🌐30GB – 240T", value="p30g"),
                discord.SelectOption(label="🌐40GB – 320T", value="p40g"),
                discord.SelectOption(label="🌐50GB – 400T", value="p50g"),
            ],
        )

        async def select_cb(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            selected_value = interaction.data["values"][0]
            selected_label = next(
                opt.label for opt in select.options if opt.value == selected_value
            )
            plan_label, price_label = (
                (
                    selected_label.split("–")[0].strip()[1:],  # Remove emoji
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
                try:
                    category = await guild.create_category(
                        CATEGORY_NAME, overwrites=overwrites
                    )
                    logger.info(f"Created category {CATEGORY_NAME}")
                except discord.Forbidden:
                    await interaction.followup.send(
                        "⚠️ Bot majaz be sakht category nist.", ephemeral=True
                    )
                    logger.error("Bot lacks permission to create category")
                    return
                except Exception as e:
                    await interaction.followup.send(
                        "⚠️ Khataye dakheli rokh dad.", ephemeral=True
                    )
                    logger.error(f"Failed to create category: {e}")
                    return

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

            # Name for the ticket channel with random 6-digit number
            ticket_name = f"ticket-{author.name}-{random.randint(100000, 999999)}"

            try:
                # Create the ticket channel in the specified category
                ticket_channel = await category.create_text_channel(
                    name=ticket_name,
                    overwrites=overwrites,  # Permission overwrites
                    reason=f"Ticket for {author.name} ({author.id})",  # Audit log reason
                )

                # Log successful creation
                logger.info(
                    f"Created ticket channel {ticket_channel.id} for user {author.id}"
                )

            except discord.Forbidden:
                # Bot lacks permission to create channel
                await interaction.followup.send(
                    "⚠️ Bot majaz be sakht channel nist.", ephemeral=True
                )
                logger.error("Bot lacks permission to create text channel")
                return

            except Exception as e:
                # Catch any other unexpected errors
                await interaction.followup.send(
                    "⚠️ Khataye dakheli rokh dad.", ephemeral=True
                )
                logger.error(f"Failed to create ticket channel: {e}")
                return

            ticket_embed = discord.Embed(
                title="🎫 HyperShield | Ticket",
                description=f"✅ Shoma plan **{selected_label}** ro entekhab kardi.\n💳 **{CARD_NUMBER}**\n📸 Tasvir pardakht ro ersal konid.",
                timestamp=datetime.utcnow(),
            )

            pay_button = Button(
                label="💳 Sabt Pardakht", style=discord.ButtonStyle.primary
            )

            async def pay_cb(btn_interaction: discord.Interaction):
                if btn_interaction.user.id != author.id:
                    await btn_interaction.response.send_message(
                        "⚠️ Faghat sakht ticket mitavanad az in dokme estefade konad.",
                        ephemeral=True,
                    )
                    return
                await btn_interaction.response.send_modal(
                    PaymentModal(
                        plan_label=plan_label,
                        price_label=price_label,
                        ticket_channel_id=ticket_channel.id,
                    )
                )

            pay_button.callback = pay_cb
            ticket_view = View(timeout=None)  # Persistent view
            ticket_view.add_item(pay_button)

            # Add a close button for the ticket
            close_button = Button(
                label="🔒 Bastan Ticket", style=discord.ButtonStyle.danger
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
                logger.info(
                    f"Ticket {ticket_channel.id} closed by {close_interaction.user.id}"
                )

            close_button.callback = close_cb
            ticket_view.add_item(close_button)

            await ticket_channel.send(
                content=f"👋 Salam {author.mention}!",
                embed=ticket_embed,
                view=ticket_view,
            )

            # Notify admin channel as embed
            admin_channel = discord.utils.get(
                guild.text_channels, name=ADMIN_CHANNEL_NAME
            )
            if admin_channel:
                admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
                mention_text = admin_role.mention if admin_role else ""
                admin_embed = discord.Embed(
                    title="🚨 Ticket Jadid",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow(),
                )
                admin_embed.add_field(name="User", value=author.mention, inline=True)
                admin_embed.add_field(name="Plan", value=selected_label, inline=True)
                admin_embed.add_field(
                    name="Channel", value=ticket_channel.mention, inline=False
                )
                try:
                    await admin_channel.send(content=mention_text, embed=admin_embed)
                    logger.info(f"Admin notified for new ticket {ticket_channel.id}")
                except Exception as e:
                    logger.error(f"Failed to notify admin for new ticket: {e}")
            else:
                logger.warning(
                    "Admin channel not found; skipping new ticket notification"
                )

            await interaction.followup.send(
                f"🎟️ Ticket baraye plan **{selected_label}** sakhte shod! {ticket_channel.mention}",
                ephemeral=True,
            )

        select.callback = select_cb
        view.add_item(select)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
