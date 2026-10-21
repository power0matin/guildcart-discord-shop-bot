"""Smoke tests for the Discord shop Cog and its command registration."""

import unittest
from types import SimpleNamespace

import discord
from discord.ext import commands

from guildcart.app import COG_MODULES, create_bot
from guildcart.cogs.shop import ShopCog, is_shop_admin
from guildcart.settings import Settings


class ShopExtensionTests(unittest.IsolatedAsyncioTestCase):
    async def test_shop_cog_registers_expected_commands(self):
        bot = create_bot(Settings.from_environment())
        try:
            for extension in COG_MODULES:
                await bot.load_extension(extension)

            self.assertIsNotNone(bot.get_command("help"))
            self.assertIsNotNone(bot.get_command("shop"))
            self.assertIsNotNone(bot.get_command("orders"))
            order_group = bot.get_command("order")
            self.assertIsNotNone(order_group)
            self.assertEqual(
                {command.name for command in order_group.commands},
                {"approve", "reject"},
            )
            self.assertIsNotNone(bot.tree.get_command("order"))
        finally:
            await bot.close()

    async def test_only_discord_cogs_are_loaded(self):
        self.assertEqual(COG_MODULES, ("guildcart.cogs.core", "guildcart.cogs.shop"))

    async def test_sample_shop_has_valid_plan_options(self):
        bot = create_bot(Settings.from_environment())
        try:
            cog = ShopCog(bot)
            self.assertEqual(len(cog.plan_options), 3)
            self.assertTrue(
                all(option.label and option.value for option in cog.plan_options)
            )
        finally:
            await bot.close()

    async def test_shop_admin_check_requires_admin_or_configured_role(self):
        admin = SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=True), roles=[]
        )
        staff = SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=False),
            roles=[SimpleNamespace(name="Admin")],
        )
        regular_user = SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=False),
            roles=[SimpleNamespace(name="Member")],
        )

        self.assertTrue(is_shop_admin(admin))
        self.assertTrue(is_shop_admin(staff))
        self.assertFalse(is_shop_admin(regular_user))


if __name__ == "__main__":
    unittest.main()
