"""Add the onboarding completion marker without locking out existing users."""
from alembic import op
from sqlalchemy import Boolean, Column, inspect, text

revision = "20260811_0005"
down_revision = "20260810_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "onboarding_completed" not in columns:
        # Existing accounts are grandfathered; registration explicitly stores false.
        op.add_column("users", Column("onboarding_completed", Boolean(), nullable=False, server_default=text("1")))


def downgrade() -> None:
    raise RuntimeError("Onboarding downgrade is disabled to protect account access")
