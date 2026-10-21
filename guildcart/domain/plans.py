"""Validation helpers for GuildCart's legacy plan configuration."""

import re
from decimal import Decimal, InvalidOperation


_PLAN_SEPARATOR = re.compile(r"\s+[–—-]\s+")


def parse_amount(raw_value: str) -> Decimal:
    """Parse a positive legacy amount, optionally suffixed with T."""
    if not isinstance(raw_value, str):
        raise ValueError("Amount must be text.")

    normalized = raw_value.strip().replace(",", "").replace(" ", "")
    if normalized.casefold().endswith("t"):
        normalized = normalized[:-1]

    try:
        amount = Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid positive number.") from None

    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be a valid positive number.")

    return amount


def parse_plan_label(label: str) -> tuple[str, str]:
    """Split a legacy label such as Starter – 50T into name and price."""
    if not isinstance(label, str) or not label.strip():
        raise ValueError("Plan label must be a non-empty string.")

    parts = _PLAN_SEPARATOR.split(label.strip(), maxsplit=1)
    if len(parts) != 2:
        raise ValueError(
            "Plan label must contain a name and numeric price separated by "
            "an en dash, em dash, or hyphen (example: Starter – 50T)."
        )

    plan_name, price_label = (part.strip() for part in parts)
    if not plan_name or not price_label:
        raise ValueError("Plan name and price must both be provided.")

    parse_amount(price_label)
    return plan_name, price_label


def validate_plans(plans: object) -> list[dict[str, str]]:
    """Validate plans before they are exposed in a Discord select menu."""
    if not isinstance(plans, list) or not plans:
        raise ValueError("'plans' must be a non-empty list.")
    if len(plans) > 25:
        raise ValueError("Discord select menus support at most 25 plans.")

    validated: list[dict[str, str]] = []
    seen_values: set[str] = set()

    for index, item in enumerate(plans, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Plan #{index} must be an object.")

        label = item.get("label")
        value = item.get("value")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Plan #{index} requires a non-empty label.")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Plan #{index} requires a non-empty value.")
        if len(label) > 100:
            raise ValueError(f"Plan #{index} label must be 100 characters or fewer.")
        if len(value) > 100:
            raise ValueError(f"Plan #{index} value must be 100 characters or fewer.")
        if value.strip() in seen_values:
            raise ValueError(f"Duplicate plan value: {value!r}.")

        parse_plan_label(label)
        seen_values.add(value.strip())
        validated.append({"label": label.strip(), "value": value.strip()})

    return validated
