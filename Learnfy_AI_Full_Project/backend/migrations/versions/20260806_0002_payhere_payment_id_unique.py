"""Add PayHere payment-ID idempotency constraint without recreating payment tables."""
from alembic import op
from sqlalchemy import inspect, text

revision = "20260806_0002"
down_revision = "20260806_0001"
branch_labels = None
depends_on = None

CONSTRAINT = "uq_payments_provider_payment_id"

def upgrade() -> None:
    bind = op.get_bind()
    uniques = inspect(bind).get_unique_constraints("payments")
    indexes = inspect(bind).get_indexes("payments")
    covered = any(item.get("column_names") == ["provider_payment_id"] for item in uniques)
    covered = covered or any(item.get("unique") and item.get("column_names") == ["provider_payment_id"] for item in indexes)
    if not covered:
        duplicate = bind.execute(text(
            "SELECT provider_payment_id FROM payments "
            "WHERE provider_payment_id IS NOT NULL "
            "GROUP BY provider_payment_id HAVING COUNT(*) > 1 LIMIT 1"
        )).first()
        if duplicate:
            raise RuntimeError(
                "Cannot add PayHere payment-ID uniqueness: duplicate provider_payment_id values exist. "
                "Back up the database and review the duplicate transaction history; no data was changed."
            )
        op.create_unique_constraint(CONSTRAINT, "payments", ["provider_payment_id"])

def downgrade() -> None:
    raise RuntimeError("PayHere idempotency downgrade is intentionally disabled to protect transaction history")
