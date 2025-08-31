import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ HyperShield Shop")
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        """
        HyperShield Shop — فروشگاه رسمی هایپرشیلد
        """
        CATEGORY_NAME = os.getenv("CATEGORY_NAME")
        ADMIN_CHANNEL_NAME = os.getenv("ADMIN_CHANNEL_NAME")
        ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME")
        CARD_NUMBER = os.getenv("CARD_NUMBER")

        embed = discord.Embed(
            title="💎 HyperShield | سرورهای پرسرعت آلمان 🇩🇪",
            description=(
                "🚀 **Chara HyperShield?**\n"
                "- Serverhaye anti-filter ba ping kam\n"
                "- Poshtibani 24/7 az tarigh Telegram\n"
                "- Test free 24 sa'ate\n"
                "- Pardakht amn ba cart & crypto\n\n"
                "📱 Channel Telegram: [Shop HyperShield](https://t.me/Shop_HyperSheild)"
            ),
            color=discord.Color(0x00FFFF),
        )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/912587142629326859/1410658003891388516/channel.jpg"
        )
        embed.set_footer(
            text="🌐 HyperShield — Speed ⚡ Security",
            icon_url="https://cdn.discordapp.com/attachments/912587142629326859/1410658003891388516/channel.jpg",
        )

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

        view = discord.ui.View(timeout=None)

        buy_button = discord.ui.Button(
            label="📱 Telegram Channel",
            style=discord.ButtonStyle.link,
            url="https://t.me/Shop_HyperSheild",
        )
        view.add_item(buy_button)

        assistant_button = discord.ui.Button(
            label="🧑‍💻 Support",
            style=discord.ButtonStyle.link,
            url="https://t.me/Assistant_HyperShield",
        )
        view.add_item(assistant_button)

        select = discord.ui.Select(
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

        async def select_callback(interaction: discord.Interaction):
            try:
                selected = interaction.data["values"][0]
                plan_text = next(
                    opt.label for opt in select.options if opt.value == selected
                )

                guild = interaction.guild
                author = interaction.user

                category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
                if category is None:
                    category = await guild.create_category(CATEGORY_NAME)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    author: discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, read_message_history=True
                    ),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        manage_messages=True,
                    ),
                }

                ticket_channel = await guild.create_text_channel(
                    name=f"ticket-{author.name}",
                    category=category,
                    overwrites=overwrites,
                    reason=f"Ticket for {author}",
                )

                ticket_embed = discord.Embed(
                    title="🎫 HyperShield | Ticket",
                    description=(
                        f"👋 Salam {author.mention}!\n\n"
                        f"✅ Shoma plan **{plan_text}** ro entekhab kardi.\n\n"
                        "🔹 Lotfan mablagh ro be shomare kart zir vaariz konid:\n"
                        f"💳 **{CARD_NUMBER}**\n\n"
                        "📸 Tasvir-e vaarizi ro dar in ticket ersal konid.\n\n"
                        "🛡️ Payamhaye shoma faghat tavasot **Admin-ha** dida mishavad."
                    ),
                    color=discord.Color.green(),
                )

                await ticket_channel.send(embed=ticket_embed)

                # Notify admin channel
                admin_channel = discord.utils.get(
                    guild.text_channels, name=ADMIN_CHANNEL_NAME
                )
                if admin_channel:
                    await admin_channel.send(
                        f"🚨 Ticket jadid sakhte shod!\n\n"
                        f"👤 User: {author.mention}\n"
                        f"📦 Plan: **{plan_text}**\n"
                        f"📂 Channel: {ticket_channel.mention}\n\n"
                        "📝 Lotfan tasvir-e vaarizi ro barrasi konid."
                    )

                await interaction.response.send_message(
                    f"🎟️ Ticket shoma baraye plan **{plan_text}** sakhte shod!\n👉 {ticket_channel.mention}",
                    ephemeral=True,
                )

            except Exception as e:
                await interaction.response.send_message(
                    f"⚠️ Error: {str(e)}", ephemeral=True
                )

        select.callback = select_callback
        view.add_item(select)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))
