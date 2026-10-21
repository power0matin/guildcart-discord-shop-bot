"""Compatibility imports for the original features.shop module."""

import discord

from guildcart.cogs.shop import (
    PaymentModal,
    ShopCog,
    generate_ticket_name,
    get_order_store,
    is_shop_admin,
)
from guildcart.settings import Settings, load_plan_entries

_settings = Settings.from_environment()
CATEGORY_NAME = _settings.category_name
ADMIN_CHANNEL_NAME = _settings.admin_channel_name
ADMIN_ROLE_NAME = _settings.admin_role_name
PAYMENT_TIMEOUT_MINUTES = _settings.payment_timeout_minutes
PAYMENTS_DB = _settings.payments_db
CARD_NUMBER = _settings.card_number
CRYPTO_ADDRESS_USDT = _settings.crypto_address_usdt
TICKET_NAME_TEMPLATE = _settings.ticket_name_template
SHOP_TITLE = _settings.shop_title
SHOP_DESCRIPTION = _settings.shop_description
SHOP_FOOTER = _settings.shop_footer
TELEGRAM_SHOP_URL = _settings.telegram_shop_url
TELEGRAM_SUPPORT_URL = _settings.telegram_support_url
BTN_SHOP_LABEL = _settings.btn_shop_label
BTN_SUPPORT_LABEL = _settings.btn_support_label
BTN_PAY_LABEL = _settings.btn_pay_label
BTN_CLOSE_LABEL = _settings.btn_close_label
PLAN_OPTIONS = [
    discord.SelectOption(label=item["label"], value=item["value"])
    for item in load_plan_entries(_settings.config_path)
]


async def setup(bot):
    await bot.add_cog(ShopCog(bot))


__all__ = [
    "PaymentModal", "PLAN_OPTIONS", "ShopCog", "setup", "is_shop_admin",
    "generate_ticket_name", "get_order_store",
]
