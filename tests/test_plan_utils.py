"""Unit tests for legacy plan configuration and amount parsing."""

import unittest
from decimal import Decimal

from features.plan_utils import parse_amount, parse_plan_label, validate_plans


class ParseAmountTests(unittest.TestCase):
    def test_accepts_integer_and_legacy_suffix(self):
        self.assertEqual(parse_amount("50"), Decimal("50"))
        self.assertEqual(parse_amount("50T"), Decimal("50"))

    def test_accepts_decimal_and_thousands_separator(self):
        self.assertEqual(parse_amount("1,250.50 T"), Decimal("1250.50"))

    def test_rejects_invalid_or_non_positive_amounts(self):
        for value in ("", "abc", "NaN", "Infinity", "0", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_amount(value)


class ParsePlanLabelTests(unittest.TestCase):
    def test_supports_legacy_dash_variants(self):
        self.assertEqual(parse_plan_label("Starter – 50T"), ("Starter", "50T"))
        self.assertEqual(parse_plan_label("Plus — 100T"), ("Plus", "100T"))
        self.assertEqual(parse_plan_label("Pro - 200T"), ("Pro", "200T"))

    def test_rejects_labels_without_a_numeric_price(self):
        for label in ("", "Starter", "Starter – free", "– 50T", "Starter – "):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_plan_label(label)


class ValidatePlansTests(unittest.TestCase):
    def test_returns_normalized_plan_entries(self):
        plans = [{"label": " Starter – 50T ", "value": "starter"}]
        self.assertEqual(
            validate_plans(plans),
            [{"label": "Starter – 50T", "value": "starter"}],
        )

    def test_rejects_missing_or_empty_plan_list(self):
        for plans in (None, {}, [], "plans"):
            with self.subTest(plans=plans):
                with self.assertRaises(ValueError):
                    validate_plans(plans)

    def test_rejects_duplicate_values_and_more_than_25_plans(self):
        duplicate_values = [
            {"label": "Starter – 50T", "value": "same"},
            {"label": "Plus – 100T", "value": "same"},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate plan value"):
            validate_plans(duplicate_values)

        too_many = [
            {"label": f"Plan{i} – {i + 1}T", "value": f"plan-{i}"}
            for i in range(26)
        ]
        with self.assertRaisesRegex(ValueError, "at most 25"):
            validate_plans(too_many)

    def test_rejects_oversized_discord_component_values(self):
        plans = [{"label": "A" * 101 + " – 50T", "value": "starter"}]
        with self.assertRaisesRegex(ValueError, "label must be 100"):
            validate_plans(plans)


if __name__ == "__main__":
    unittest.main()
