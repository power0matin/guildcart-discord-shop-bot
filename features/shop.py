import discord
from discord.ext import commands


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="🛍️ HyperShield Shop")
    async def shop(self, ctx: commands.Context):
        """
        HyperShield Shop with fingleesh texts
        """

        # Embed professional
        embed = discord.Embed(
            title="💎 HyperShield | Serverhaye PorSor'at Germany 🇩🇪",
            description=(
                "🚀 **Chara HyperShield?**\n"
                "- Serverhaye anti-filter ba ping kam\n"
                "- Poshtibani 24/7 az tarigh Telegram\n"
                "- Test free 24 sa'ate\n"
                "- Pardakht amn ba cart & crypto\n\n"
                "<:telegram:123456789012345678> Channel Telegram: [Shop HyperShield](https://t.me/Shop_HyperSheild)"
            ),
            color=discord.Color(0x00FFFF),  # cyan,
        )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/912587142629326859/1410658003891388516/channel.jpg?ex=68b1d124&is=68b07fa4&hm=6a07732b569f9f3605737196740455f64bf35332631e553d985f9684ebcdbd0d&"
        )
        embed.set_footer(
            text="🌐 HyperShield — Speed & Security",
            icon_url="https://cdn.discordapp.com/attachments/912587142629326859/1410658003891388516/channel.jpg?ex=68b1d124&is=68b07fa4&hm=6a07732b569f9f3605737196740455f64bf35332631e553d985f9684ebcdbd0d&",
        )

        # Add fields (plans)
        embed.add_field(
            name="🔥 Tunnel (Ejtemayi & Arzun)",
            value="20GB – 65 Toman | 30GB – 90 Toman\n40GB – 130 Toman | 50GB – 160 Toman\n60GB – 190 Toman",
            inline=False,
        )
        embed.add_field(
            name="⚡ Unlimited (Fair Usage)",
            value="80GB – 210 Toman | 100GB – 260 Toman\n150GB – 390 Toman | 200GB – 520 Toman",
            inline=False,
        )
        embed.add_field(
            name="🌐 Premium",
            value="10GB – 80 Toman | 20GB – 160 Toman\n30GB – 240 Toman | 40GB – 320 Toman\n50GB – 400 Toman",
            inline=False,
        )

        # View for button & select
        view = discord.ui.View(timeout=None)

        # Button to Telegram
        buy_button = discord.ui.Button(
            label="🛒 Kharid az telegram",
            style=discord.ButtonStyle.link,
            url="https://t.me/Shop_HyperSheild",
        )
        view.add_item(buy_button)

        Assistant_button = discord.ui.Button(
            label="🧑‍💻 Support",
            style=discord.ButtonStyle.link,
            url="https://t.me/Assistant_HyperShield",
        )
        view.add_item(Assistant_button)

        # Select menu for plans
        select = discord.ui.Select(
            placeholder="Yek plan entekhab konid...",
            options=[
                discord.SelectOption(label="10GB – 40 Toman", value="10g"),
                discord.SelectOption(label="20GB – 65 Toman", value="20g"),
                discord.SelectOption(label="30GB – 90 Toman", value="30g"),
                discord.SelectOption(label="40GB – 130 Toman", value="40g"),
                discord.SelectOption(label="50GB – 160 Toman", value="50g"),
                discord.SelectOption(label="60GB – 190 Toman", value="60g"),
                discord.SelectOption(label="80GB – 210 Toman", value="80g"),
                discord.SelectOption(label="100GB – 260 Toman", value="100g"),
                discord.SelectOption(label="150GB – 390 Toman", value="150g"),
                discord.SelectOption(label="200GB – 520 Toman", value="200g"),
            ],
        )

        # تعریف callback به عنوان closure تا به select دسترسی داشته باشه
        async def select_callback(interaction: discord.Interaction):
            selected = interaction.data["values"][0]
            plan_text = next(
                opt.label for opt in select.options if opt.value == selected
            )

            guild = interaction.guild
            author = interaction.user

            # پیدا کردن یا ایجاد دسته تیکت‌ها
            category_name = "HyperShield"
            category = discord.utils.get(guild.categories, name=category_name)
            if category is None:
                category = await guild.create_category(category_name)

            # Permission Overwrites
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                author: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                ),
            }

            # ایجاد کانال تیکت
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{author.name}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket for {author}",
            )

            # پیام داخل تیکت
            await ticket_channel.send(
                f"Salam {author.mention}! ✅\n"
                f"Shoma plan **{plan_text}** ro entekhab kardi.\n\n"
                f"Lotfan be in shomare kart vaariz konid:\n"
                "💳 1234-5678-9012-3456\n"
                f"Va tasvir varizi ro inja ersal konid.\n\n"
                f"Payamaye shoma be Admin ha etela' dade mishavad."
            )

            # اطلاع‌رسانی به Admin
            admin_channel = discord.utils.get(guild.text_channels, name="admin-notify")
            if admin_channel:
                await admin_channel.send(
                    f"📌 User {author.mention} plan **{plan_text}** ro entekhab kard. "
                    f"Tasvir varizy ro check kon."
                )

            # پاسخ ephemeral
            await interaction.response.send_message(
                f"🎫 Ticket shoma baraye plan **{plan_text}** sakhte shod ✅",
                ephemeral=True,
            )

        select.callback = select_callback
        view.add_item(select)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))
