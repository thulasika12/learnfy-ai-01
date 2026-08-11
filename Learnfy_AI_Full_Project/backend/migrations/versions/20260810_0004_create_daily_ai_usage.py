"""Create the missing daily AI usage quota table without touching usage data."""
from alembic import op
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, inspect, text

revision = "20260810_0004"
down_revision = "20260810_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "daily_ai_usage" in inspect(bind).get_table_names():
        return
    op.create_table(
        "daily_ai_usage",
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        Column("feature", String(30), nullable=False),
        Column("usage_date", Date, nullable=False),
        Column("usage_count", Integer, nullable=False, server_default="0"),
        Column("updated_at", DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
        UniqueConstraint("user_id", "feature", "usage_date", name="uq_daily_ai_usage"),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "idx_daily_ai_usage_user_date", "daily_ai_usage", ["user_id", "usage_date"]
    )


def downgrade() -> None:
    raise RuntimeError("Daily AI usage downgrade is disabled to protect quota history")