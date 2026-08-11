"""Align subscriptions with PayHere and optional legacy Stripe metadata.

This migration is additive and data-preserving. It never recreates or clears
the subscriptions table.
"""
from alembic import op
from sqlalchemy import inspect, String, text

revision = "20260810_0003"
down_revision = "20260806_0002"
branch_labels = None
depends_on = None


def _columns(bind) -> dict[str, dict]:
    return {column["name"]: column for column in inspect(bind).get_columns("subscriptions")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "subscriptions" not in inspector.get_table_names():
        raise RuntimeError("subscriptions table is missing; refusing to create or replace it")

    if bind.dialect.name == "mysql":
        op.alter_column(
            "payments", "provider", existing_type=String(30),
            existing_nullable=False, server_default="payhere",
        )

    columns = _columns(bind)
    additions = {
        "stripe_customer_id": "VARCHAR(255) NULL",
        "stripe_subscription_id": "VARCHAR(255) NULL",
        "cancel_at_period_end": "BOOLEAN NOT NULL DEFAULT FALSE",
    }
    for name, definition in additions.items():
        if name not in columns:
            op.execute(text(f"ALTER TABLE subscriptions ADD COLUMN {name} {definition}"))

    columns = _columns(bind)
    if not columns["source_payment_id"].get("nullable", True):
        op.alter_column(
            "subscriptions", "source_payment_id",
            existing_type=columns["source_payment_id"]["type"], nullable=True,
        )

    inspector = inspect(bind)
    source_fk = next((fk for fk in inspector.get_foreign_keys("subscriptions")
                      if fk.get("constrained_columns") == ["source_payment_id"]), None)
    if source_fk is None:
        op.create_foreign_key(
            "fk_subscriptions_source_payment", "subscriptions", "payments",
            ["source_payment_id"], ["id"], ondelete="SET NULL",
        )
    elif (source_fk.get("options", {}).get("ondelete") or "").upper() != "SET NULL":
        op.drop_constraint(source_fk["name"], "subscriptions", type_="foreignkey")
        op.create_foreign_key(
            "fk_subscriptions_source_payment", "subscriptions", "payments",
            ["source_payment_id"], ["id"], ondelete="SET NULL",
        )

    inspector = inspect(bind)
    indexes = inspector.get_indexes("subscriptions")
    uniques = inspector.get_unique_constraints("subscriptions")
    if not any(item.get("column_names") == ["stripe_customer_id"] for item in indexes):
        op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])
    unique_subscription = any(item.get("column_names") == ["stripe_subscription_id"] for item in uniques)
    unique_subscription = unique_subscription or any(
        item.get("unique") and item.get("column_names") == ["stripe_subscription_id"] for item in indexes
    )
    if not unique_subscription:
        op.create_unique_constraint(
            "uq_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"]
        )


def downgrade() -> None:
    raise RuntimeError("Subscription schema downgrade is disabled to protect payment and entitlement history")