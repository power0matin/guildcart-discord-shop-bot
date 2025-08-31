import os
import logging
from datetime import datetime

import discord
from discord import app_commands, TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, Button, View
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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


class PaymentModal(Modal, title="Sabt Pardakht"):
    def __init__(self, plan_label: str, price_label: str, ticket_channel_id: int):
        super().__init__()
        self.plan_label = plan_label
        self.price_label = price_label
        self.ticket_channel_id = ticket_channel_id

        self.last4 = TextInput(
            label="4 ragham akhar kart", placeholder="1234", min_length=4, max_length=4
        )
        self.amount = TextInput(
            label="Mablagh (amount)", placeholder=f"mesal: {price_label}", min_length=1
        )
        self.tx = TextInput(
            label="Tx ID / Description (optional)", required=False, style=TextStyle.long
        )

        self.add_item(self.last4)
        self.add_item(self.amount)
        self.add_item(self.tx)

    async def on_submit(self, interaction: discord.Interaction):
        last4_val = self.last4.value.strip()
        amount_raw = self.amount.value.strip()
        tx_val = self.tx.value.strip() or "N/A"

        if not last4_val.isdigit() or len(last4_val) != 4:
            await interaction.response.send_message(
                "⚠️ Last4 bayad 4 ragham numeric bashe.", ephemeral=True
            )
            return

        try:
            amount_val = float(amount_raw)
            if amount_val <= 0:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message(
                "⚠️ Mablagh ghalat ast.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Confirm to user
        await interaction.followup.send(
            f"✅ Pardakht shoma sabt shod!\n"
            f"Plan: **{self.plan_label}** | Price: **{self.price_label}**\n"
            f"Amount: **{amount_val}T** | Last4: **{last4_val}**\nTx/Desc: {tx_val}",
            ephemeral=True,
        )

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
                admin_embed.add_field(name="Plan", value=self.plan_label, inline=True)
                admin_embed.add_field(name="Price", value=self.price_label, inline=True)
                admin_embed.add_field(
                    name="Amount", value=f"{amount_val}T", inline=True
                )
                admin_embed.add_field(name="Last4", value=last4_val, inline=True)
                admin_embed.add_field(name="Tx/Desc", value=tx_val, inline=False)
                await admin_channel.send(content=mention_text, embed=admin_embed)
            except Exception as e:
                logger.error(f"Failed to send to admin channel: {e}")


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ Show shop embed and plans")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title="💎 HyperShield | High Speed Servers",
            description="🚀 Chara HyperShield?\n- Anti-filter servers ba ping kam\n- Poshtibani 24/7\n- Pardakht ba cart & crypto",
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

        select = Select(
            placeholder="📦 Yek plan entekhab konid...",
            options=[
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
            ],
        )

        async def select_cb(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            selected_label = next(
                opt.label
                for opt in select.options
                if opt.value == interaction.data["values"][0]
            )
            plan_label, price_label = (
                (
                    selected_label.split("–")[0].strip(),
                    selected_label.split("–")[1].strip(),
                )
                if "–" in selected_label
                else (selected_label, "N/A")
            )

            guild = interaction.guild
            author = interaction.user
            category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

            if category is None:
                perms = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False)
                }
                category = await guild.create_category(CATEGORY_NAME, overwrites=perms)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                author: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                ),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )

            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{author.name}-{author.discriminator}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket for {author}",
            )

            ticket_embed = discord.Embed(
                title="🎫 HyperShield | Ticket",
                description=f"✅ Shoma plan **{selected_label}** ro entekhab kardi.\n💳 **{CARD_NUMBER}**\n📸 Tasvir pardakht ro ersal konid.",
                timestamp=datetime.utcnow(),
            )

            pay_button = Button(
                label="💳 Sabt Pardakht", style=discord.ButtonStyle.primary
            )

            async def pay_cb(btn_interaction: discord.Interaction):
                try:
                    await btn_interaction.response.send_modal(
                        PaymentModal(
                            plan_label=plan_label,
                            price_label=price_label,
                            ticket_channel_id=ticket_channel.id,
                        )
                    )
                except discord.errors.InteractionResponded:
                    await btn_interaction.followup.send(
                        "⚠️ Modal قبلاً باز شده است.", ephemeral=True
                    )

            pay_button.callback = pay_cb
            ticket_view = View()
            ticket_view.add_item(pay_button)
            await ticket_channel.send(
                content=f"👋 Salam {author.mention}!",
                embed=ticket_embed,
                view=ticket_view,
            )

            # Notify admin channel as embed
            admin_channel = discord.utils.get(
                guild.text_channels, name=ADMIN_CHANNEL_NAME
            )
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)

            if admin_channel:
                mention_text = admin_role.mention if admin_role else ""
                admin_embed = discord.Embed(
                    title="🚨 Ticket Jadid",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow(),
                )
                admin_embed.add_field(name="User", value=author.mention, inline=True)
                admin_embed.add_field(name="Plan", value=plan_label, inline=True)
                admin_embed.add_field(
                    name="Channel", value=ticket_channel.mention, inline=False
                )
                await admin_channel.send(
                    content=f"{author.mention}!", embed=admin_embed
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
