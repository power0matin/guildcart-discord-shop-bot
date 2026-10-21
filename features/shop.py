"""Compatibility import path for the original features.shop module."""
from guildcart.cogs.shop import (
    ADMIN_CHANNEL_NAME, ADMIN_ROLE_NAME, BTN_CLOSE_LABEL, BTN_PAY_LABEL,
    BTN_SHOP_LABEL, BTN_SUPPORT_LABEL, CARD_NUMBER, CATEGORY_NAME,
    CRYPTO_ADDRESS_USDT, PAYMENT_TIMEOUT_MINUTES, PAYMENTS_DB, PLAN_OPTIONS,
    SHOP_DESCRIPTION, SHOP_FOOTER, SHOP_TITLE, TELEGRAM_SHOP_URL,
    TELEGRAM_SUPPORT_URL, TICKET_NAME_TEMPLATE, PaymentModal, ShopCog,
    generate_ticket_name, get_order_store, is_shop_admin,
)


async def setup(bot):
    await bot.add_cog(ShopCog(bot))


__all__ = [
    "PaymentModal", "PLAN_OPTIONS", "ShopCog", "setup", "is_shop_admin",
    "generate_ticket_name", "get_order_store",
]
