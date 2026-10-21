"""Durable SQLite storage for GuildCart's manual order-review workflow.

This module records order state only. It does not prove that a payment was made
and it does not provision a product or VPN subscription.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator
import uuid


PENDING_REVIEW = "pending_review"
PAID = "paid"
REJECTED = "rejected"
CANCELLED = "cancelled"


class OrderNotFoundError(LookupError):
    """Raised when an order does not exist in the specified guild."""


class OrderStateError(ValueError):
    """Raised when an order cannot transition from its current state."""


@dataclass(frozen=True)
class Order:
    order_id: str
    guild_id: int
    customer_id: int
    product_label: str
    price_label: str
    submitted_amount: str
    payment_reference: str
    status: str
    created_at: str
    ticket_channel_id: int | None
    reviewed_at: str | None
    reviewed_by: int | None
    review_note: str | None


class OrderStore:
    """Small synchronous SQLite repository, suitable for one bot instance."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if self.db_path.parent != Path("."):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    ticket_channel_id INTEGER,
                    product_label TEXT NOT NULL,
                    price_label TEXT NOT NULL,
                    submitted_amount TEXT NOT NULL,
                    payment_reference TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK (
                        status IN ('pending_review', 'paid', 'rejected', 'cancelled')
                    ),
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    reviewed_by INTEGER,
                    review_note TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_guild_status_created
                ON orders (guild_id, status, created_at)
                """
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Order:
        return Order(**dict(row))

    def create_order(
        self,
        *,
        guild_id: int,
        customer_id: int,
        product_label: str,
        price_label: str,
        submitted_amount: str,
        payment_reference: str = "",
        ticket_channel_id: int | None = None,
    ) -> Order:
        """Create an order awaiting manual review and return its durable record."""
        if guild_id <= 0 or customer_id <= 0:
            raise ValueError("guild_id and customer_id must be positive integers.")
        if not product_label.strip() or not price_label.strip():
            raise ValueError("product_label and price_label are required.")
        if not submitted_amount.strip():
            raise ValueError("submitted_amount is required.")

        created_at = datetime.now(timezone.utc).isoformat()
        # 64 bits of random suffix makes collisions exceptionally unlikely while
        # keeping the human-facing ID short enough for Discord slash commands.
        order_id = f"GC-{uuid.uuid4().hex[:16].upper()}"

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO orders (
                    order_id, guild_id, customer_id, ticket_channel_id,
                    product_label, price_label, submitted_amount,
                    payment_reference, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    guild_id,
                    customer_id,
                    ticket_channel_id,
                    product_label.strip(),
                    price_label.strip(),
                    submitted_amount.strip(),
                    payment_reference.strip()[:1000],
                    PENDING_REVIEW,
                    created_at,
                ),
            )
            row = connection.execute(
                "SELECT * FROM orders WHERE order_id = ?", (order_id,)
            ).fetchone()

        return self._from_row(row)

    def get_order(self, *, guild_id: int, order_id: str) -> Order:
        """Get an order only when it belongs to the requested Discord guild."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM orders WHERE guild_id = ? AND order_id = ?",
                (guild_id, order_id.strip().upper()),
            ).fetchone()
        if row is None:
            raise OrderNotFoundError("Order was not found in this server.")
        return self._from_row(row)

    def list_pending_orders(self, *, guild_id: int, limit: int = 10) -> list[Order]:
        """List orders awaiting review for one guild, oldest first."""
        if limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50.")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM orders
                WHERE guild_id = ? AND status = ?
                ORDER BY created_at ASC, order_id ASC
                LIMIT ?
                """,
                (guild_id, PENDING_REVIEW, limit),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def review_order(
        self,
        *,
        guild_id: int,
        order_id: str,
        reviewer_id: int,
        decision: str,
        note: str | None = None,
    ) -> Order:
        """Approve or reject a pending order, atomically and at most once."""
        if decision not in (PAID, REJECTED):
            raise ValueError("decision must be 'paid' or 'rejected'.")
        if reviewer_id <= 0:
            raise ValueError("reviewer_id must be a positive integer.")
        normalized_id = order_id.strip().upper()
        reviewed_at = datetime.now(timezone.utc).isoformat()

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status FROM orders WHERE guild_id = ? AND order_id = ?",
                (guild_id, normalized_id),
            ).fetchone()
            if row is None:
                raise OrderNotFoundError("Order was not found in this server.")
            if row["status"] != PENDING_REVIEW:
                raise OrderStateError(
                    f"Order is already {row['status']}; only pending orders can be reviewed."
                )

            cursor = connection.execute(
                """
                UPDATE orders
                SET status = ?, reviewed_at = ?, reviewed_by = ?, review_note = ?
                WHERE guild_id = ? AND order_id = ? AND status = ?
                """,
                (
                    decision,
                    reviewed_at,
                    reviewer_id,
                    (note or "").strip()[:500] or None,
                    guild_id,
                    normalized_id,
                    PENDING_REVIEW,
                ),
            )
            if cursor.rowcount != 1:
                raise OrderStateError("Order state changed during review; reload and retry.")

            updated = connection.execute(
                "SELECT * FROM orders WHERE guild_id = ? AND order_id = ?",
                (guild_id, normalized_id),
            ).fetchone()

        return self._from_row(updated)
