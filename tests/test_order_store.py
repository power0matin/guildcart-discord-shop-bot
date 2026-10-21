"""Tests for durable order storage and guarded manual review transitions."""

import tempfile
import unittest
from pathlib import Path

from features.order_store import (
    PAID,
    PENDING_REVIEW,
    REJECTED,
    OrderNotFoundError,
    OrderStateError,
    OrderStore,
)


class OrderStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "nested" / "orders.db"
        self.store = OrderStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_order(self, *, guild_id=123, customer_id=456):
        return self.store.create_order(
            guild_id=guild_id,
            customer_id=customer_id,
            product_label="Starter VPN — 30 days",
            price_label="50T",
            submitted_amount="50",
            payment_reference="test-reference",
            ticket_channel_id=789,
        )

    def test_order_is_persisted_across_store_recreation(self):
        created = self.create_order()
        reopened = OrderStore(self.db_path).get_order(
            guild_id=123, order_id=created.order_id.lower()
        )

        self.assertEqual(reopened.order_id, created.order_id)
        self.assertEqual(reopened.status, PENDING_REVIEW)
        self.assertEqual(reopened.customer_id, 456)
        self.assertEqual(reopened.payment_reference, "test-reference")
        self.assertIsNone(reopened.reviewed_by)

    def test_pending_orders_are_scoped_to_the_guild(self):
        first = self.create_order(guild_id=123)
        second = self.create_order(guild_id=999)

        pending = self.store.list_pending_orders(guild_id=123)
        self.assertEqual([order.order_id for order in pending], [first.order_id])
        self.assertNotIn(second.order_id, [order.order_id for order in pending])

    def test_review_approval_is_durable_and_records_reviewer(self):
        created = self.create_order()
        reviewed = self.store.review_order(
            guild_id=123,
            order_id=created.order_id,
            reviewer_id=987,
            decision=PAID,
            note="Transfer checked manually",
        )

        self.assertEqual(reviewed.status, PAID)
        self.assertEqual(reviewed.reviewed_by, 987)
        self.assertEqual(reviewed.review_note, "Transfer checked manually")
        self.assertIsNotNone(reviewed.reviewed_at)

        reopened = OrderStore(self.db_path).get_order(
            guild_id=123, order_id=created.order_id
        )
        self.assertEqual(reopened.status, PAID)
        self.assertEqual(reopened.reviewed_by, 987)

    def test_rejection_requires_order_to_be_pending(self):
        created = self.create_order()
        rejected = self.store.review_order(
            guild_id=123,
            order_id=created.order_id,
            reviewer_id=987,
            decision=REJECTED,
            note="Could not verify the payment",
        )
        self.assertEqual(rejected.status, REJECTED)

        with self.assertRaises(OrderStateError):
            self.store.review_order(
                guild_id=123,
                order_id=created.order_id,
                reviewer_id=987,
                decision=PAID,
            )

    def test_order_from_another_guild_is_not_visible(self):
        created = self.create_order(guild_id=123)
        with self.assertRaises(OrderNotFoundError):
            self.store.get_order(guild_id=999, order_id=created.order_id)

        with self.assertRaises(OrderNotFoundError):
            self.store.review_order(
                guild_id=999,
                order_id=created.order_id,
                reviewer_id=987,
                decision=PAID,
            )

    def test_invalid_decisions_and_limits_are_rejected(self):
        created = self.create_order()
        with self.assertRaises(ValueError):
            self.store.review_order(
                guild_id=123,
                order_id=created.order_id,
                reviewer_id=987,
                decision="fulfilled",
            )
        with self.assertRaises(ValueError):
            self.store.list_pending_orders(guild_id=123, limit=0)

    def test_required_order_fields_are_validated(self):
        with self.assertRaises(ValueError):
            self.store.create_order(
                guild_id=123,
                customer_id=456,
                product_label="",
                price_label="50T",
                submitted_amount="50",
            )


if __name__ == "__main__":
    unittest.main()
