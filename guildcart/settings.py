"""Validated runtime settings and shop configuration loading."""
from __future__ import annotations
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from guildcart.domain.plans import validate_plans

load_dotenv()

class ConfigurationError(ValueError):
    """Raised when local GuildCart configuration cannot be used safely."""

@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings; the Discord token is intentionally excluded."""
    prefix: str = "$"
    log_level: str = "INFO"
    category_name: str = "tickets"
    admin_channel_name: str = "admin-notify"
    admin_role_name: str = "Admin"
    payment_timeout_minutes: int = 30
    payments_db: Path = Path("data/payments.db")
    config_path: Path = Path("config.json")
    card_number: str = "Configure payment instructions privately"
    crypto_address_usdt: str = ""
    ticket_name_template: str = "ticket-{author}-{rand6}"
    shop_title: str = "GuildCart | Digital Shop"
    shop_description: str = ""
    shop_footer: str = ""
    telegram_shop_url: str = ""
    telegram_support_url: str = ""
    btn_shop_label: str = "Shop channel"
    btn_support_label: str = "Support"
    btn_pay_label: str = "Submit payment details"
    btn_close_label: str = "Close ticket"

    @classmethod
    def from_environment(cls) -> "Settings":
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in logging.getLevelNamesMapping():
            raise ConfigurationError(
                f"Invalid LOG_LEVEL {log_level!r}; use DEBUG, INFO, WARNING, ERROR, or CRITICAL."
            )
        try:
            timeout = int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "30"))
        except ValueError:
            raise ConfigurationError("PAYMENT_TIMEOUT_MINUTES must be a positive integer.") from None
        if timeout < 1:
            raise ConfigurationError("PAYMENT_TIMEOUT_MINUTES must be at least 1.")
        prefix = os.getenv("PREFIX", "$")
        if not prefix.strip():
            raise ConfigurationError("PREFIX cannot be empty.")
        return cls(
            prefix=prefix, log_level=log_level,
            category_name=os.getenv("CATEGORY_NAME", "tickets"),
            admin_channel_name=os.getenv("ADMIN_CHANNEL_NAME", "admin-notify"),
            admin_role_name=os.getenv("ADMIN_ROLE_NAME", "Admin"),
            payment_timeout_minutes=timeout,
            payments_db=Path(os.getenv("PAYMENTS_DB", "data/payments.db")).expanduser(),
            config_path=Path(os.getenv("SHOP_CONFIG_PATH", "config.json")).expanduser(),
            card_number=os.getenv("CARD_NUMBER", "Configure payment instructions privately"),
            crypto_address_usdt=os.getenv("CRYPTO_ADDRESS_USDT", ""),
            ticket_name_template=os.getenv("TICKET_NAME_TEMPLATE", "ticket-{author}-{rand6}"),
            shop_title=os.getenv("SHOP_TITLE", "GuildCart | Digital Shop"),
            shop_description=os.getenv("SHOP_DESCRIPTION", ""),
            shop_footer=os.getenv("SHOP_FOOTER", ""),
            telegram_shop_url=os.getenv("TELEGRAM_SHOP_URL", ""),
            telegram_support_url=os.getenv("TELEGRAM_SUPPORT_URL", ""),
            btn_shop_label=os.getenv("BTN_SHOP_LABEL", "Shop channel"),
            btn_support_label=os.getenv("BTN_SUPPORT_LABEL", "Support"),
            btn_pay_label=os.getenv("BTN_PAY_LABEL", "Submit payment details"),
            btn_close_label=os.getenv("BTN_CLOSE_LABEL", "Close ticket"),
        )

def load_plan_entries(path: str | Path) -> list[dict[str, str]]:
    """Read and validate legacy plan entries, raising actionable errors."""
    config_path = Path(path).expanduser()
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            data: Any = json.load(stream)
    except FileNotFoundError:
        raise ConfigurationError(
            f"Shop config not found at {config_path}. Copy config.json.example to config.json."
        ) from None
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in {config_path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from None
    except OSError as exc:
        raise ConfigurationError(f"Cannot read shop config {config_path}: {exc}") from None
    if not isinstance(data, dict):
        raise ConfigurationError(f"Invalid shop config in {config_path}: root must be a JSON object.")
    try:
        return validate_plans(data.get("plans"))
    except ValueError as exc:
        raise ConfigurationError(f"Invalid shop config in {config_path}: {exc}") from exc

__all__ = ["ConfigurationError", "Settings", "load_plan_entries"]
