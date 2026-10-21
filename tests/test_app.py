"""Regression tests for the package entry point and application factory."""

import importlib.util
import unittest
from pathlib import Path

from guildcart.app import COG_MODULES, create_bot
from guildcart.settings import Settings


class AppFactoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_main_module_exists_and_import_does_not_start_the_bot(self):
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        self.assertTrue(main_path.is_file())
        spec = importlib.util.spec_from_file_location("guildcart_main_entry", main_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(callable(module.main))

    async def test_factory_does_not_connect_and_uses_supplied_settings(self):
        settings = Settings.from_environment()
        bot = create_bot(settings)
        try:
            self.assertIs(bot.settings, settings)
            self.assertEqual(bot.command_prefix, settings.prefix)
        finally:
            await bot.close()

    async def test_extensions_are_explicit_cog_modules(self):
        self.assertEqual(
            COG_MODULES,
            ("guildcart.cogs.core", "guildcart.cogs.shop"),
        )


if __name__ == "__main__":
    unittest.main()
